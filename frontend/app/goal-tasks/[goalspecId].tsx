import { useState, useEffect } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  RefreshControl,
  ActivityIndicator,
} from 'react-native';
import { todosAPI, goalSpecAPI } from '@/services/api';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { useLocalSearchParams, useRouter } from 'expo-router';

const COLORS = {
  bg: '#131313',
  surface: '#2A2A2A',
  border: '#3E3E3E',
  text: '#ECECEC',
  textSecondary: '#8E8E8E',
  primary: '#5B6AFF',
  success: '#34C759',
  warning: '#FF9500',
  danger: '#EF4444',
  study: '#FF3B30',
  language: '#3B82F6',
  sport: '#34C759',
  career: '#06B6D4',
  personal: '#A855F7',
};

const getCategoryColor = (category: string): string => {
  switch (category?.toLowerCase()) {
    case 'study': return COLORS.study;
    case 'language': return COLORS.language;
    case 'sport': return COLORS.sport;
    case 'career': return COLORS.career;
    default: return COLORS.primary;
  }
};

const getCategoryIcon = (category: string): string => {
  switch (category?.toLowerCase()) {
    case 'study': return 'school';
    case 'language': return 'translate';
    case 'sport': return 'dumbbell';
    case 'career': return 'briefcase';
    case 'finance': return 'cash';
    case 'health': return 'heart-pulse';
    case 'creative': return 'palette';
    case 'admin': return 'file-document';
    case 'research': return 'flask';
    case 'networking': return 'account-group';
    case 'travel': return 'airplane';
    default: return 'star';
  }
};

