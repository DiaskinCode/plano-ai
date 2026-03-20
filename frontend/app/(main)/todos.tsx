import { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  FlatList,
  SectionList,
  TouchableOpacity,
  StyleSheet,
  RefreshControl,
  Alert,
  TextInput,
  Modal,
  ScrollView,
  ActivityIndicator,
  SafeAreaView,
} from 'react-native';
import { BlurView } from 'expo-blur';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { todosAPI, insightsAPI, goalSpecAPI } from '@/services/api';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import CalendarScreen from './calendar';
import { useLocalSearchParams, useRouter } from 'expo-router';
import {
  scheduleNotificationForTask,
  cancelNotificationForTask,
  syncTaskNotifications
} from '@/utils/taskNotifications';
import analytics from '@/services/analytics';
import { colors, spacing, borderRadius } from '@/theme';
import { FadeInSlide } from '@/lib/animations';
import LiquidGlassCard from '@/components/LiquidGlassCard';

// Generate 14 days (7 before, today, 6 after)
const generateDays = () => {
  const days = [];
  const today = new Date();
  for (let i = -7; i <= 6; i++) {
    const date = new Date(today);
    date.setDate(today.getDate() + i);
    days.push(date);
  }
  return days;
};

// Helper to group todos by date
const groupTodosByDate = (todos: any[]) => {
  const grouped: { [key: string]: any[] } = {};

  todos.forEach(todo => {
    const date = todo.scheduled_date;
    if (!grouped[date]) {
      grouped[date] = [];
    }
    grouped[date].push(todo);
  });

  // Convert to array and sort by date
  return Object.keys(grouped)
    .sort((a, b) => new Date(a).getTime() - new Date(b).getTime())
    .map(date => ({
      title: date,
      data: grouped[date],
    }));
};

// Group tasks by university, then by type (blockers first)
const groupTodosByUniversity = (todos: any[]) => {
  const groups: { [key: string]: any } = {};

  todos.forEach(todo => {
    // Skip undefined todos
    if (!todo) return;

    // ✅ Check scope for proper grouping
    // Global tasks (scope='global' or no university) go in General section
    const isGlobal = !todo.university || todo.scope === 'global';
    const uniId = isGlobal ? 'general' : todo.university.id;

    if (!groups[uniId]) {
      if (isGlobal) {
        groups[uniId] = {
          university: null,
          universityId: 'general',
          universityName: 'General Tasks',
          blockers: [],
          applicationTasks: [],
          foundationTasks: [],
        };
      } else {
        groups[uniId] = {
          university: todo.university,
          universityId: uniId,
          universityName: todo.university_name || todo.university?.name || 'University',
          blockers: [],
          applicationTasks: [],
          foundationTasks: [],
        };
      }
    }

    // Categorize by type
    if (todo.is_blocker) {
      groups[uniId].blockers.push(todo);
    } else if (todo.requirement_type === 'foundation') {
      groups[uniId].foundationTasks.push(todo);
    } else {
      groups[uniId].applicationTasks.push(todo);
    }
  });

  // Convert to array and sort:
  // 1. Universities with blockers first
  // 2. Nearest deadline next
  // 3. Alphabetical by name last
  return Object.values(groups).sort((a, b) => {
    // Priority 1: Has blockers
    if (a.blockers.length > 0 && b.blockers.length === 0) return -1;
    if (b.blockers.length > 0 && a.blockers.length === 0) return 1;

    // Priority 2: Nearest deadline
    const aDeadline = a.university?.deadline ? new Date(a.university.deadline).getTime() : Infinity;
    const bDeadline = b.university?.deadline ? new Date(b.university.deadline).getTime() : Infinity;
    if (aDeadline !== bDeadline) return aDeadline - bDeadline;

    // Priority 3: Alphabetical (but General Tasks always last)
    if (a.universityId === 'general') return 1;
    if (b.universityId === 'general') return -1;

    return a.universityName.localeCompare(b.universityName);
  });
};

// Group tasks by stage (strategy, shortlist, docs, essays, apply, visa, arrival)
const groupTodosByStage = (todos: any[]) => {
  const stages = [
    'strategy',
    'shortlist',
    'docs',
    'essays',
    'apply',
    'visa',
    'arrival',
  ];

  const stageLabels: { [key: string]: string } = {
    strategy: '🎯 Strategy',
    shortlist: '📋 Shortlist',
    docs: '📄 Documents',
    essays: '✍️ Essays',
    apply: '🚀 Apply',
    visa: '✈️ Visa',
    arrival: '🎓 Post-Admission',
  };

  const groups: { [key: string]: any } = {};

  // Initialize all stages
  stages.forEach(stage => {
    groups[stage] = {
      stage,
      label: stageLabels[stage] || stage,
      blockers: [],
      regularTasks: [],
    };
  });

  // Group todos by stage
  todos.forEach(todo => {
    if (!todo) return;

    const stage = todo.stage || 'docs'; // Default to docs if no stage

    if (!groups[stage]) {
      // Create unknown stage if not in our list
      groups[stage] = {
        stage,
        label: stage,
        blockers: [],
        regularTasks: [],
      };
    }

    if (todo.is_blocker) {
      groups[stage].blockers.push(todo);
    } else {
      groups[stage].regularTasks.push(todo);
    }
  });

  // Convert to array and filter out empty stages
  return stages
    .filter(stage => groups[stage] && (groups[stage].blockers.length > 0 || groups[stage].regularTasks.length > 0))
    .map(stage => groups[stage]);
};

// Category color mapping
const getCategoryColor = (category: string): string => {
  switch (category?.toLowerCase()) {
    case 'study': return '#FF3B30';
    case 'language': return '#3B82F6';
    case 'sport': return '#34C759';
    case 'career': return '#06B6D4';
    case 'finance': return '#FFD60A';
    case 'health': return '#FF69B4';
    case 'creative': return '#A855F7';
    default: return '#5B6AFF';
  }
};

// College admissions task category color mapping
const getCollegeCategoryColor = (category: string): string => {
  switch (category) {
    case 'Documents': return '#3B82F6';  // Blue
    case 'Essays': return '#10B981';     // Green
    case 'Portfolio': return '#8B5CF6';  // Purple
    case 'SAT Prep': return '#F59E0B';    // Orange
    case 'IELTS Prep': return '#F97316';  // Red-Orange
    case 'Applications': return '#EF4444'; // Red
    case 'Extracurriculars': return '#6B7280'; // Gray
    default: return '#5B6AFF';
  }
};

// Get college category icon
const getCollegeCategoryIcon = (category: string): string => {
  switch (category) {
    case 'Documents': return '📄';
    case 'Essays': return '📝';
    case 'Portfolio': return '💼';
    case 'SAT Prep': return '📊';
    case 'IELTS Prep': return '🗣';
    case 'Applications': return '🎓';
    case 'Extracurriculars': return '🎯';
    default: return '📌';
  }
};

