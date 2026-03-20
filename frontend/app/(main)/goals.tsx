import { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
  TouchableOpacity,
} from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { goalSpecAPI } from '@/services/api';
import { useTranslation } from 'react-i18next';
import { useRouter } from 'expo-router';
import Svg, { Circle } from 'react-native-svg';
import { colors, spacing, borderRadius } from '@/theme';

// Circular Progress Component
const CircularProgress = ({ progress, size = 80, strokeWidth = 8 }: { progress: number; size?: number; strokeWidth?: number }) => {
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const strokeDashoffset = circumference - (progress / 100) * circumference;

  return (
    <View style={{ width: size, height: size, alignItems: 'center', justifyContent: 'center' }}>
      <Svg width={size} height={size} style={{ transform: [{ rotate: '-90deg' }] }}>
        {/* Background Circle */}
        <Circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={colors.border}
          strokeWidth={strokeWidth}
          fill="none"
        />
        {/* Progress Circle */}
        <Circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={colors.primary}
          strokeWidth={strokeWidth}
          fill="none"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
        />
      </Svg>
      <View style={{ position: 'absolute', alignItems: 'center', justifyContent: 'center' }}>
        <Text style={{ fontSize: 18, fontWeight: 'bold', color: colors.text }}>{progress}%</Text>
      </View>
    </View>
  );
};