export default function GoalTasksScreen() {
  const router = useRouter();
  const { goalspecId } = useLocalSearchParams();
  const [goalspec, setGoalspec] = useState<any>(null);
  const [tasks, setTasks] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadGoalAndTasks();
  }, [goalspecId]);

  const loadGoalAndTasks = async () => {
    try {
      setLoading(true);

      // Convert goalspecId to number for comparisons
      const numericGoalspecId = Number(goalspecId);

      // Load the specific goalspec
      const goalspecResponse = await goalSpecAPI.retrieve(numericGoalspecId);
      setGoalspec(goalspecResponse.data);

      // Load all tasks filtered by this goalspec
      const tasksResponse = await todosAPI.list();
      let allTasks = tasksResponse.data.results || tasksResponse.data;

      // Filter tasks that belong to this goalspec
      // Note: task.goalspec is a number from the backend
      const goalTasks = allTasks.filter((task: any) => task.goalspec === numericGoalspecId);

      // Sort by scheduled_date
      goalTasks.sort((a: any, b: any) => {
        const dateA = new Date(a.scheduled_date).getTime();
        const dateB = new Date(b.scheduled_date).getTime();
        return dateA - dateB;
      });

      setTasks(goalTasks);
    } catch (error) {
      console.error('Failed to load goal tasks:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleRefresh = () => {
    setRefreshing(true);
    loadGoalAndTasks();
  };

  const handleTaskPress = (taskId: number) => {
    router.push(`/task/${taskId}` as any);
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'done':
        return {
          label: 'Done',
          color: COLORS.success,
          icon: 'check-circle',
        };
      case 'ready':
      case 'pending':
        return {
          label: 'Pending',
          color: COLORS.warning,
          icon: 'clock-outline',
        };
      case 'skipped':
        return {
          label: 'Skipped',
          color: COLORS.textSecondary,
          icon: 'skip-forward',
        };
      default:
        return {
          label: status,
          color: COLORS.textSecondary,
          icon: 'help-circle',
        };
    }
  };

  const renderTask = ({ item }: any) => {
    const statusBadge = getStatusBadge(item.status);
    const taskDate = new Date(item.scheduled_date);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const isOverdue = taskDate < today && item.status !== 'done' && item.status !== 'skipped';

    return (
      <TouchableOpacity
        style={styles.taskCard}
        onPress={() => handleTaskPress(item.id)}
        activeOpacity={0.7}
      >
        <View style={styles.taskHeader}>
          <Text style={styles.taskTitle} numberOfLines={2}>
            {item.title}
          </Text>
          <View style={[styles.statusBadge, { backgroundColor: statusBadge.color + '20' }]}>
            <MaterialCommunityIcons
              name={statusBadge.icon as any}
              size={14}
              color={statusBadge.color}
            />
            <Text style={[styles.statusText, { color: statusBadge.color }]}>
              {statusBadge.label}
            </Text>
          </View>
        </View>

        {item.description && (
          <Text style={styles.taskDescription} numberOfLines={2}>
            {item.description}
          </Text>
        )}

        <View style={styles.taskMeta}>
          <View style={styles.metaItem}>
            <MaterialCommunityIcons
              name="calendar"
              size={14}
              color={isOverdue ? COLORS.danger : COLORS.textSecondary}
            />
            <Text style={[styles.metaText, isOverdue && styles.overdueText]}>
              {new Date(item.scheduled_date).toLocaleDateString('en-US', {
                month: 'short',
                day: 'numeric',
                year: 'numeric',
              })}
              {isOverdue && ' (Overdue)'}
            </Text>
          </View>

          {item.timebox_minutes && (
            <View style={styles.metaItem}>
              <MaterialCommunityIcons
                name="clock-outline"
                size={14}
                color={COLORS.textSecondary}
              />
              <Text style={styles.metaText}>{item.timebox_minutes}m</Text>
            </View>
          )}

          {item.energy_level && (
            <View style={styles.metaItem}>
              <MaterialCommunityIcons
                name={
                  item.energy_level === 'high'
                    ? 'flash'
                    : item.energy_level === 'medium'
                    ? 'battery-medium'
                    : 'weather-night'
                }
                size={14}
                color={COLORS.textSecondary}
              />
              <Text style={styles.metaText}>{item.energy_level}</Text>
            </View>
          )}
        </View>
      </TouchableOpacity>
    );
  };

  const renderEmptyState = () => (
    <View style={styles.emptyContainer}>
      <MaterialCommunityIcons
        name={getCategoryIcon(goalspec?.category || '')}
        size={64}
        color={COLORS.border}
      />
      <Text style={styles.emptyTitle}>No tasks for this goal yet</Text>
      <Text style={styles.emptyDescription}>
        Tasks for "{goalspec?.title}" will appear here
      </Text>
    </View>
  );

  if (loading) {
    return (
      <View style={styles.container}>
        <View style={styles.header}>
          <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
            <MaterialCommunityIcons name="arrow-left" size={24} color={COLORS.text} />
          </TouchableOpacity>
          <Text style={styles.headerTitle} numberOfLines={1}>
            Loading...
          </Text>
          <View style={styles.backButton} />
        </View>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={getCategoryColor(goalspec?.category || '')} />
        </View>
      </View>
    );
  }

  const categoryColor = getCategoryColor(goalspec?.category || '');
  const categoryIcon = getCategoryIcon(goalspec?.category || '');

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
          <MaterialCommunityIcons name="arrow-left" size={24} color={COLORS.text} />
        </TouchableOpacity>
        <View style={styles.headerTitleContainer}>
          <View style={[styles.categoryIcon, { backgroundColor: categoryColor }]}>
            <MaterialCommunityIcons name={categoryIcon as any} size={18} color="#fff" />
          </View>
          <Text style={styles.headerTitle} numberOfLines={1}>
            {goalspec?.title || 'Goal Tasks'}
          </Text>
        </View>
        <View style={styles.backButton} />
      </View>

      {/* Goal Info Card */}
      {goalspec && (
        <View style={styles.goalInfoCard}>
          <View style={styles.goalInfoHeader}>
            <Text style={styles.goalTitle}>{goalspec.title}</Text>
            {goalspec.target_date && (
              <View style={styles.targetDateBadge}>
                <MaterialCommunityIcons name="calendar-check" size={14} color={categoryColor} />
                <Text style={[styles.targetDateText, { color: categoryColor }]}>
                  {new Date(goalspec.target_date).toLocaleDateString('en-US', {
                    month: 'short',
                    day: 'numeric',
                    year: 'numeric',
                  })}
                </Text>
              </View>
            )}
          </View>
          {goalspec.description && (
            <Text style={styles.goalDescription} numberOfLines={2}>
              {goalspec.description}
            </Text>
          )}
        </View>
      )}

      {/* Stats Bar */}
      <View style={styles.statsBar}>
        <View style={styles.statItem}>
          <Text style={styles.statValue}>{tasks.length}</Text>
          <Text style={styles.statLabel}>Total</Text>
        </View>
        <View style={styles.statDivider} />
        <View style={styles.statItem}>
          <Text style={[styles.statValue, { color: COLORS.success }]}>
            {tasks.filter((t) => t.status === 'done').length}
          </Text>
          <Text style={styles.statLabel}>Done</Text>
        </View>
        <View style={styles.statDivider} />
        <View style={styles.statItem}>
          <Text style={[styles.statValue, { color: COLORS.warning }]}>
            {tasks.filter((t) => t.status === 'ready' || t.status === 'pending').length}
          </Text>
          <Text style={styles.statLabel}>Pending</Text>
        </View>
      </View>

      {/* Tasks List */}
      <FlatList
        data={tasks}
        renderItem={renderTask}
        keyExtractor={(item) => item.id.toString()}
        contentContainerStyle={styles.listContent}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={handleRefresh}
            tintColor={categoryColor}
          />
        }
        ListEmptyComponent={renderEmptyState}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.bg,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingTop: 60,
    paddingBottom: 16,
    backgroundColor: COLORS.bg,
  },
  backButton: {
    width: 40,
    height: 40,
    justifyContent: 'center',
    alignItems: 'center',
  },
  headerTitleContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    flex: 1,
    marginHorizontal: 8,
  },
  categoryIcon: {
    width: 32,
    height: 32,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: COLORS.text,
    flex: 1,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  goalInfoCard: {
    backgroundColor: COLORS.surface,
    marginHorizontal: 16,
    marginBottom: 12,
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  goalInfoHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 8,
    gap: 12,
  },
  goalTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
    flex: 1,
  },
  targetDateBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 8,
    paddingVertical: 4,
    backgroundColor: COLORS.bg,
    borderRadius: 6,
  },
  targetDateText: {
    fontSize: 11,
    fontWeight: '600',
  },
  goalDescription: {
    fontSize: 14,
    color: COLORS.textSecondary,
    lineHeight: 20,
  },
  statsBar: {
    flexDirection: 'row',
    backgroundColor: COLORS.surface,
    paddingVertical: 16,
    paddingHorizontal: 20,
    marginHorizontal: 16,
    marginBottom: 12,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  statItem: {
    flex: 1,
    alignItems: 'center',
  },
  statValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: COLORS.text,
    marginBottom: 4,
  },
  statLabel: {
    fontSize: 12,
    color: COLORS.textSecondary,
  },
  statDivider: {
    width: 1,
    backgroundColor: COLORS.border,
  },
  listContent: {
    paddingHorizontal: 16,
    paddingBottom: 16,
  },
  taskCard: {
    backgroundColor: COLORS.surface,
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  taskHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 8,
    gap: 12,
  },
  taskTitle: {
    flex: 1,
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
    lineHeight: 22,
  },
  statusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  statusText: {
    fontSize: 11,
    fontWeight: '600',
  },
  taskDescription: {
    fontSize: 14,
    color: COLORS.textSecondary,
    marginBottom: 12,
    lineHeight: 20,
  },
  taskMeta: {
    flexDirection: 'row',
    gap: 16,
    flexWrap: 'wrap',
  },
  metaItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  metaText: {
    fontSize: 12,
    color: COLORS.textSecondary,
  },
  overdueText: {
    color: COLORS.danger,
    fontWeight: '600',
  },
  emptyContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 80,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: COLORS.text,
    marginTop: 16,
    marginBottom: 8,
  },
  emptyDescription: {
    fontSize: 14,
    color: COLORS.textSecondary,
    textAlign: 'center',
    paddingHorizontal: 40,
  },
});