export default function TodosScreen() {
  const router = useRouter();
  const params = useLocalSearchParams();
  const goalspecId = params.goalspecId ? Number(params.goalspecId) : null;

  const [viewMode, setViewMode] = useState<'university' | 'date' | 'stage'>('university');
  const [todos, setTodos] = useState<any[]>([]);
  const [sections, setSections] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [statusFilter, setStatusFilter] = useState('all'); // all, pending, done
  const [goalspecs, setGoalspecs] = useState<any[]>([]);
  const [goalspecMap, setGoalspecMap] = useState<{ [key: number]: any }>({});
  const [showAddModal, setShowAddModal] = useState(false);
  const [showCalendarModal, setShowCalendarModal] = useState(false);
  const [newTodoText, setNewTodoText] = useState('');
  const [generating, setGenerating] = useState(false);
  const [generationStage, setGenerationStage] = useState<string>('');
  const [days] = useState(generateDays());
  const [calendarMonth, setCalendarMonth] = useState(new Date());
  const dayScrollRef = useRef<ScrollView>(null);
  const [isGuest, setIsGuest] = useState(false);

  // ✅ Coverage from API (not calculated locally)
  const [coverage, setCoverage] = useState<{
    verifiedCoverage: number;
    assumedCoverage: number;
    planStatus: 'verified' | 'draft' | 'not_generated';
    missingCount: number;
  }>({
    verifiedCoverage: 0,
    assumedCoverage: 0,
    planStatus: 'not_generated',
    missingCount: 0
  });

  // Feedback Modal State
  const [showFeedbackModal, setShowFeedbackModal] = useState(false);
  const [feedbackTask, setFeedbackTask] = useState<any>(null);
  const [feedbackType, setFeedbackType] = useState<'completed' | 'skipped'>('completed');
  const [difficultyRating, setDifficultyRating] = useState(3);
  const [actualDuration, setActualDuration] = useState('');
  const [energyAtCompletion, setEnergyAtCompletion] = useState<'high' | 'medium' | 'low'>('medium');
  const [feedbackNotes, setFeedbackNotes] = useState('');
  const [skipReason, setSkipReason] = useState<'skipped_no_time' | 'skipped_no_motivation' | 'skipped_distracted' | 'skipped_too_hard' | 'skipped_other'>('skipped_no_time');
  const [submittingFeedback, setSubmittingFeedback] = useState(false);

  useEffect(() => {
    const checkGuestMode = async () => {
      const guestMode = await AsyncStorage.getItem('isGuest');
      setIsGuest(guestMode === 'true');
    };
    checkGuestMode();
    loadGoalspecs();
  }, []);

  useEffect(() => {
    if (!isGuest) {
      loadTodos();
    }
  }, [selectedDate, statusFilter, viewMode, goalspecId, isGuest]);

  // ✅ Fetch coverage from eligibility endpoint
  useEffect(() => {
    const fetchCoverage = async () => {
      if (isGuest) return;

      try {
        const token = await AsyncStorage.getItem('token');
        if (!token) return;

        const API_URL = process.env.EXPO_PUBLIC_API_URL || 'https://pathai-backend.com';

        const response = await fetch(`${API_URL}/api/todos/eligibility/check/`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });

        if (response.ok) {
          const data = await response.json();
          setCoverage({
            verifiedCoverage: data.coverage.verified_percent,
            assumedCoverage: data.coverage.assumed_percent,
            planStatus: data.coverage.plan_status,
            missingCount: data.coverage.missing_count
          });
        }
      } catch (error) {
        console.error('Failed to fetch coverage:', error);
      }
    };

    fetchCoverage();
  }, [isGuest]);

  // Auto-scroll to today's date
  useEffect(() => {
    setTimeout(() => {
      const todayIndex = days.findIndex(day => isToday(day));
      if (todayIndex !== -1 && dayScrollRef.current) {
        dayScrollRef.current.scrollTo({ x: todayIndex * 52, animated: true });
      }
    }, 100);
  }, []);

  const handleGenerateTasks = async () => {
    Alert.alert(
      'Check Eligibility First',
      'Let\'s verify which universities you\'re eligible for before generating tasks. This ensures we create the right plan for you.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Check Now',
          onPress: () => router.push('/task/eligibility-gate')
        }
      ]
    );
  };

  const loadGoalspecs = async () => {
    try {
      const response = await goalSpecAPI.list();
      const specs = response.data;

      // Ensure specs is an array before processing
      if (Array.isArray(specs)) {
        setGoalspecs(specs);

        // Create a map for quick lookup
        const map: { [key: number]: any } = {};
        specs.forEach((spec: any) => {
          map[spec.id] = spec;
        });
        setGoalspecMap(map);
      } else {
        console.warn('Goalspecs response is not an array:', specs);
        setGoalspecs([]);
        setGoalspecMap({});
      }
    } catch (error) {
      console.error('Failed to load goalspecs:', error);
      setGoalspecs([]);
      setGoalspecMap({});
    }
  };

  const loadTodos = async () => {
    try {
      setLoading(true);
      const status = statusFilter === 'all' ? undefined : statusFilter;

      // Fetch all todos (for list view, we want all upcoming/past dates)
      const response = await todosAPI.list(undefined, status);
      let allTodos = response.data.results || response.data;

      // Filter by goalspecId if provided
      if (goalspecId) {
        allTodos = allTodos.filter((todo: any) => todo.goalspec === goalspecId);
      }

      setTodos(allTodos);

      // Group by date for SectionList
      const grouped = groupTodosByDate(allTodos);
      setSections(grouped);

      // Sync local notifications with server state
      syncTaskNotifications(() => Promise.resolve({ data: { results: allTodos } }));
    } catch (error) {
      console.error('Failed to load todos:', error);
    } finally {
      setLoading(false);
    }
  };

  const isToday = (date: Date) => {
    const today = new Date();
    return date.toDateString() === today.toDateString();
  };

  const isSameDay = (date1: Date, date2: Date) => {
    return date1.toDateString() === date2.toDateString();
  };

  const getDaysInMonth = (date: Date) => {
    const year = date.getFullYear();
    const month = date.getMonth();
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const days = [];

    for (let i = 1; i <= daysInMonth; i++) {
      days.push(new Date(year, month, i));
    }
    return days;
  };

  const handleMarkDone = async (task: any) => {
    try {
      // Mark task as done using the markDone endpoint
      await todosAPI.markDone(task.id);

      // Track task completion
      const goalspec = task.goalspec ? goalspecMap[task.goalspec] : null;
      analytics.trackTaskCompleted(task.id, {
        title: task.title,
        goalspec_id: task.goalspec,
        category: goalspec?.category || goalspec?.goal_type,
      });

      // Refresh the list
      loadTodos();
      // Show brief success feedback
      setFeedbackTask(task);
      setFeedbackType('completed');
      setShowFeedbackModal(true);
      // Auto-close after 1.5 seconds
      setTimeout(() => {
        setShowFeedbackModal(false);
        setFeedbackTask(null);
      }, 1500);
    } catch (error) {
      console.error('Failed to mark task as done:', error);
    }
  };

  const handleSkip = async (task: any) => {
    try {
      // Skip task using the skip endpoint
      await todosAPI.skip(task.id);

      // Track task skip
      analytics.trackTaskSkipped(task.id);

      // Refresh the list
      loadTodos();
      // Show brief feedback
      setFeedbackTask(task);
      setFeedbackType('skipped');
      setShowFeedbackModal(true);
      // Auto-close after 1.5 seconds
      setTimeout(() => {
        setShowFeedbackModal(false);
        setFeedbackTask(null);
      }, 1500);
    } catch (error) {
      console.error('Failed to skip task:', error);
    }
  };

  const submitFeedback = async () => {
    if (!feedbackTask) return;

    try {
      setSubmittingFeedback(true);

      if (feedbackType === 'completed') {
        // Complete with feedback
        await insightsAPI.completeWithFeedback(feedbackTask.id, {
          completion_reason: 'completed',
          difficulty_rating: difficultyRating,
          actual_duration_minutes: actualDuration ? parseInt(actualDuration) : undefined,
          notes: feedbackNotes || undefined,
          energy_level_at_completion: energyAtCompletion,
        });

        // Cancel local notification for completed task
        await cancelNotificationForTask(feedbackTask.id);

        Alert.alert('Success', 'Task completed! 🎉');
      } else {
        // Skip with feedback
        await insightsAPI.completeWithFeedback(feedbackTask.id, {
          completion_reason: skipReason,
          notes: feedbackNotes || undefined,
        });

        // Cancel local notification for skipped task
        await cancelNotificationForTask(feedbackTask.id);

        Alert.alert('Success', 'Task skipped');
      }

      setShowFeedbackModal(false);
      setFeedbackTask(null);
      loadTodos();
    } catch (error: any) {
      console.error('Failed to submit feedback:', error);
      Alert.alert('Error', error?.response?.data?.error || 'Failed to submit feedback');
    } finally {
      setSubmittingFeedback(false);
    }
  };

  const handleAddTodo = async () => {
    if (!newTodoText.trim()) return;

    try {
      const response = await todosAPI.createTodo({
        task: newTodoText,
        scheduled_for: new Date().toISOString().split('T')[0],
      });

      // Track task creation
      if (response.data) {
        analytics.trackTaskCreated(response.data.id, {
          title: response.data.title || newTodoText,
          scheduled_date: new Date().toISOString().split('T')[0],
        });

        // Schedule local notification for the created task
        await scheduleNotificationForTask(response.data);
      }

      setNewTodoText('');
      setShowAddModal(false);
      loadTodos();
    } catch (error) {
      Alert.alert('Error', 'Failed to create todo');
    }
  };

  const renderTodo = ({ item }: any) => {
    if (!item) return null;

    const isPast = new Date(item.scheduled_date) < new Date(new Date().setHours(0, 0, 0, 0));
    const isDone = item.status === 'done';
    const isSkipped = item.status === 'skipped';
    const endTime = item.scheduled_time && item.estimated_duration_minutes
      ? calculateEndTime(item.scheduled_time, item.estimated_duration_minutes)
      : null;

    // Get goalspec data
    const goalspec = item.goalspec ? goalspecMap[item.goalspec] : null;
    const categoryColor = goalspec ? getCategoryColor(goalspec.category || goalspec.goal_type) : '#5B6AFF';

    // Get energy icon and color
    const getEnergyBadge = (level: string) => {
      switch (level) {
        case 'high': return { icon: 'flash', color: '#FF3B30', label: 'High' };
        case 'medium': return { icon: 'battery-medium', color: '#FF9500', label: 'Med' };
        case 'low': return { icon: 'weather-night', color: '#34C759', label: 'Low' };
        default: return { icon: 'help-circle-outline', color: '#8E8E8E', label: '?' };
      }
    };

    const energyBadge = getEnergyBadge(item.energy_level || 'medium');

    // Calculate progress for global tasks with university_checklist
    const getProgress = () => {
      if (item.university_checklist && Object.keys(item.university_checklist).length > 0) {
        const checklist = item.university_checklist;
        const total = Object.keys(checklist).length;
        const completed = Object.values(checklist).filter((v: any) => v.status === 'done').length;
        return { completed, total, show: true };
      }
      return { completed: 0, total: 0, show: false };
    };

    const progress = getProgress();

    return (

      <View style={{ marginBottom: spacing.sm }}>
        <LiquidGlassCard
          onPress={() => router.push(`/task/${item.id}`)}
          variant={isDone ? 'subtle' : 'default'}
          intensity={isDone ? 'light' : 'medium'}
          style={[
            styles.todoCard,
            isPast && !isDone && styles.compactCardPast,
            isSkipped && styles.compactCardSkipped
          ]}
        >
          <View style={styles.compactCardContent}>
            {/* Left border with scope color */}
            <View style={[styles.leftBorder, {
              backgroundColor: isDone ? '#34C759' : isSkipped ? '#FF9500' :
                item.scope === 'global' ? '#5B6AFF' :
                item.scope === 'country' ? '#FF9500' :
                item.scope === 'university' ? '#34C759' :
                goalspec ? categoryColor : getPriorityColor(item.priority)
            }]} />

            <View style={styles.compactCardMain}>
              {/* Title */}
              <Text style={[
                styles.compactCardTitle,
                isPast && !isDone && styles.taskTitlePast,
                isDone && styles.taskTitleDone,
                isSkipped && styles.taskTitleSkipped
              ]} numberOfLines={2}>
                {item.title}
              </Text>

              {/* Why/Reason line - NEW */}
              {item.reason && (
                <Text style={styles.compactCardWhy} numberOfLines={1}>
                  {item.reason}
                </Text>
              )}

              {/* Chips row */}
              <View style={styles.compactCardChips}>
                {/* Due date chip */}
                {item.scheduled_date && (
                  <View style={styles.compactChip}>
                    <MaterialCommunityIcons name="calendar" size={12} color={colors.textSecondary} />
                    <Text style={styles.compactChipText}>
                      {new Date(item.scheduled_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                    </Text>
                  </View>
                )}

                {/* Blocker chip */}
                {item.is_blocker && (
                  <View style={[styles.compactChip, styles.blockerChip]}>
                    <MaterialCommunityIcons name="alert-circle" size={12} color={colors.error} />
                    <Text style={[styles.compactChipText, { color: colors.error }]}>Blocker</Text>
                  </View>
                )}

                {/* Evidence status chip - NEW */}
                {item.evidence_status && item.evidence_status !== 'missing' && (
                  <View style={[
                    styles.compactChip,
                    item.evidence_status === 'complete' ? styles.evidenceCompleteChip : styles.evidencePartialChip
                  ]}>
                    <MaterialCommunityIcons
                      name={item.evidence_status === 'complete' ? 'check-circle' : 'progress-upload'}
                      size={12}
                      color={item.evidence_status === 'complete' ? '#34C759' : '#FF9500'}
                    />
                    <Text style={[
                      styles.compactChipText,
                      { color: item.evidence_status === 'complete' ? '#34C759' : '#FF9500' }
                    ]}>
                      {item.evidence_status === 'complete' ? 'Evidence' : 'Partial'}
                    </Text>
                  </View>
                )}

                {/* Link icon - NEW */}
                {item.link_url && (
                  <MaterialCommunityIcons name="open" size={14} color={colors.primary} />
                )}

                {/* Scope badge - NEW */}
                {item.scope && item.scope !== 'university' && (
                  <View style={[styles.compactChip, styles.scopeChip]}>
                    <Text style={styles.scopeChipText}>
                      {item.scope === 'global' ? 'All' :
                       item.scope === 'country' ? item.country : item.scope}
                    </Text>
                  </View>
                )}
              </View>

              {/* Progress for global tasks - NEW */}
              {progress.show && (
                <View style={styles.compactCardProgress}>
                  <MaterialCommunityIcons name="check-circle" size={14} color={colors.success} />
                  <Text style={styles.compactProgressText}>
                    Submitted: {progress.completed}/{progress.total}
                  </Text>
                </View>
              )}
            </View>

            {/* Right side - Done/Skipped indicator */}
            {isDone && (
              <View style={styles.doneIndicator}>
                <MaterialCommunityIcons name="check-circle" size={20} color="#34C759" />
              </View>
            )}
            {isSkipped && (
              <View style={styles.doneIndicator}>
                <MaterialCommunityIcons name="close-circle" size={20} color="#FF9500" />
              </View>
            )}
          </View>
        </LiquidGlassCard>
      </View>
    );
  };

  const renderStageSection = ({ item }: any) => {
    const group = item;
    if (!group) return null;

    const blockers = group.blockers || [];
    const regularTasks = group.regularTasks || [];

    // Safe key extractor
    const safeKeyExtractor = (taskItem: any, index: number) => {
      if (taskItem?.id) return `task-${taskItem.id}`;
      if (taskItem?.dedupe_key) return `dedupe-${taskItem.dedupe_key}`;
      return `task-${group.stage}-${index}`;
    };

    return (
      <View style={styles.stageSection}>
        {/* Stage Header */}
        <View style={styles.stageHeader}>
          <Text style={styles.stageTitle}>{group.label}</Text>
          {blockers.length > 0 && (
            <View style={styles.blockerCountBadge}>
              <MaterialCommunityIcons name="alert" size={14} color={colors.error} />
              <Text style={styles.blockerCountText}>{blockers.length}</Text>
            </View>
          )}
        </View>

        {/* Blockers */}
        {blockers.length > 0 && (
          <View style={styles.blockersSection}>
            <Text style={styles.blockersTitle}>⚠️ Must Complete First</Text>
            <FlatList
              data={blockers.filter(Boolean)}
              renderItem={renderTodo}
              keyExtractor={safeKeyExtractor}
              scrollEnabled={false}
            />
          </View>
        )}

        {/* Regular Tasks */}
        {regularTasks.length > 0 && (
          <View style={styles.regularTasksSection}>
            <FlatList
              data={regularTasks.filter(Boolean)}
              renderItem={renderTodo}
              keyExtractor={safeKeyExtractor}
              scrollEnabled={false}
            />
          </View>
        )}
      </View>
    );
  };

  const renderUniversitySection = ({ item }: any) => {
    const group = item;
    if (!group) return null;

    const blockers = group.blockers || [];
    const applicationTasks = group.applicationTasks || [];
    const foundationTasks = group.foundationTasks || [];

    // Safe key extractor that returns a string
    const safeKeyExtractor = (taskItem: any, index: number) => {
      if (taskItem?.id) return `task-${taskItem.id}`;
      if (taskItem?.dedupe_key) return `dedupe-${taskItem.dedupe_key}`;
      return `task-${group.universityId}-${index}`;
    };

    return (
      <View style={styles.universitySection}>
        {/* University Header */}
        <View style={styles.universityHeader}>
          <Text style={styles.universityName}>{group.universityName || 'General Tasks'}</Text>
          {group.university?.deadline && (
            <Text style={styles.universityDeadline}>
              Deadline: {new Date(group.university.deadline).toLocaleDateString()}
            </Text>
          )}
        </View>

        {/* Blockers (show first) */}
        {blockers.length > 0 && (
          <View style={styles.blockersSection}>
            <Text style={styles.blockersTitle}>⚠️ Must Complete First</Text>
            <FlatList
              data={blockers.filter(Boolean)}
              renderItem={renderTodo}
              keyExtractor={safeKeyExtractor}
              scrollEnabled={false}
            />
          </View>
        )}

        {/* Application Tasks (only if no blockers) */}
        {applicationTasks.length > 0 && (
          <View style={styles.appTasksSection}>
            <Text style={styles.appTasksTitle}>📋 Application Steps</Text>
            <FlatList
              data={applicationTasks.filter(Boolean)}
              renderItem={renderTodo}
              keyExtractor={safeKeyExtractor}
              scrollEnabled={false}
            />
          </View>
        )}

        {/* Foundation Tasks (if applicable) */}
        {foundationTasks.length > 0 && (
          <View style={styles.foundationSection}>
            <Text style={styles.foundationTitle}>🎓 Foundation Track</Text>
            <FlatList
              data={foundationTasks.filter(Boolean)}
              renderItem={renderTodo}
              keyExtractor={safeKeyExtractor}
              scrollEnabled={false}
            />
          </View>
        )}
      </View>
    );
  };

  const calculateEndTime = (startTime: string, durationMinutes: number): string => {
    const [hours, minutes] = startTime.split(':').map(Number);
    const totalMinutes = hours * 60 + minutes + durationMinutes;
    const endHours = Math.floor(totalMinutes / 60) % 24;
    const endMinutes = totalMinutes % 60;
    return `${endHours.toString().padStart(2, '0')}:${endMinutes.toString().padStart(2, '0')}`;
  };

  const formatSectionHeader = (dateString: string): string => {
    const date = new Date(dateString);
    const today = new Date();
    const isPast = date < new Date(today.setHours(0, 0, 0, 0));

    const dayNames = ['Воскресенье', 'Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота'];
    const monthNames = ['янв.', 'февр.', 'март', 'апр.', 'май', 'июнь', 'июль', 'авг.', 'сент.', 'окт.', 'нояб.', 'дек.'];

    const dayName = dayNames[date.getDay()];
    const day = date.getDate();
    const month = monthNames[date.getMonth()];

    return `${dayName} — ${day} ${month}.`;
  };

  const renderSectionHeader = ({ section }: any) => {
    const isPast = new Date(section.title) < new Date(new Date().setHours(0, 0, 0, 0));
    const isToday = new Date(section.title).toDateString() === new Date().toDateString();

    return (
      <Text style={[
        styles.sectionHeader,
        isPast && styles.sectionHeaderPast,
        isToday && styles.sectionHeaderToday
      ]}>
        {formatSectionHeader(section.title)}
      </Text>
    );
  };

  // Guest mode UI
  if (isGuest) {
    return (
      <View style={styles.container}>
        <View style={styles.header}>
          <Text style={styles.headerTitle}>Tasks</Text>
        </View>

        <View style={styles.guestPromptContainer}>
          <MaterialCommunityIcons name="lock-outline" size={64} color="#5B6AFF" />
          <Text style={styles.guestPromptTitle}>Sign in to Create Tasks</Text>
          <Text style={styles.guestPromptText}>
            Create an account to build your personalized task list and track your progress
          </Text>

          <TouchableOpacity
            style={styles.signInButton}
            onPress={async () => {
              await AsyncStorage.removeItem('isGuest');
              router.replace('/(auth)/login');
            }}
          >
            <Text style={styles.signInButtonText}>Sign In</Text>
            <MaterialCommunityIcons name="arrow-right" size={20} color="#fff" />
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.createAccountButton}
            onPress={async () => {
              await AsyncStorage.removeItem('isGuest');
              router.replace('/(auth)/register');
            }}
          >
            <Text style={styles.createAccountButtonText}>Create Account</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  // ✅ Coverage fetched from API via useEffect, not calculated locally

  // Plan Status Card Component
  const PlanStatusCard = () => (
    <View style={styles.coverageContainer}>
      <View style={styles.coverageHeader}>
        <Text style={styles.coverageTitle}>Plan Status</Text>
        <View style={[
          styles.coverageBadge,
          coverage.planStatus === 'verified' ? styles.verifiedBadge : styles.draftBadge
        ]}>
          <MaterialCommunityIcons
            name={coverage.planStatus === 'verified' ? 'check-circle' : 'pencil'}
            size={14}
            color={coverage.planStatus === 'verified' ? '#34C759' : '#FF9500'}
          />
          <Text style={[
            styles.coverageBadgeText,
            coverage.planStatus === 'verified' ? styles.verifiedText : styles.draftText
          ]}>
            {coverage.planStatus === 'verified' ? 'Verified' : 'Draft'}
          </Text>
        </View>
      </View>

      <View style={styles.coverageMetrics}>
        <View style={styles.metric}>
          <Text style={styles.metricLabel}>Verified</Text>
          <Text style={[
            styles.metricValue,
            coverage.verifiedCoverage >= 95 ? styles.metricExcellent : styles.metricGood
          ]}>
            {coverage.verifiedCoverage}%
          </Text>
        </View>
        <View style={styles.metricDivider} />
        <View style={styles.metric}>
          <Text style={styles.metricLabel}>With assumptions</Text>
          <Text style={styles.metricValue}>{coverage.assumedCoverage}%</Text>
        </View>
      </View>

      {coverage.planStatus === 'draft' && coverage.missingCount > 0 && (
        <TouchableOpacity
          style={styles.verifyButton}
          onPress={() => router.push('/requirements/verify')}
        >
          <MaterialCommunityIcons name="shield-check" size={16} color="#5B6AFF" />
          <Text style={styles.verifyButtonText}>
            Verify {coverage.missingCount} requirements to finalize plan
          </Text>
        </TouchableOpacity>
      )}
    </View>
  );

  return (
    <SafeAreaView style={styles.container}>
      {/* Status Strip - Show blockers and next deadline */}
      <View style={styles.statusStrip}>
        <View style={styles.statusItem}>
          <MaterialCommunityIcons
            name="alert-circle"
            size={16}
            color={(todos || []).filter(t => t?.is_blocker).length > 0 ? colors.error : colors.textSecondary}
          />
          <Text style={styles.statusLabel}>
            Blockers:{' '}
            <Text style={styles.statusValue}>
              {String((todos || []).filter(t => t?.is_blocker).length)}
            </Text>
          </Text>
        </View>
        <View style={styles.statusItem}>
          <MaterialCommunityIcons name="calendar" size={16} color={colors.textSecondary} />
          <Text style={styles.statusLabel}>
            Next:{' '}
            <Text style={styles.statusValue}>
              {(todos || []).filter(t => t?.scheduled_date).length > 0
                ? new Date(Math.min(...(todos || []).filter(t => t?.scheduled_date).map(t => new Date(t.scheduled_date).getTime()))).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
                : 'Set deadline'}
            </Text>
          </Text>
        </View>
      </View>

      <View style={styles.header}>
        <Text style={styles.headerTitle}>My Tasks</Text>
        <TouchableOpacity
          style={[styles.addButton, (todos || []).length === 0 && styles.generatePlanButtonSmall]}
          onPress={(todos || []).length === 0 ? handleGenerateTasks : () => setShowAddModal(true)}
          disabled={generating}
        >
          {(todos || []).length === 0 && generating ? (
            <ActivityIndicator size="small" color="#fff" />
          ) : (todos || []).length === 0 ? (
            <>
              <MaterialCommunityIcons name="rocket-launch" size={16} color="#fff" />
              <Text style={styles.addButtonText}>Generate Plan</Text>
            </>
          ) : (
            <Text style={styles.addButtonText}>+ Add</Text>
          )}
        </TouchableOpacity>
      </View>

      {/* View Switcher - By University | By Date */}
      <View style={styles.viewSwitcher}>
        {/* Row 1: View mode tabs */}
        <View style={styles.viewModeToggleRow}>
          <TouchableOpacity
            style={[styles.viewTab, viewMode === 'university' && styles.viewTabActive]}
            onPress={() => setViewMode('university')}
          >
            <Text
              style={[styles.viewTabText, viewMode === 'university' && styles.viewTabTextActive]}
              numberOfLines={1}
              ellipsizeMode="tail"
            >
              By University
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.viewTab, viewMode === 'date' && styles.viewTabActive]}
            onPress={() => setViewMode('date')}
          >
            <Text
              style={[styles.viewTabText, viewMode === 'date' && styles.viewTabTextActive]}
              numberOfLines={1}
              ellipsizeMode="tail"
            >
              By Date
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.viewTab, viewMode === 'stage' && styles.viewTabActive]}
            onPress={() => setViewMode('stage')}
          >
            <Text
              style={[styles.viewTabText, viewMode === 'stage' && styles.viewTabTextActive]}
              numberOfLines={1}
              ellipsizeMode="tail"
            >
              By Stage
            </Text>
          </TouchableOpacity>
        </View>

        {/* Row 2: Status filter */}
        <View style={styles.statusFilterRow}>
          {['all', 'pending', 'done'].map((s) => (
            <TouchableOpacity
              key={s}
              style={[styles.filterButton, statusFilter === s && styles.filterButtonActive]}
              onPress={() => setStatusFilter(s)}
            >
              <Text
                style={styles.filterButtonText}
                numberOfLines={1}
                ellipsizeMode="tail"
              >
                {s.charAt(0).toUpperCase() + s.slice(1)}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      {viewMode === 'university' ? (
        <FlatList
          data={groupTodosByUniversity(todos || [])}
          renderItem={renderUniversitySection}
          keyExtractor={(item) => item?.universityId || 'general'}
          contentContainerStyle={(todos || []).length === 0 ? styles.emptyListContent : styles.listContent}
          refreshControl={
            <RefreshControl refreshing={loading} onRefresh={loadTodos} />
          }
          ListHeaderComponent={
            (todos || []).length > 0 ? PlanStatusCard : null
          }
          ListEmptyComponent={
            <View style={styles.emptyContainer}>
              <View style={styles.emptyIconContainer}>
                <MaterialCommunityIcons name="school" size={64} color="#5B6AFF" />
              </View>
              <Text style={styles.emptyText}>No Admissions Plan Yet</Text>
              <Text style={styles.emptyDescription}>
                Get a personalized roadmap with application deadlines, essay milestones, and test schedules tailored to your target universities.
              </Text>

              <TouchableOpacity
                style={styles.primaryActionButton}
                onPress={handleGenerateTasks}
                disabled={generating}
              >
                {generating ? (
                  <>
                    <ActivityIndicator size="small" color="#fff" />
                    <Text style={styles.primaryActionButtonText}>
                      {generationStage || 'Checking...'}
                    </Text>
                  </>
                ) : (
                  <>
                    <MaterialCommunityIcons name="rocket-launch" size={20} color="#fff" />
                    <Text style={styles.primaryActionButtonText}>
                      Check Eligibility & Generate Tasks
                    </Text>
                  </>
                )}
              </TouchableOpacity>

              <TouchableOpacity
                style={styles.secondaryActionButton}
                onPress={() => setShowAddModal(true)}
              >
                <Text style={styles.secondaryActionButtonText}>
                  Or add a manual task
                </Text>
              </TouchableOpacity>
            </View>
          }
        />
      ) : viewMode === 'date' ? (
        <SectionList
          sections={sections}
          renderItem={renderTodo}
          renderSectionHeader={renderSectionHeader}
          keyExtractor={(item) => item.id.toString()}
          contentContainerStyle={styles.listContent}
          refreshControl={
            <RefreshControl refreshing={loading} onRefresh={loadTodos} />
          }
          stickySectionHeadersEnabled={false}
          ListEmptyComponent={
            <View style={styles.emptyContainer}>
              <View style={styles.emptyIconContainer}>
                <MaterialCommunityIcons name="school" size={64} color="#5B6AFF" />
              </View>
              <Text style={styles.emptyText}>No Admissions Plan Yet</Text>
              <Text style={styles.emptyDescription}>
                Get a personalized roadmap with application deadlines, essay milestones, and test schedules tailored to your target universities.
              </Text>

              <TouchableOpacity
                style={styles.primaryActionButton}
                onPress={handleGenerateTasks}
                disabled={generating}
              >
                {generating ? (
                  <>
                    <ActivityIndicator size="small" color="#fff" />
                    <Text style={styles.primaryActionButtonText}>
                      {generationStage || 'Checking...'}
                    </Text>
                  </>
                ) : (
                  <>
                    <MaterialCommunityIcons name="rocket-launch" size={20} color="#fff" />
                    <Text style={styles.primaryActionButtonText}>
                      Check Eligibility & Generate Tasks
                    </Text>
                  </>
                )}
              </TouchableOpacity>

              <TouchableOpacity
                style={styles.secondaryActionButton}
                onPress={() => setShowAddModal(true)}
              >
                <Text style={styles.secondaryActionButtonText}>
                  Or add a manual task
                </Text>
              </TouchableOpacity>
            </View>
          }
        />
      ) : (
        <FlatList
          data={groupTodosByStage(todos || [])}
          renderItem={renderStageSection}
          keyExtractor={(item) => item?.stage || 'unknown'}
          contentContainerStyle={(todos || []).length === 0 ? styles.emptyListContent : styles.listContent}
          refreshControl={
            <RefreshControl refreshing={loading} onRefresh={loadTodos} />
          }
          ListEmptyComponent={
            <View style={styles.emptyContainer}>
              <View style={styles.emptyIconContainer}>
                <MaterialCommunityIcons name="school" size={64} color="#5B6AFF" />
              </View>
              <Text style={styles.emptyText}>No Admissions Plan Yet</Text>
              <Text style={styles.emptyDescription}>
                Get a personalized roadmap with application deadlines, essay milestones, and test schedules tailored to your target universities.
              </Text>

              <TouchableOpacity
                style={styles.primaryActionButton}
                onPress={handleGenerateTasks}
                disabled={generating}
              >
                {generating ? (
                  <>
                    <ActivityIndicator size="small" color="#fff" />
                    <Text style={styles.primaryActionButtonText}>
                      {generationStage || 'Checking...'}
                    </Text>
                  </>
                ) : (
                  <>
                    <MaterialCommunityIcons name="rocket-launch" size={20} color="#fff" />
                    <Text style={styles.primaryActionButtonText}>
                      Check Eligibility & Generate Tasks
                    </Text>
                  </>
                )}
              </TouchableOpacity>

              <TouchableOpacity
                style={styles.secondaryActionButton}
                onPress={() => setShowAddModal(true)}
              >
                <Text style={styles.secondaryActionButtonText}>
                  Or add a manual task
                </Text>
              </TouchableOpacity>
            </View>
          }
        />
      )}

      {/* Calendar Modal (Full Calendar) */}
      <Modal
        visible={showCalendarModal}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setShowCalendarModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.fullCalendarModal}>
            <View style={styles.fullCalendarHeader}>
              <TouchableOpacity
                onPress={() => {
                  const newMonth = new Date(calendarMonth);
                  newMonth.setMonth(newMonth.getMonth() - 1);
                  setCalendarMonth(newMonth);
                }}
              >
                <MaterialCommunityIcons name="chevron-left" size={28} color="#ECECEC" />
              </TouchableOpacity>
              <Text style={styles.fullCalendarTitle}>
                {calendarMonth.toLocaleString('default', { month: 'long', year: 'numeric' })}
              </Text>
              <TouchableOpacity
                onPress={() => {
                  const newMonth = new Date(calendarMonth);
                  newMonth.setMonth(newMonth.getMonth() + 1);
                  setCalendarMonth(newMonth);
                }}
              >
                <MaterialCommunityIcons name="chevron-right" size={28} color="#ECECEC" />
              </TouchableOpacity>
            </View>

            <View style={styles.calendarGrid}>
              {getDaysInMonth(calendarMonth).map((day) => {
                const isSelected = day.toDateString() === selectedDate.toDateString();
                const isTodayDay = day.toDateString() === new Date().toDateString();
                return (
                  <TouchableOpacity
                    key={day.toISOString()}
                    style={[
                      styles.calendarDay,
                      isSelected && styles.calendarDaySelected,
                      isTodayDay && styles.calendarDayToday,
                    ]}
                    onPress={() => {
                      setSelectedDate(day);
                      setCalendarMonth(day);
                      setShowCalendarModal(false);
                    }}
                  >
                    <Text
                      style={[
                        styles.calendarDayText,
                        isSelected && styles.calendarDayTextSelected,
                        isTodayDay && !isSelected && styles.calendarDayTextToday,
                      ]}
                    >
                      {day.getDate()}
                    </Text>
                  </TouchableOpacity>
                );
              })}
            </View>

            <TouchableOpacity
              style={styles.closeCalendarButton}
              onPress={() => setShowCalendarModal(false)}
            >
              <Text style={styles.closeCalendarText}>Close</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>

      <Modal
        visible={showAddModal}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setShowAddModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Add New Task</Text>
            <TextInput
              style={styles.modalInput}
              placeholder="What needs to be done?"
              value={newTodoText}
              onChangeText={setNewTodoText}
              multiline
              autoFocus
            />
            <View style={styles.modalActions}>
              <TouchableOpacity
                style={[styles.modalButton, styles.cancelButton]}
                onPress={() => {
                  setShowAddModal(false);
                  setNewTodoText('');
                }}
              >
                <Text style={styles.cancelButtonText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.modalButton, styles.saveButton]}
                onPress={handleAddTodo}
              >
                <Text style={styles.saveButtonText}>Add Task</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>

      {/* Task Completion/Skip Confirmation Modal */}
      <Modal
        visible={showFeedbackModal}
        animationType="fade"
        transparent={true}
        onRequestClose={() => setShowFeedbackModal(false)}
      >
        <View style={styles.successModalOverlay}>
          <View style={styles.successModal}>
            <View style={[
              styles.successIconContainer,
              { backgroundColor: feedbackType === 'completed' ? 'rgba(52, 199, 89, 0.15)' : 'rgba(255, 149, 0, 0.15)' }
            ]}>
              <MaterialCommunityIcons
                name={feedbackType === 'completed' ? 'check-circle' : 'close-circle'}
                size={48}
                color={feedbackType === 'completed' ? '#34C759' : '#FF9500'}
              />
            </View>
            <Text style={styles.successTitle}>
              {feedbackType === 'completed' ? 'Task Completed!' : 'Task Skipped'}
            </Text>
            <Text style={styles.successTaskName} numberOfLines={2}>
              {feedbackTask?.title}
            </Text>
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
}

