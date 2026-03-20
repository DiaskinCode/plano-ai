import { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  Dimensions,
  Animated,
} from 'react-native';
import { analyticsAPI } from '@/services/api';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import Svg, { Circle, Rect, G } from 'react-native-svg';

const { width } = Dimensions.get('window');

const COLORS = {
  bg: '#000000',
  surface: '#1A1A1A',
  card: '#2A2A2A',
  border: '#3E3E3E',
  text: '#ECECEC',
  textSecondary: '#8E8E8E',
  primary: '#5B6AFF',
  success: '#34C759',
  warning: '#FF9500',
  danger: '#EF4444',
  purple: '#A855F7',
  cyan: '#06B6D4',
  pink: '#EC4899',
};

// Circular Progress Component
const CircularProgress = ({
  percentage,
  size = 100,
  strokeWidth = 8,
  color = COLORS.primary,
  label,
  value,
  showPercentage = true,
}: {
  percentage: number;
  size?: number;
  strokeWidth?: number;
  color?: string;
  label?: string;
  value?: string;
  showPercentage?: boolean;
}) => {
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const strokeDashoffset = circumference - (percentage / 100) * circumference;

  return (
    <View style={{ alignItems: 'center' }}>
      <View style={{ width: size, height: size }}>
        <Svg width={size} height={size}>
          {/* Background circle */}
          <Circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke={COLORS.border}
            strokeWidth={strokeWidth}
            fill="none"
          />
          {/* Progress circle */}
          <Circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke={color}
            strokeWidth={strokeWidth}
            fill="none"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            transform={`rotate(-90 ${size / 2} ${size / 2})`}
          />
        </Svg>
        <View style={[styles.circularContent, { width: size, height: size }]}>
          {showPercentage ? (
            <Text style={[styles.circularValue, { color }]}>{Math.round(percentage)}%</Text>
          ) : value ? (
            <Text style={[styles.circularValue, { color, fontSize: size * 0.22 }]}>{value}</Text>
          ) : null}
        </View>
      </View>
      {label && <Text style={styles.circularLabel}>{label}</Text>}
    </View>
  );
};

// Weekly Bar Chart Component
const WeeklyChart = ({ data }: { data: number[] }) => {
  const maxValue = Math.max(...data, 1);
  const barWidth = (width - 80) / 7;
  const chartHeight = 120;
  const days = ['M', 'T', 'W', 'T', 'F', 'S', 'S'];

  return (
    <View style={styles.chartContainer}>
      <View style={styles.barsContainer}>
        {data.map((value, index) => {
          const barHeight = (value / maxValue) * (chartHeight - 20);
          const isToday = index === new Date().getDay() - 1 || (new Date().getDay() === 0 && index === 6);
          return (
            <View key={index} style={styles.barColumn}>
              <View style={[styles.barWrapper, { height: chartHeight - 20 }]}>
                <View
                  style={[
                    styles.bar,
                    {
                      height: Math.max(barHeight, 4),
                      backgroundColor: isToday ? COLORS.primary : value > 0 ? COLORS.success : COLORS.border,
                    },
                  ]}
                />
              </View>
              <Text style={[styles.barLabel, isToday && styles.barLabelActive]}>{days[index]}</Text>
            </View>
          );
        })}
      </View>
    </View>
  );
};

// Streak Display Component
const StreakDisplay = ({ streak, goal = 7 }: { streak: number; goal?: number }) => {
  const flames = [];
  for (let i = 0; i < goal; i++) {
    flames.push(
      <View key={i} style={styles.flameContainer}>
        <Text style={[styles.flame, i < streak ? styles.flameActive : styles.flameInactive]}>
          🔥
        </Text>
        {i < streak && <View style={styles.flameDot} />}
      </View>
    );
  }

  return (
    <View style={styles.streakContainer}>
      <View style={styles.streakHeader}>
        <Text style={styles.streakTitle}>Current Streak</Text>
        <Text style={styles.streakValue}>{streak} days</Text>
      </View>
      <View style={styles.flamesRow}>{flames}</View>
      {streak >= 3 && (
        <View style={styles.streakBadge}>
          <MaterialCommunityIcons name="trophy" size={16} color="#FFD700" />
          <Text style={styles.streakBadgeText}>
            {streak >= 7 ? 'Week Champion!' : streak >= 5 ? 'On Fire!' : 'Great Progress!'}
          </Text>
        </View>
      )}
    </View>
  );
};