export default function GoalsScreen() {
  const { t } = useTranslation();
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [goalsData, setGoalsData] = useState<any>(null);

  useEffect(() => {
    loadGoalsData();
  }, []);

  const loadGoalsData = async () => {
    try {
      setLoading(true);
      const response = await goalSpecAPI.withMilestones();
      console.log('GoalSpec with Milestones:', response.data);
      setGoalsData(response.data);
    } catch (error: any) {
      console.error('Failed to load goals:', error);
      setGoalsData(null);
    } finally {
      setLoading(false);
    }
  };

  const handleGoalPress = (goal: any) => {
    // Navigate to goal-specific tasks screen (stays in Goals tab context)
    router.push(`/goal-tasks/${goal.id}` as any);
  };

  const getCategoryDisplayName = (category: string) => {
    const names: Record<string, string> = {
      'study': 'Study',
      'career': 'Career',
      'sport': 'Sport',
      'finance': 'Finance',
      'language': 'Language',
      'health': 'Health',
      'creative': 'Creative',
      'admin': 'Admin',
      'research': 'Research',
      'networking': 'Networking',
      'travel': 'Travel',
      'other': 'Other',
    };
    return names[category] || category;
  };

  const getCategoryIcon = (category: string) => {
    const icons: Record<string, string> = {
      'study': 'school',
      'career': 'briefcase',
      'sport': 'dumbbell',
      'finance': 'cash',
      'language': 'translate',
      'health': 'heart-pulse',
      'creative': 'palette',
      'admin': 'file-document',
      'research': 'flask',
      'networking': 'account-group',
      'travel': 'airplane',
      'other': 'star',
    };
    return icons[category] || 'star';
  };

  const getGoalStatusColor = (status: string) => {
    switch (status) {
      case 'on_track':
        return colors.primary;
      case 'at_risk':
        return colors.warning;
      case 'stalled':
        return colors.error;
      default:
        return colors.textSecondary;
    }
  };

  const getGoalStatusLabel = (status: string) => {
    switch (status) {
      case 'on_track':
        return 'On track';
      case 'at_risk':
        return 'At risk';
      case 'stalled':
        return 'Stalled';
      default:
        return 'Unknown';
    }
  };

  // Show empty state if no goals
  if (!goalsData || goalsData.total_goals === 0) {
    return (
      <View style={styles.container}>
        <View style={styles.header}>
          <Text style={styles.logo}>Goals</Text>
        </View>
        <View style={styles.emptyContainer}>
          <MaterialCommunityIcons name="target" size={64} color={colors.border} />
          <Text style={styles.emptyText}>No goals created yet</Text>
          <Text style={styles.emptySubtext}>
            Chat with your AI coach to create your first goal
          </Text>
        </View>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.logo}>Goals</Text>
      </View>

      <ScrollView
        style={styles.content}
        showsVerticalScrollIndicator={false}
        refreshControl={<RefreshControl refreshing={loading} onRefresh={loadGoalsData} />}
      >
        {/* Goals with milestones */}
        {goalsData.goals && goalsData.goals.map((goal: any) => (
          <View key={goal.id} style={styles.goalCard}>
            <TouchableOpacity
              onPress={() => handleGoalPress(goal)}
              activeOpacity={0.7}
              style={styles.goalCardContent}
            >
              {/* Goal Header */}
              <View style={styles.goalHeader}>
                <MaterialCommunityIcons
                  name={getCategoryIcon(goal.category) as any}
                  size={20}
                  color={colors.primary}
                />
                <Text style={styles.goalTitle} numberOfLines={2}>
                  {goal.title}
                </Text>
                {goal.total_tasks > 0 && (
                  <View style={styles.tasksBadge}>
                    <MaterialCommunityIcons name="checkbox-marked" size={12} color={colors.primary} />
                    <Text style={styles.tasksBadgeText}>
                      {goal.completed_tasks}/{goal.total_tasks}
                    </Text>
                  </View>
                )}
              </View>

              {goal.description && (
                <Text style={styles.goalDescription} numberOfLines={2}>
                  {goal.description}
                </Text>
              )}

              {/* Circular Progress */}
              <View style={styles.circularProgressContainer}>
                <CircularProgress progress={goal.progress} size={80} strokeWidth={8} />
              </View>
            </TouchableOpacity>

            {/* Milestones */}
            {goal.milestones && goal.milestones.length > 0 && (
              <View style={styles.milestonesSection}>
                <Text style={styles.milestonesHeader}>Milestones</Text>
                {goal.milestones.map((milestone: any, index: number) => (
                  <View key={index} style={styles.milestoneCard}>
                    <View style={styles.milestoneHeader}>
                      <View style={styles.milestoneIndexBadge}>
                        <Text style={styles.milestoneIndexText}>{milestone.index}</Text>
                      </View>
                      <Text style={styles.milestoneTitle} numberOfLines={2}>
                        {milestone.title}
                      </Text>
                    </View>

                    {/* Milestone Progress */}
                    <View style={styles.milestoneProgress}>
                      <View style={styles.milestoneProgressBar}>
                        <View
                          style={[
                            styles.milestoneProgressFill,
                            {
                              width: `${milestone.progress}%`,
                              backgroundColor: milestone.progress >= 70 ? colors.primary : milestone.progress >= 30 ? colors.warning : colors.error,
                            },
                          ]}
                        />
                      </View>
                      <Text style={styles.milestoneProgressText}>
                        {milestone.completed_tasks}/{milestone.total_tasks} ({milestone.progress}%)
                      </Text>
                    </View>
                  </View>
                ))}
              </View>
            )}

          </View>
        ))}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.bg,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: spacing.lg,
    paddingTop: 60,
    paddingBottom: spacing.md,
    backgroundColor: colors.bg,
  },
  logo: {
    fontSize: 24,
    fontWeight: 'bold',
    color: colors.text,
  },
  addButton: {
    padding: spacing.sm,
  },
  content: {
    flex: 1,
  },
  categorySection: {
    marginBottom: spacing.lg,
  },
  categoryHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    gap: spacing.sm,
  },
  categoryTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: colors.text,
    flex: 1,
  },
  categoryBadge: {
    backgroundColor: colors.surface,
    paddingHorizontal: spacing.sm,
    paddingVertical: 4,
    borderRadius: borderRadius.md,
    borderWidth: 1,
    borderColor: colors.border,
  },
  categoryBadgeText: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.primary,
  },
  goalCard: {
    backgroundColor: colors.surface,
    marginHorizontal: spacing.md,
    marginBottom: spacing.sm,
    borderRadius: borderRadius.md,
    borderWidth: 1,
    borderColor: colors.border,
    overflow: 'hidden',
  },
  goalCardContent: {
    padding: spacing.md,
  },
  goalHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: spacing.sm,
  },
  goalTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.text,
    flex: 1,
    marginRight: spacing.sm,
  },
  goalDescription: {
    fontSize: 14,
    color: colors.textSecondary,
    marginBottom: spacing.sm,
    lineHeight: 20,
  },
  circularProgressContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: spacing.sm,
  },
  tasksBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: `${colors.primary}1A`,
    paddingHorizontal: spacing.sm,
    paddingVertical: 4,
    borderRadius: borderRadius.md,
  },
  tasksBadgeText: {
    fontSize: 12,
    fontWeight: '600',
    color: colors.primary,
  },
  progressContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    marginBottom: spacing.sm,
  },
  progressBar: {
    flex: 1,
    height: 6,
    backgroundColor: colors.border,
    borderRadius: 3,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    backgroundColor: colors.primary,
    borderRadius: 3,
  },
  progressText: {
    fontSize: 12,
    fontWeight: '600',
    color: colors.textSecondary,
    minWidth: 38,
    textAlign: 'right',
  },
  goalFooter: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  statusLabel: {
    fontSize: 12,
    fontWeight: '600',
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: spacing.lg,
  },
  emptyText: {
    fontSize: 18,
    fontWeight: '600',
    color: colors.textSecondary,
    marginTop: spacing.md,
    marginBottom: spacing.sm,
  },
  emptySubtext: {
    fontSize: 14,
    color: colors.textSecondary,
    textAlign: 'center',
  },
  generateButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    marginTop: spacing.sm,
    paddingVertical: 10,
    paddingHorizontal: spacing.md,
    backgroundColor: `${colors.primary}1A`,
    borderWidth: 1,
    borderColor: colors.primary,
    borderRadius: borderRadius.sm,
  },
  generateButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.primary,
  },
  milestonesSection: {
    paddingTop: spacing.md,
    paddingHorizontal: spacing.md,
    paddingBottom: spacing.sm,
    borderTopWidth: 1,
    borderTopColor: colors.border,
  },
  milestonesHeader: {
    fontSize: 14,
    fontWeight: '700',
    color: colors.text,
    marginBottom: spacing.sm,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  milestoneCard: {
    backgroundColor: `${colors.surface}80`,
    padding: spacing.sm,
    borderRadius: borderRadius.sm,
    marginBottom: spacing.sm,
    borderWidth: 1,
    borderColor: colors.border,
  },
  milestoneHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    marginBottom: 10,
  },
  milestoneIndexBadge: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  milestoneIndexText: {
    fontSize: 12,
    fontWeight: 'bold',
    color: colors.bg,
  },
  milestoneTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.text,
    flex: 1,
  },
  milestoneProgress: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
  },
  milestoneProgressBar: {
    flex: 1,
    height: 4,
    backgroundColor: colors.border,
    borderRadius: 2,
    overflow: 'hidden',
  },
  milestoneProgressFill: {
    height: '100%',
    borderRadius: 2,
  },
  milestoneProgressText: {
    fontSize: 11,
    fontWeight: '600',
    color: colors.textSecondary,
    minWidth: 80,
    textAlign: 'right',
  },
});