const getPriorityColor = (priority: number | string) => {
  // Convert number to string if needed (backend sends 1=low, 2=medium, 3=high)
  const priorityStr = typeof priority === 'number'
    ? (priority === 3 ? 'high' : priority === 2 ? 'medium' : 'low')
    : priority?.toLowerCase();

  switch (priorityStr) {
    case 'high': return '#FF3B30';
    case 'medium': return '#FF9500';
    case 'low': return '#34C759';
    default: return '#999';
  }
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.bg,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: spacing.md,
    paddingTop: spacing.md,
    backgroundColor: colors.surface,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: colors.text,
  },
  addButton: {
    backgroundColor: colors.primary,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: borderRadius.lg,
  },
  addButtonText: {
    color: '#fff',
    fontWeight: '600',
  },
  // Goals Section Styles
  goalsSection: {
    backgroundColor: colors.surface,
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  goalsHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.md,
  },
  goalsTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: colors.text,
  },
  viewMoreButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  viewMoreText: {
    fontSize: 13,
    fontWeight: '600',
    color: colors.primary,
  },
  goalsCarousel: {
    flexDirection: 'row',
    gap: spacing.md,
  },
  goalCard: {
    width: 200,
  },
  goalHeader: {
    marginBottom: spacing.sm,
  },
  goalTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: colors.text,
    marginBottom: 4,
    flex: 1,
  },
  goalCategoryBadge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 8,
  },
  goalCategoryText: {
    fontSize: 10,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  goalDescription: {
    fontSize: 12,
    color: colors.textSecondary,
    marginBottom: spacing.sm,
    lineHeight: 16,
  },
  goalProgressContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
  },
  goalProgressBar: {
    flex: 1,
    height: 4,
    backgroundColor: colors.bg,
    borderRadius: 2,
    overflow: 'hidden',
  },
  goalProgressFill: {
    height: '100%',
    backgroundColor: colors.primary,
    borderRadius: 2,
  },
  goalProgressText: {
    fontSize: 12,
    fontWeight: '600',
    color: colors.primary,
    minWidth: 35,
    textAlign: 'right',
  },
  noGoalsContainer: {
    alignItems: 'center',
    paddingVertical: spacing.xl,
    gap: spacing.sm,
  },
  noGoalsText: {
    fontSize: 14,
    color: colors.textSecondary,
  },
  createGoalButton: {
    backgroundColor: colors.primary,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: borderRadius.md,
    marginTop: spacing.sm,
  },
  createGoalButtonText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  calendarContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.bg,
    paddingVertical: spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: colors.surface,
  },
  calendarScroll: {
    paddingHorizontal: spacing.md,
    gap: spacing.sm,
  },
  dayButton: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 10,
    paddingHorizontal: 14,
    borderRadius: borderRadius.md,
    backgroundColor: colors.surface,
    minWidth: 60,
    borderWidth: 1,
    borderColor: colors.border,
  },
  dayButtonSelected: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  dayButtonToday: {
    borderColor: colors.primary,
    borderWidth: 2,
  },
  dayName: {
    fontSize: 11,
    fontWeight: '600',
    color: colors.textSecondary,
    marginBottom: 4,
    textTransform: 'uppercase',
  },
  dayNameSelected: {
    color: '#fff',
  },
  dayNumber: {
    fontSize: 16,
    fontWeight: 'bold',
    color: colors.text,
  },
  dayNumberSelected: {
    color: '#fff',
  },
  calendarArrow: {
    paddingHorizontal: spacing.md,
    paddingVertical: 10,
  },
  statusFilterContainer: {
    flexDirection: 'row',
    paddingHorizontal: spacing.md,
    paddingTop: spacing.sm,
    paddingBottom: spacing.sm,
    gap: spacing.sm,
    backgroundColor: colors.bg,
  },
  statusFilterButton: {
    flex: 1,
    paddingVertical: 6,
    paddingHorizontal: spacing.sm,
    borderRadius: borderRadius.sm,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    alignItems: 'center',
  },
  statusFilterButtonActive: {
    backgroundColor: colors.success,
    borderColor: colors.success,
  },
  statusFilterText: {
    fontSize: 12,
    fontWeight: '600',
    color: colors.textSecondary,
  },
  statusFilterTextActive: {
    color: '#fff',
  },
  listContent: {
    padding: spacing.md,
  },
  todoCard: {
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: borderRadius.md,
    padding: spacing.md,
    marginBottom: spacing.sm,
  },
  todoHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: spacing.sm,
  },
  todoInfo: {
    flex: 1,
  },
  todoTask: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 4,
    color: colors.text,
  },
  todoTime: {
    fontSize: 13,
    color: colors.textSecondary,
  },
  priorityBadge: {
    paddingHorizontal: spacing.sm,
    paddingVertical: 4,
    borderRadius: borderRadius.xs,
    height: 24,
  },
  priorityText: {
    fontSize: 11,
    color: '#fff',
    fontWeight: '600',
    textTransform: 'uppercase',
  },
  todoActions: {
    flexDirection: 'row',
    gap: spacing.sm,
  },
  actionButton: {
    flex: 1,
    paddingVertical: 10,
    borderRadius: borderRadius.sm,
    alignItems: 'center',
  },
  doneButton: {
    backgroundColor: colors.success,
  },
  skipButton: {
    backgroundColor: colors.warning,
  },
  actionButtonText: {
    color: '#fff',
    fontWeight: '600',
  },
  emptyContainer: {
    alignItems: 'center',
    paddingTop: 40,
    paddingHorizontal: spacing.xl,
  },
  emptyIconContainer: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: 'rgba(91, 106, 255, 0.1)',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.lg,
  },
  emptyText: {
    fontSize: 20,
    fontWeight: '700',
    color: colors.text,
    marginBottom: spacing.sm,
    textAlign: 'center',
  },
  emptyDescription: {
    fontSize: 14,
    color: colors.textSecondary,
    textAlign: 'center',
    marginBottom: spacing.xl,
    lineHeight: 20,
    paddingHorizontal: spacing.md,
  },
  emptySubtext: {
    fontSize: 14,
    color: colors.textTertiary,
  },
  benefitsRow: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: spacing.lg,
    marginBottom: spacing.xl,
  },
  benefitItem: {
    alignItems: 'center',
    gap: spacing.xs,
  },
  benefitText: {
    fontSize: 11,
    fontWeight: '600',
    color: colors.textSecondary,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  generateButton: {
    marginTop: spacing.lg,
    backgroundColor: colors.primary,
    paddingVertical: 14,
    paddingHorizontal: spacing.lg,
    borderRadius: borderRadius.md,
  },
  generatePlanButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.sm,
    backgroundColor: colors.primary,
    paddingVertical: 14,
    paddingHorizontal: spacing.xl,
    borderRadius: borderRadius.lg,
    shadowColor: colors.primary,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 4,
    elevation: 2,
  },
  generateButtonText: {
    color: '#fff',
    fontSize: 15,
    fontWeight: '600',
    textAlign: 'center',
  },
  generatePlanButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.7)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: spacing.lg,
  },
  modalContent: {
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: borderRadius.lg,
    padding: spacing.lg,
    width: '100%',
    maxWidth: 400,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: spacing.md,
    color: colors.text,
  },
  modalSubtitle: {
    fontSize: 16,
    color: colors.textSecondary,
    marginBottom: spacing.lg,
    textAlign: 'center',
  },
  modalInput: {
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.bg,
    color: colors.text,
    borderRadius: borderRadius.sm,
    padding: spacing.sm,
    fontSize: 16,
    minHeight: 100,
    textAlignVertical: 'top',
    marginBottom: spacing.md,
  },
  modalActions: {
    flexDirection: 'row',
    gap: spacing.sm,
  },
  modalButton: {
    flex: 1,
    paddingVertical: spacing.sm,
    borderRadius: borderRadius.sm,
    alignItems: 'center',
  },
  cancelButton: {
    backgroundColor: colors.border,
  },
  saveButton: {
    backgroundColor: colors.primary,
  },
  cancelButtonText: {
    color: colors.text,
    fontWeight: '600',
  },
  saveButtonText: {
    color: '#fff',
    fontWeight: '600',
  },
  viewSwitcher: {
    flexDirection: 'column',
    padding: spacing.sm,
    paddingHorizontal: spacing.md,
    gap: spacing.sm,
    backgroundColor: colors.surface,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  viewModeToggleRow: {
    flexDirection: 'row',
    gap: spacing.sm,
  },
  statusFilterRow: {
    flexDirection: 'row',
    gap: spacing.xs,
  },
  viewTab: {
    flex: 1,
    minWidth: 140,
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.md,
    alignItems: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: borderRadius.sm,
  },
  viewTabActive: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  viewTabText: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.textSecondary,
    textAlign: 'center',
  },
  viewTabTextActive: {
    color: '#fff',
  },
  filterButton: {
    minWidth: 80,
    height: 36,
    paddingHorizontal: 12,
    paddingVertical: 0,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: borderRadius.sm,
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderWidth: 1,
    borderColor: colors.border,
  },
  filterButtonText: {
    fontSize: 13,
    fontWeight: '600',
    color: colors.textSecondary,
    textAlign: 'center',
  },
  // Compact card styles
  todoCard: {
    borderRadius: borderRadius.lg,
  },
  todoCardContent: {
    flexDirection: 'row',
    alignItems: 'stretch',
  },
  compactCard: {
    flexDirection: 'row',
    backgroundColor: '#1A1A1A',
    borderRadius: 12,
    marginBottom: 12,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: '#2A2A2A',
    alignItems: 'stretch',
  },
  compactCardPast: {
    opacity: 0.6,
  },
  compactCardDone: {
    backgroundColor: `${colors.success}14`,
    borderWidth: 1,
    borderColor: `${colors.success}33`,
  },
  compactCardSkipped: {
    backgroundColor: `${colors.warning}14`,
    borderWidth: 1,
    borderColor: `${colors.warning}33`,
    opacity: 0.7,
  },
  doneIndicator: {
    position: 'absolute',
    top: 10,
    right: 10,
    zIndex: 1,
  },
  leftBorder: {
    width: 4,
    alignSelf: 'stretch',
    borderRadius: 2,
    marginRight: spacing.sm,
  },
  taskContent: {
    flex: 1,
  },
  taskInfo: {
    marginBottom: spacing.sm,
  },
  taskTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: colors.text,
    marginBottom: 6,
    lineHeight: 20,
  },
  taskTitlePast: {
    color: colors.textSecondary,
  },
  taskTitleDone: {
    color: colors.success,
    textDecorationLine: 'line-through',
    opacity: 0.8,
  },
  taskTitleSkipped: {
    color: colors.warning,
    textDecorationLine: 'line-through',
    opacity: 0.7,
  },
  goalBadge: {
    alignSelf: 'flex-start',
    paddingHorizontal: spacing.sm,
    paddingVertical: 3,
    borderRadius: borderRadius.sm,
    borderWidth: 1,
    marginBottom: 6,
  },
  goalBadgeText: {
    fontSize: 11,
    fontWeight: '600',
  },
  taskTime: {
    fontSize: 12,
    color: colors.textSecondary,
    marginTop: 4,
  },
  taskTimePast: {
    color: colors.textTertiary,
  },
  bottomActions: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: spacing.sm,
    alignItems: 'center',
    paddingTop: spacing.sm,
    borderTopWidth: 1,
    borderTopColor: colors.border,
  },
  actionButtonsGroup: {
    flexDirection: 'row',
    gap: spacing.sm,
    alignItems: 'center',
  },
  inlineActions: {
    flexDirection: 'row',
    gap: 6,
    alignItems: 'center',
  },
  miniButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: colors.bg,
    borderWidth: 1,
    borderColor: colors.border,
    alignItems: 'center',
    justifyContent: 'center',
  },
  viewDetailsButton: {
    flexDirection: 'row',
    height: 36,
    borderRadius: 18,
    backgroundColor: colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 4,
    paddingHorizontal: spacing.md,
    shadowColor: colors.primary,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.3,
    shadowRadius: 4,
    elevation: 3,
  },
  viewDetailsText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  // Section headers
  sectionHeader: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.text,
    paddingHorizontal: spacing.md,
    paddingTop: spacing.md,
    paddingBottom: spacing.sm,
    backgroundColor: colors.bg,
  },
  sectionHeaderPast: {
    color: colors.textSecondary,
  },
  sectionHeaderToday: {
    color: colors.error,
  },
  dayPickerContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.bg,
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: colors.surface,
  },
  dayPickerContent: {
    paddingRight: spacing.sm,
    gap: spacing.sm,
  },
  dayButtonCircle: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    justifyContent: 'center',
    alignItems: 'center',
  },
  dayButtonCircleSelected: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  dayButtonCircleToday: {
    borderColor: colors.primary,
    borderWidth: 2,
  },
  dayButtonCircleText: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.textSecondary,
  },
  dayButtonCircleTextSelected: {
    color: '#fff',
  },
  calendarIconButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    justifyContent: 'center',
    alignItems: 'center',
  },
  fullCalendarModal: {
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: borderRadius.xl,
    padding: spacing.lg,
    width: '90%',
    maxHeight: '80%',
  },
  fullCalendarHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.lg,
  },
  fullCalendarTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: colors.text,
  },
  calendarGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    marginBottom: spacing.lg,
  },
  calendarDay: {
    width: '13%',
    aspectRatio: 1,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: spacing.sm,
    borderRadius: borderRadius.sm,
    backgroundColor: colors.bg,
    borderWidth: 1,
    borderColor: colors.border,
  },
  calendarDaySelected: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  calendarDayToday: {
    borderColor: colors.primary,
    borderWidth: 2,
  },
  calendarDayText: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.textSecondary,
  },
  calendarDayTextSelected: {
    color: '#fff',
  },
  calendarDayTextToday: {
    color: colors.primary,
  },
  closeCalendarButton: {
    backgroundColor: colors.bg,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: borderRadius.md,
    paddingVertical: 14,
    alignItems: 'center',
  },
  closeCalendarText: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.text,
  },
  // AI Properties Styles
  aiPropertiesRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginTop: 6,
    marginBottom: 4,
  },
  aiPropertyBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: borderRadius.xs,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.bg,
    gap: 3,
  },
  aiPropertyText: {
    fontSize: 10,
    fontWeight: '600',
  },
  cognitiveDot: {
    width: 4,
    height: 4,
    borderRadius: 2,
    backgroundColor: colors.border,
    marginHorizontal: 1,
  },
  cognitiveDotFilled: {
    backgroundColor: colors.warning,
  },
  timeboxBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: borderRadius.xs,
    backgroundColor: colors.bg,
    gap: 3,
  },
  timeboxText: {
    fontSize: 10,
    fontWeight: '600',
    color: colors.textSecondary,
  },

  // Feedback Modal Styles
  feedbackModal: {
    backgroundColor: colors.surface,
    borderTopLeftRadius: borderRadius.xxl,
    borderTopRightRadius: borderRadius.xxl,
    width: '100%',
    maxHeight: '85%',
    padding: spacing.lg,
  },
  feedbackHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.md,
    paddingBottom: spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  feedbackTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: colors.text,
  },
  feedbackContent: {
    flex: 1,
  },
  feedbackTaskTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.primary,
    marginBottom: spacing.lg,
  },
  feedbackLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.text,
    marginBottom: spacing.sm,
    marginTop: spacing.md,
  },
  ratingRow: {
    flexDirection: 'row',
    gap: spacing.sm,
    marginBottom: spacing.sm,
  },
  ratingButton: {
    flex: 1,
    alignItems: 'center',
    paddingVertical: spacing.sm,
    backgroundColor: colors.bg,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: borderRadius.sm,
  },
  ratingButtonActive: {
    borderColor: colors.warning,
  },
  feedbackInput: {
    backgroundColor: colors.bg,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: borderRadius.sm,
    padding: spacing.sm,
    fontSize: 15,
    color: colors.text,
    marginBottom: spacing.sm,
  },
  energyRow: {
    flexDirection: 'row',
    gap: 10,
    marginBottom: spacing.sm,
  },
  energyButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    paddingVertical: spacing.sm,
    backgroundColor: colors.bg,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: borderRadius.sm,
  },
  energyButtonActive: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  energyText: {
    fontSize: 13,
    fontWeight: '600',
    color: colors.textSecondary,
  },
  energyTextActive: {
    color: '#fff',
  },
  skipReasonsContainer: {
    gap: spacing.sm,
    marginBottom: spacing.sm,
  },
  skipReasonButton: {
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.md,
    backgroundColor: colors.bg,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: borderRadius.sm,
  },
  skipReasonButtonActive: {
    backgroundColor: colors.warning,
    borderColor: colors.warning,
  },
  skipReasonText: {
    fontSize: 14,
    fontWeight: '500',
    color: colors.textSecondary,
    textAlign: 'center',
  },
  skipReasonTextActive: {
    color: '#fff',
  },
  feedbackNotesInput: {
    backgroundColor: colors.bg,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: borderRadius.sm,
    padding: spacing.sm,
    fontSize: 14,
    color: colors.text,
    minHeight: 80,
    textAlignVertical: 'top',
    marginBottom: spacing.lg,
  },
  submitFeedbackButton: {
    backgroundColor: colors.primary,
    paddingVertical: spacing.md,
    borderRadius: borderRadius.md,
    alignItems: 'center',
    marginBottom: 10,
  },
  submitFeedbackText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#fff',
  },
  successModalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: spacing.lg,
  },
  successModal: {
    backgroundColor: colors.surface,
    borderRadius: borderRadius.xl,
    padding: spacing.xl,
    alignItems: 'center',
    width: '80%',
    maxWidth: 300,
    borderWidth: 1,
    borderColor: colors.border,
  },
  successIconContainer: {
    width: 80,
    height: 80,
    borderRadius: 40,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: spacing.md,
  },
  successTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: colors.text,
    marginBottom: spacing.sm,
    textAlign: 'center',
  },
  successTaskName: {
    fontSize: 14,
    color: colors.textSecondary,
    textAlign: 'center',
    lineHeight: 20,
  },
  statusBadge: {
    backgroundColor: `${colors.success}26`,
    paddingHorizontal: spacing.sm,
    paddingVertical: 6,
    borderRadius: borderRadius.md,
    borderWidth: 1,
    borderColor: `${colors.success}4D`,
  },
  statusBadgeSkipped: {
    backgroundColor: `${colors.warning}26`,
    borderColor: `${colors.warning}4D`,
  },
  statusBadgeText: {
    fontSize: 12,
    fontWeight: '600',
    color: colors.text,
  },
  guestPromptContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: spacing.xl,
  },
  guestPromptTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: colors.text,
    marginTop: spacing.lg,
    marginBottom: spacing.sm,
    textAlign: 'center',
  },
  guestPromptText: {
    fontSize: 16,
    color: colors.textSecondary,
    textAlign: 'center',
    marginBottom: spacing.xl,
    lineHeight: 24,
  },
  signInButton: {
    flexDirection: 'row',
    backgroundColor: colors.primary,
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.xl,
    borderRadius: borderRadius.md,
    alignItems: 'center',
    gap: spacing.sm,
    marginBottom: spacing.md,
    width: '100%',
    justifyContent: 'center',
  },
  signInButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '600',
  },
  createAccountButton: {
    backgroundColor: 'transparent',
    borderWidth: 1,
    borderColor: colors.primary,
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.xl,
    borderRadius: borderRadius.md,
    width: '100%',
    alignItems: 'center',
  },
  createAccountButtonText: {
    color: colors.primary,
    fontSize: 16,
    fontWeight: '600',
  },
  universitySection: {
    marginBottom: spacing.lg,
    backgroundColor: colors.surface,
    borderRadius: borderRadius.lg,
    padding: spacing.md,
    borderWidth: 1,
    borderColor: colors.border,
  },
  universityHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.md,
    paddingBottom: spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  universityName: {
    fontSize: 18,
    fontWeight: '700',
    color: colors.text,
    flex: 1,
  },
  universityDeadline: {
    fontSize: 13,
    color: colors.error,
    fontWeight: '600',
  },
  blockersSection: {
    marginBottom: spacing.md,
  },
  blockersTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.warning,
    marginBottom: spacing.sm,
  },
  appTasksSection: {
    marginBottom: spacing.md,
  },
  appTasksTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.success,
    marginBottom: spacing.sm,
  },
  foundationSection: {
    backgroundColor: 'rgba(91, 106, 255, 0.05)',
    padding: spacing.sm,
    borderRadius: borderRadius.sm,
  },
  foundationTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.primary,
    marginBottom: spacing.sm,
  },
  mainViewToggle: {
    flexDirection: 'row',
    gap: spacing.sm,
  },
  statusFilter: {
    flexDirection: 'row',
    gap: spacing.sm,
    marginTop: spacing.sm,
  },
  filterButton: {
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
    borderRadius: borderRadius.sm,
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderWidth: 1,
    borderColor: colors.border,
  },
  filterButtonActive: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  filterButtonText: {
    fontSize: 13,
    fontWeight: '600',
    color: colors.textSecondary,
  },
  filterButtonTextActive: {
    color: '#fff',
  },
  // Status Strip
  statusStrip: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.md,
    backgroundColor: 'rgba(91, 106, 255, 0.1)',
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  statusItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs,
  },
  statusLabel: {
    fontSize: 13,
    color: colors.textSecondary,
  },
  statusValue: {
    fontSize: 13,
    fontWeight: '600',
    color: colors.text,
  },
  // View Tab (improved toggle)
  viewTab: {
    flex: 1,
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.md,
    alignItems: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: borderRadius.sm,
  },
  viewTabActive: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  viewTabText: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.textSecondary,
  },
  viewTabTextActive: {
    color: '#fff',
  },
  // Empty List Content
  emptyListContent: {
    flexGrow: 1,
    justifyContent: 'center',
    paddingVertical: spacing.xl * 2,
  },
  // Generate Plan Button (small, for header)
  generatePlanButtonSmall: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs,
    backgroundColor: colors.primary,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs,
    borderRadius: borderRadius.sm,
  },
  // Primary Action Button (for empty state)
  primaryActionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.sm,
    backgroundColor: colors.primary,
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.xl,
    borderRadius: borderRadius.md,
    marginTop: spacing.lg,
    minWidth: 280,
  },
  primaryActionButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
  },
  // Secondary Action Button (for empty state)
  secondaryActionButton: {
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.xl,
    borderRadius: borderRadius.md,
    marginTop: spacing.sm,
    borderWidth: 1,
    borderColor: colors.border,
  },
  secondaryActionButtonText: {
    fontSize: 14,
    fontWeight: '500',
    color: colors.primary,
  },
  // NEW: Coverage Meter Styles
  coverageContainer: {
    backgroundColor: colors.card,
    borderRadius: borderRadius.lg,
    padding: spacing.md,
    marginHorizontal: spacing.md,
    marginTop: spacing.sm,
    marginBottom: spacing.md,
    borderWidth: 1,
    borderColor: colors.border,
  },
  coverageHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.sm,
  },
  coverageTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.text,
  },
  coverageBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs,
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
    borderRadius: borderRadius.sm,
  },
  verifiedBadge: {
    backgroundColor: '#34C75920',
  },
  draftBadge: {
    backgroundColor: '#FF950020',
  },
  coverageBadgeText: {
    fontSize: 12,
    fontWeight: '600',
  },
  verifiedText: {
    color: '#34C759',
  },
  draftText: {
    color: '#FF9500',
  },
  coverageMetrics: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-around',
    paddingVertical: spacing.sm,
  },
  metric: {
    alignItems: 'center',
  },
  metricLabel: {
    fontSize: 11,
    color: colors.textSecondary,
    marginBottom: spacing.xs,
  },
  metricValue: {
    fontSize: 20,
    fontWeight: '700',
    color: colors.text,
  },
  metricExcellent: {
    color: '#34C759',
  },
  metricGood: {
    color: '#5B6AFF',
  },
  metricDivider: {
    width: 1,
    height: 40,
    backgroundColor: colors.border,
  },
  verifyButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.sm,
    backgroundColor: '#5B6AFF20',
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.md,
    borderRadius: borderRadius.sm,
    marginTop: spacing.sm,
  },
  verifyButtonText: {
    fontSize: 12,
    fontWeight: '500',
    color: '#5B6AFF',
  },
  // NEW: Compact Card Styles
  compactCardContent: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: spacing.sm,
  },
  compactCardMain: {
    flex: 1,
    marginLeft: spacing.sm,
  },
  compactCardTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.text,
    marginBottom: spacing.xs,
  },
  compactCardWhy: {
    fontSize: 12,
    color: colors.textSecondary,
    marginBottom: spacing.sm,
    fontStyle: 'italic',
  },
  compactCardChips: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    alignItems: 'center',
    gap: spacing.xs,
  },
  compactChip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs / 2,
    backgroundColor: colors.background,
    paddingHorizontal: spacing.xs,
    paddingVertical: 2,
    borderRadius: borderRadius.xs,
  },
  compactChipText: {
    fontSize: 10,
    color: colors.textSecondary,
  },
  blockerChip: {
    backgroundColor: '#FF3B3020',
  },
  evidenceCompleteChip: {
    backgroundColor: '#34C75920',
  },
  evidencePartialChip: {
    backgroundColor: '#FF950020',
  },
  scopeChip: {
    backgroundColor: '#5B6AFF20',
  },
  scopeChipText: {
    fontSize: 10,
    fontWeight: '600',
    color: '#5B6AFF',
    textTransform: 'uppercase',
  },
  compactCardProgress: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs,
    marginTop: spacing.sm,
  },
  compactProgressText: {
    fontSize: 11,
    color: colors.textSecondary,
    fontWeight: '500',
  },
  // NEW: Stage Section Styles
  stageSection: {
    marginBottom: spacing.lg,
  },
  stageHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: spacing.md,
    paddingTop: spacing.md,
    paddingBottom: spacing.sm,
    backgroundColor: colors.card,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  stageTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: colors.text,
  },
  blockerCountBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs,
    backgroundColor: '#FF3B3020',
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
    borderRadius: borderRadius.sm,
  },
  blockerCountText: {
    fontSize: 11,
    fontWeight: '600',
    color: colors.error,
  },
  regularTasksSection: {
    paddingHorizontal: spacing.md,
    paddingTop: spacing.sm,
  },
});