// Achievement Badge Component
const AchievementBadge = ({
  icon,
  title,
  earned,
  color = COLORS.primary
}: {
  icon: string;
  title: string;
  earned: boolean;
  color?: string;
}) => (
  <View style={[styles.badge, earned && { borderColor: color }]}>
    <MaterialCommunityIcons
      name={icon as any}
      size={24}
      color={earned ? color : COLORS.border}
    />
    <Text style={[styles.badgeText, earned && { color: COLORS.text }]}>{title}</Text>
    {earned && (
      <MaterialCommunityIcons name="check-circle" size={14} color={COLORS.success} style={styles.badgeCheck} />
    )}
  </View>
);

export default function AnalyticsScreen() {
  const [activeTab, setActiveTab] = useState('overview');
  const [range, setRange] = useState('week');
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const fadeAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    loadData();
  }, [activeTab, range]);

  useEffect(() => {
    if (data) {
      fadeAnim.setValue(0);
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 300,
        useNativeDriver: true,
      }).start();
    }
  }, [data]);

  const loadData = async () => {
    try {
      setLoading(true);
      let response;

      switch (activeTab) {
        case 'overview':
          response = await analyticsAPI.getOverview(range);
          break;
        case 'time':
          response = await analyticsAPI.getTimeFocus(range);
          break;
        case 'tasks':
          response = await analyticsAPI.getTasksOutcomes(range);
          break;
        case 'milestones':
          response = await analyticsAPI.getMilestonesPath(range);
          break;
        case 'habits':
          response = await analyticsAPI.getHabitsQuality(range);
          break;
        case 'pulse':
          response = await analyticsAPI.getDailyPulse();
          break;
      }

      setData(response?.data);
    } catch (error) {
      console.error('Failed to load analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  // Helper function to safely display values
  const safeValue = (value: any, suffix: string = '') => {
    if (value === null || value === undefined || value === 'null') {
      return '0' + suffix;
    }
    return value + suffix;
  };

  // Get motivational message based on performance
  const getMotivationalMessage = () => {
    if (!data) return "Let's track your progress!";

    const completion = data.completion_rate || 0;
    const streak = data.streak_days || 0;

    if (streak >= 7) return "🏆 Incredible! You're a consistency champion!";
    if (streak >= 5) return "🔥 You're on fire! Keep the momentum!";
    if (completion >= 80) return "⭐ Outstanding performance this week!";
    if (completion >= 50) return "💪 Good progress! Push a little harder!";
    if (completion > 0) return "🌱 You've started - that's what matters!";
    return "🎯 Complete your first task to begin tracking!";
  };

  const renderOverview = () => {
    const focusMinutes = data?.focus_minutes_completed || 0;
    const focusBudget = data?.focus_minutes_budget || 0;
    const focusPercentage = focusBudget > 0 ? (focusMinutes / focusBudget) * 100 : 0;

    const milestoneDone = data?.milestone_critical_done || 0;
    const milestoneTotal = data?.milestone_critical_total || 0;
    const milestonePercentage = milestoneTotal > 0 ? (milestoneDone / milestoneTotal) * 100 : 0;

    const checkIns = data?.checkins_done || 0;
    const streak = data?.streak_days || 0;

    // Mock weekly data - in real app, this would come from API
    const weeklyTasks = data?.weekly_tasks || [3, 5, 4, 6, 2, 0, 0];

    return (
      <Animated.View style={{ opacity: fadeAnim }}>
        {/* Motivational Header */}
        <View style={styles.motivationalCard}>
          <Text style={styles.motivationalText}>{getMotivationalMessage()}</Text>
        </View>

        {/* Key Metrics */}
        <View style={styles.metricsRow}>
          <CircularProgress
            percentage={focusPercentage}
            size={100}
            color={COLORS.primary}
            label="Focus"
            showPercentage={true}
          />
          <CircularProgress
            percentage={milestonePercentage}
            size={100}
            color={COLORS.success}
            label="Milestones"
            showPercentage={true}
          />
          <CircularProgress
            percentage={Math.min((checkIns / 7) * 100, 100)}
            size={100}
            color={COLORS.purple}
            label="Check-ins"
            value={`${checkIns}/7`}
            showPercentage={false}
          />
        </View>

        {/* Weekly Activity Chart */}
        <Card title="Weekly Activity">
          <WeeklyChart data={weeklyTasks} />
        </Card>

        {/* Streak */}
        <Card title="">
          <StreakDisplay streak={streak} />
        </Card>

        {/* Best Performance */}
        <Card title="Best Performance">
          <View style={styles.bestPerformanceRow}>
            <View style={styles.bestPerformanceItem}>
              <MaterialCommunityIcons name="calendar-star" size={24} color={COLORS.warning} />
              <Text style={styles.bestLabel}>Best Day</Text>
              <Text style={styles.bestValue}>
                {data?.best_day || 'N/A'}
              </Text>
              <Text style={styles.bestSub}>
                {safeValue(data?.best_day_minutes, ' min')}
              </Text>
            </View>
            <View style={styles.bestDivider} />
            <View style={styles.bestPerformanceItem}>
              <MaterialCommunityIcons name="clock-star-four-points" size={24} color={COLORS.cyan} />
              <Text style={styles.bestLabel}>Best Hour</Text>
              <Text style={styles.bestValue}>
                {data?.best_hour || 'N/A'}
              </Text>
            </View>
          </View>
        </Card>

        {/* Achievements */}
        <Card title="Achievements">
          <View style={styles.badgesRow}>
            <AchievementBadge
              icon="flag-checkered"
              title="First Task"
              earned={(data?.total_completed || 0) > 0}
              color={COLORS.success}
            />
            <AchievementBadge
              icon="fire"
              title="3-Day Streak"
              earned={streak >= 3}
              color={COLORS.warning}
            />
            <AchievementBadge
              icon="trophy"
              title="Week Complete"
              earned={streak >= 7}
              color="#FFD700"
            />
          </View>
        </Card>

        {data?.insight && (
          <View style={styles.insightCard}>
            <MaterialCommunityIcons name="lightbulb-on" size={20} color="#FFD700" />
            <Text style={styles.insightText}>{data.insight}</Text>
          </View>
        )}
      </Animated.View>
    );
  };

  const renderTimeFocus = () => {
    const focusMinutes = data?.focus_minutes || 0;
    const budgetAdherence = data?.budget_adherence || 0;
    const deepWork = data?.time_breakdown?.deep_work || 0;
    const admin = data?.time_breakdown?.admin || 0;
    const other = data?.time_breakdown?.other || 0;
    const total = deepWork + admin + other;

    return (
      <Animated.View style={{ opacity: fadeAnim }}>
        <View style={styles.metricsRow}>
          <CircularProgress
            percentage={budgetAdherence}
            size={120}
            strokeWidth={10}
            color={budgetAdherence >= 80 ? COLORS.success : budgetAdherence >= 50 ? COLORS.warning : COLORS.danger}
            label="Budget Adherence"
          />
        </View>

        <Card title="Total Focus Time">
          <View style={styles.bigStatContainer}>
            <Text style={styles.bigStatValue}>{focusMinutes}</Text>
            <Text style={styles.bigStatLabel}>minutes</Text>
          </View>
        </Card>

        <Card title="Time Breakdown">
          {total > 0 ? (
            <>
              <StatRowWithBar
                label="Deep Work"
                value={`${deepWork} min`}
                percentage={(deepWork / total) * 100}
                color={COLORS.primary}
              />
              <StatRowWithBar
                label="Admin"
                value={`${admin} min`}
                percentage={(admin / total) * 100}
                color={COLORS.warning}
              />
              <StatRowWithBar
                label="Other"
                value={`${other} min`}
                percentage={(other / total) * 100}
                color={COLORS.textSecondary}
              />
            </>
          ) : (
            <EmptyState message="Complete tasks to see time breakdown" />
          )}
        </Card>
      </Animated.View>
    );
  };

  const renderTasksOutcomes = () => {
    const completed = data?.completed || 0;
    const skipped = data?.skipped || 0;
    const pending = data?.pending || 0;
    const total = completed + skipped + pending;
    const completionRate = total > 0 ? (completed / total) * 100 : 0;

    return (
      <Animated.View style={{ opacity: fadeAnim }}>
        <View style={styles.metricsRow}>
          <CircularProgress
            percentage={completionRate}
            size={120}
            strokeWidth={10}
            color={completionRate >= 80 ? COLORS.success : completionRate >= 50 ? COLORS.warning : COLORS.danger}
            label="Completion Rate"
          />
        </View>

        <Card title="Task Status">
          <View style={styles.statsGrid}>
            <StatBox label="Completed" value={completed} color={COLORS.success} icon="check-circle" />
            <StatBox label="Skipped" value={skipped} color={COLORS.warning} icon="skip-next-circle" />
            <StatBox label="Pending" value={pending} color={COLORS.textSecondary} icon="clock-outline" />
          </View>
        </Card>

        <Card title="By Source">
          <StatRowWithBar
            label="Plan Tasks"
            value={data?.by_source?.plan || 0}
            percentage={total > 0 ? ((data?.by_source?.plan || 0) / total) * 100 : 0}
            color={COLORS.primary}
          />
          <StatRowWithBar
            label="Ad Hoc Tasks"
            value={data?.by_source?.adhoc || 0}
            percentage={total > 0 ? ((data?.by_source?.adhoc || 0) / total) * 100 : 0}
            color={COLORS.purple}
          />
        </Card>

        <Card title="Priority Completion">
          {data?.by_priority?.length > 0 ? (
            data.by_priority.map((item: any, idx: number) => (
              <StatRowWithBar
                key={idx}
                label={item.priority}
                value={`${item.done} / ${item.total}`}
                percentage={item.total > 0 ? (item.done / item.total) * 100 : 0}
                color={item.priority === 'Critical' ? COLORS.danger : item.priority === 'High' ? COLORS.warning : COLORS.primary}
              />
            ))
          ) : (
            <EmptyState message="No priority data available" />
          )}
        </Card>
      </Animated.View>
    );
  };

  const renderMilestonesPath = () => (
    <Animated.View style={{ opacity: fadeAnim }}>
      <View style={styles.metricsRow}>
        <CircularProgress
          percentage={data?.on_time_rate || 0}
          size={100}
          color={COLORS.success}
          label="On-Time Rate"
        />
        <CircularProgress
          percentage={data?.path_confidence || 0}
          size={100}
          color={COLORS.primary}
          label="Path Confidence"
        />
      </View>

      <Card title="Milestones">
        {data?.milestones?.length > 0 ? (
          data.milestones.map((m: any) => (
            <View key={m.id} style={styles.milestoneItem}>
              <View style={[styles.milestoneIcon, m.is_completed && styles.milestoneIconCompleted]}>
                <MaterialCommunityIcons
                  name={m.is_completed ? 'check' : 'flag'}
                  size={16}
                  color={m.is_completed ? '#fff' : COLORS.textSecondary}
                />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={[styles.milestoneTitle, m.is_completed && styles.milestoneTitleCompleted]}>
                  {m.title}
                </Text>
                <Text style={styles.milestoneDate}>{m.due_date}</Text>
              </View>
              {m.is_completed && (
                <MaterialCommunityIcons name="check-circle" size={20} color={COLORS.success} />
              )}
            </View>
          ))
        ) : (
          <EmptyState message="No milestones set yet" icon="flag-outline" />
        )}
      </Card>
    </Animated.View>
  );

  const renderHabitsQuality = () => (
    <Animated.View style={{ opacity: fadeAnim }}>
      <Card title="">
        <StreakDisplay streak={data?.soft_streak || 0} goal={5} />
      </Card>

      <View style={styles.metricsRow}>
        <CircularProgress
          percentage={data?.checkin_rate || 0}
          size={90}
          color={COLORS.cyan}
          label="Check-in"
        />
        <CircularProgress
          percentage={data?.completion_rate || 0}
          size={90}
          color={COLORS.success}
          label="Completion"
        />
      </View>

      <Card title="Planning Quality">
        <StatRowWithBar
          label="Consistency"
          value={`${data?.planning_quality?.consistency || 0}%`}
          percentage={data?.planning_quality?.consistency || 0}
          color={COLORS.primary}
        />
        <StatRowWithBar
          label="Completion"
          value={`${data?.planning_quality?.completion || 0}%`}
          percentage={data?.planning_quality?.completion || 0}
          color={COLORS.success}
        />
      </Card>
    </Animated.View>
  );

  const renderDailyPulse = () => {
    if (!data) {
      return (
        <Card title="Today's Pulse">
          <EmptyState message="No pulse data available yet" icon="weather-sunny" />
        </Card>
      );
    }

    const getWorkloadColor = () => {
      switch (data.workload_status) {
        case 'light': return COLORS.success;
        case 'optimal': return COLORS.primary;
        case 'heavy': return COLORS.warning;
        case 'overloaded': return COLORS.danger;
        default: return COLORS.textSecondary;
      }
    };

    return (
      <Animated.View style={{ opacity: fadeAnim }}>
        <Card title="Today's Pulse">
          <View style={styles.pulseHeader}>
            <Text style={styles.greetingText}>{data.greeting_message}</Text>
          </View>
        </Card>

        <Card title="Workload">
          <View style={styles.workloadContainer}>
            <CircularProgress
              percentage={Math.min(data.workload_percentage || 0, 100)}
              size={100}
              strokeWidth={10}
              color={getWorkloadColor()}
              showPercentage={true}
            />
            <View style={styles.workloadInfo}>
              <Text style={[styles.workloadStatus, { color: getWorkloadColor() }]}>
                {(data.workload_status || 'unknown').charAt(0).toUpperCase() + (data.workload_status || 'unknown').slice(1)}
              </Text>
              <Text style={styles.workloadDetailsText}>
                {Math.floor((data.total_timebox_minutes || 0) / 60)}h {(data.total_timebox_minutes || 0) % 60}m scheduled
              </Text>
              <Text style={styles.workloadDetailsText}>
                {Math.floor((data.available_minutes || 0) / 60)}h {(data.available_minutes || 0) % 60}m available
              </Text>
            </View>
          </View>
        </Card>

        <Card title="Priorities">
          {data.top_priorities?.length > 0 ? (
            data.top_priorities.map((priority: any, index: number) => (
              <View key={index} style={styles.priorityItem}>
                <View style={[styles.priorityNumber, { backgroundColor: index === 0 ? COLORS.primary : COLORS.card }]}>
                  <Text style={styles.priorityNumberText}>{index + 1}</Text>
                </View>
                <View style={{ flex: 1 }}>
                  <Text style={styles.priorityTitle}>{priority.title}</Text>
                  <Text style={styles.priorityReason}>{priority.reason}</Text>
                  {priority.timebox_minutes && (
                    <Text style={styles.priorityTime}>⏱️ {priority.timebox_minutes} min</Text>
                  )}
                </View>
              </View>
            ))
          ) : (
            <EmptyState message="No priorities for today" icon="flag-outline" />
          )}
        </Card>

        {data.warnings?.length > 0 && (
          <Card title="⚠️ Warnings">
            {data.warnings.map((warning: any, index: number) => (
              <View key={index} style={styles.warningItem}>
                <MaterialCommunityIcons
                  name={warning.severity === 'high' ? 'alert' : 'information'}
                  size={20}
                  color={warning.severity === 'high' ? COLORS.danger : COLORS.warning}
                />
                <Text style={styles.warningText}>{warning.message}</Text>
              </View>
            ))}
          </Card>
        )}

        {data.smart_suggestions?.length > 0 && (
          <Card title="💡 Smart Suggestions">
            {data.smart_suggestions.map((suggestion: any, index: number) => (
              <View key={index} style={styles.suggestionItem}>
                <MaterialCommunityIcons name="lightbulb-on" size={20} color="#FFD700" />
                <Text style={styles.suggestionText}>{suggestion.message || suggestion}</Text>
              </View>
            ))}
          </Card>
        )}

        {data.weekly_progress && (
          <Card title="Weekly Progress">
            <CircularProgress
              percentage={data.weekly_progress.completion_rate || 0}
              size={80}
              color={COLORS.success}
              label={`${data.weekly_progress.completed_tasks || 0}/${data.weekly_progress.total_tasks || 0} tasks`}
            />
            {(data.weekly_progress.overdue_tasks || 0) > 0 && (
              <View style={styles.overdueWarning}>
                <MaterialCommunityIcons name="alert" size={16} color={COLORS.danger} />
                <Text style={styles.overdueText}>
                  {data.weekly_progress.overdue_tasks} overdue tasks
                </Text>
              </View>
            )}
          </Card>
        )}
      </Animated.View>
    );
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Analytics</Text>
      </View>

      {/* Date Range Picker */}
      <View style={styles.rangeContainer}>
        {['week', 'last_week', '30days'].map((r) => (
          <TouchableOpacity
            key={r}
            style={[styles.rangeButton, range === r && styles.rangeButtonActive]}
            onPress={() => setRange(r)}
          >
            <Text style={[styles.rangeText, range === r && styles.rangeTextActive]}>
              {r === 'week' ? 'This Week' : r === 'last_week' ? 'Last Week' : '30 Days'}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Tabs */}
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        style={styles.tabsContainer}
      >
        {[
          { key: 'overview', label: 'Overview', icon: 'view-dashboard' },
          { key: 'pulse', label: 'Daily Pulse', icon: 'white-balance-sunny' },
          { key: 'time', label: 'Time & Focus', icon: 'clock-outline' },
          { key: 'tasks', label: 'Tasks', icon: 'check-circle-outline' },
          { key: 'milestones', label: 'Milestones', icon: 'flag-outline' },
          { key: 'habits', label: 'Habits', icon: 'chart-line' },
        ].map((tab) => (
          <TouchableOpacity
            key={tab.key}
            style={[styles.tab, activeTab === tab.key && styles.tabActive]}
            onPress={() => setActiveTab(tab.key)}
          >
            <MaterialCommunityIcons
              name={tab.icon as any}
              size={20}
              color={activeTab === tab.key ? COLORS.primary : COLORS.textSecondary}
            />
            <Text style={[styles.tabText, activeTab === tab.key && styles.tabTextActive]}>
              {tab.label}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      {/* Content */}
      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        {loading ? (
          <View style={styles.loadingContainer}>
            <MaterialCommunityIcons name="loading" size={32} color={COLORS.primary} />
            <Text style={styles.loadingText}>Loading analytics...</Text>
          </View>
        ) : data ? (
          <>
            {activeTab === 'overview' && renderOverview()}
            {activeTab === 'pulse' && renderDailyPulse()}
            {activeTab === 'time' && renderTimeFocus()}
            {activeTab === 'tasks' && renderTasksOutcomes()}
            {activeTab === 'milestones' && renderMilestonesPath()}
            {activeTab === 'habits' && renderHabitsQuality()}
          </>
        ) : (
          <EmptyState message="No data available" icon="chart-bar" />
        )}
        <View style={{ height: 100 }} />
      </ScrollView>
    </View>
  );
}

// Card Component
const Card = ({ title, children }: { title: string; children: React.ReactNode }) => (
  <View style={styles.card}>
    {title ? <Text style={styles.cardTitle}>{title}</Text> : null}
    {children}
  </View>
);

// Stat Row with Progress Bar
const StatRowWithBar = ({
  label,
  value,
  percentage,
  color = COLORS.primary
}: {
  label: string;
  value: string | number;
  percentage: number;
  color?: string;
}) => (
  <View style={styles.statRow}>
    <View style={styles.statRowHeader}>
      <Text style={styles.statLabel}>{label}</Text>
      <Text style={styles.statValue}>{value}</Text>
    </View>
    <View style={styles.progressBar}>
      <View style={[styles.progressFill, { width: `${Math.min(percentage, 100)}%`, backgroundColor: color }]} />
    </View>
  </View>
);

// Stat Box with Icon
const StatBox = ({
  label,
  value,
  color,
  icon
}: {
  label: string;
  value: number;
  color: string;
  icon: string;
}) => (
  <View style={styles.statBox}>
    <MaterialCommunityIcons name={icon as any} size={24} color={color} />
    <Text style={[styles.statBoxValue, { color }]}>{value}</Text>
    <Text style={styles.statBoxLabel}>{label}</Text>
  </View>
);

// Empty State Component
const EmptyState = ({ message, icon = 'chart-bar' }: { message: string; icon?: string }) => (
  <View style={styles.emptyStateContainer}>
    <MaterialCommunityIcons name={icon as any} size={48} color={COLORS.border} />
    <Text style={styles.emptyStateText}>{message}</Text>
  </View>
);

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.bg,
  },
  header: {
    padding: 16,
    paddingTop: 60,
    backgroundColor: COLORS.surface,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: COLORS.text,
  },
  rangeContainer: {
    flexDirection: 'row',
    padding: 12,
    gap: 8,
    backgroundColor: COLORS.bg,
  },
  rangeButton: {
    flex: 1,
    paddingVertical: 10,
    paddingHorizontal: 12,
    borderRadius: 8,
    backgroundColor: COLORS.card,
    borderWidth: 1,
    borderColor: COLORS.border,
    alignItems: 'center',
  },
  rangeButtonActive: {
    backgroundColor: COLORS.primary,
    borderColor: COLORS.primary,
  },
  rangeText: {
    fontSize: 13,
    color: COLORS.textSecondary,
    fontWeight: '600',
  },
  rangeTextActive: {
    color: '#fff',
  },
  tabsContainer: {
    maxHeight: 60,
    backgroundColor: COLORS.bg,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  tab: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 2,
    borderBottomColor: 'transparent',
  },
  tabActive: {
    borderBottomColor: COLORS.primary,
  },
  tabText: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.textSecondary,
  },
  tabTextActive: {
    color: COLORS.primary,
  },
  content: {
    flex: 1,
    padding: 16,
  },
  card: {
    backgroundColor: COLORS.card,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 16,
    padding: 16,
    marginBottom: 16,
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: COLORS.text,
    marginBottom: 16,
  },
  // Motivational Card
  motivationalCard: {
    backgroundColor: 'rgba(91, 106, 255, 0.15)',
    borderWidth: 1,
    borderColor: 'rgba(91, 106, 255, 0.3)',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
  },
  motivationalText: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
    textAlign: 'center',
  },
  // Metrics Row
  metricsRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    alignItems: 'flex-start',
    marginBottom: 16,
    paddingVertical: 8,
  },
  // Circular Progress
  circularContent: {
    position: 'absolute',
    justifyContent: 'center',
    alignItems: 'center',
  },
  circularValue: {
    fontSize: 18,
    fontWeight: 'bold',
  },
  circularLabel: {
    fontSize: 12,
    color: COLORS.textSecondary,
    marginTop: 8,
    fontWeight: '500',
  },
  // Chart
  chartContainer: {
    paddingVertical: 8,
  },
  barsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-end',
  },
  barColumn: {
    alignItems: 'center',
    flex: 1,
  },
  barWrapper: {
    justifyContent: 'flex-end',
    width: '80%',
  },
  bar: {
    width: '100%',
    borderRadius: 4,
    minHeight: 4,
  },
  barLabel: {
    fontSize: 11,
    color: COLORS.textSecondary,
    marginTop: 6,
    fontWeight: '500',
  },
  barLabelActive: {
    color: COLORS.primary,
    fontWeight: '700',
  },
  // Streak
  streakContainer: {
    alignItems: 'center',
  },
  streakHeader: {
    alignItems: 'center',
    marginBottom: 12,
  },
  streakTitle: {
    fontSize: 14,
    color: COLORS.textSecondary,
    marginBottom: 4,
  },
  streakValue: {
    fontSize: 28,
    fontWeight: 'bold',
    color: COLORS.text,
  },
  flamesRow: {
    flexDirection: 'row',
    gap: 8,
  },
  flameContainer: {
    alignItems: 'center',
  },
  flame: {
    fontSize: 24,
  },
  flameActive: {
    opacity: 1,
  },
  flameInactive: {
    opacity: 0.2,
  },
  flameDot: {
    width: 4,
    height: 4,
    borderRadius: 2,
    backgroundColor: COLORS.warning,
    marginTop: 4,
  },
  streakBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: 'rgba(255, 215, 0, 0.15)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
    marginTop: 12,
  },
  streakBadgeText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#FFD700',
  },
  // Best Performance
  bestPerformanceRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  bestPerformanceItem: {
    flex: 1,
    alignItems: 'center',
    gap: 8,
  },
  bestDivider: {
    width: 1,
    height: 60,
    backgroundColor: COLORS.border,
    marginHorizontal: 16,
  },
  bestLabel: {
    fontSize: 12,
    color: COLORS.textSecondary,
  },
  bestValue: {
    fontSize: 18,
    fontWeight: 'bold',
    color: COLORS.text,
  },
  bestSub: {
    fontSize: 12,
    color: COLORS.textSecondary,
  },
  // Badges
  badgesRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 8,
  },
  badge: {
    flex: 1,
    alignItems: 'center',
    padding: 12,
    backgroundColor: COLORS.surface,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: COLORS.border,
    position: 'relative',
  },
  badgeText: {
    fontSize: 10,
    color: COLORS.textSecondary,
    marginTop: 6,
    textAlign: 'center',
  },
  badgeCheck: {
    position: 'absolute',
    top: 4,
    right: 4,
  },
  // Stat Row
  statRow: {
    marginBottom: 16,
  },
  statRowHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 6,
  },
  statLabel: {
    fontSize: 14,
    color: COLORS.textSecondary,
  },
  statValue: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.text,
  },
  progressBar: {
    height: 6,
    backgroundColor: COLORS.border,
    borderRadius: 3,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    borderRadius: 3,
  },
  // Stat Box
  statsGrid: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 12,
  },
  statBox: {
    flex: 1,
    alignItems: 'center',
    padding: 12,
    backgroundColor: COLORS.surface,
    borderRadius: 12,
    gap: 4,
  },
  statBoxValue: {
    fontSize: 24,
    fontWeight: 'bold',
  },
  statBoxLabel: {
    fontSize: 11,
    color: COLORS.textSecondary,
  },
  // Big Stat
  bigStatContainer: {
    alignItems: 'center',
    paddingVertical: 16,
  },
  bigStatValue: {
    fontSize: 48,
    fontWeight: 'bold',
    color: COLORS.primary,
  },
  bigStatLabel: {
    fontSize: 14,
    color: COLORS.textSecondary,
    marginTop: 4,
  },
  // Insight Card
  insightCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    backgroundColor: 'rgba(255, 215, 0, 0.1)',
    borderWidth: 1,
    borderColor: 'rgba(255, 215, 0, 0.3)',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
  },
  insightText: {
    flex: 1,
    fontSize: 14,
    color: '#FFD700',
    fontWeight: '500',
  },
  // Milestone
  milestoneItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  milestoneIcon: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: COLORS.surface,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  milestoneIconCompleted: {
    backgroundColor: COLORS.success,
  },
  milestoneTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.text,
  },
  milestoneTitleCompleted: {
    textDecorationLine: 'line-through',
    color: COLORS.textSecondary,
  },
  milestoneDate: {
    fontSize: 12,
    color: COLORS.textSecondary,
    marginTop: 2,
  },
  // Loading
  loadingContainer: {
    alignItems: 'center',
    paddingTop: 60,
    gap: 12,
  },
  loadingText: {
    textAlign: 'center',
    color: COLORS.textSecondary,
    fontSize: 14,
  },
  // Empty State
  emptyStateContainer: {
    alignItems: 'center',
    paddingVertical: 32,
    gap: 12,
  },
  emptyStateText: {
    textAlign: 'center',
    color: COLORS.textSecondary,
    fontSize: 14,
  },
  // Daily Pulse Styles
  pulseHeader: {
    marginBottom: 8,
  },
  greetingText: {
    fontSize: 16,
    color: COLORS.text,
    lineHeight: 24,
  },
  priorityItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 16,
    paddingBottom: 16,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  priorityNumber: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: COLORS.primary,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  priorityNumberText: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#FFFFFF',
  },
  priorityTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: 4,
  },
  priorityReason: {
    fontSize: 13,
    color: COLORS.textSecondary,
    marginBottom: 4,
  },
  priorityTime: {
    fontSize: 12,
    color: COLORS.primary,
  },
  workloadContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 20,
  },
  workloadInfo: {
    flex: 1,
    gap: 4,
  },
  workloadStatus: {
    fontSize: 18,
    fontWeight: 'bold',
    textTransform: 'capitalize',
    marginBottom: 4,
  },
  workloadDetailsText: {
    fontSize: 13,
    color: COLORS.textSecondary,
  },
  warningItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 12,
    marginBottom: 12,
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  warningText: {
    flex: 1,
    fontSize: 14,
    color: COLORS.text,
    lineHeight: 20,
  },
  suggestionItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 12,
    marginBottom: 12,
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  suggestionText: {
    flex: 1,
    fontSize: 14,
    color: COLORS.text,
    lineHeight: 20,
  },
  overdueWarning: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    marginTop: 12,
    padding: 8,
    backgroundColor: 'rgba(239, 68, 68, 0.1)',
    borderRadius: 8,
  },
  overdueText: {
    fontSize: 13,
    color: COLORS.danger,
    fontWeight: '500',
  },
});
