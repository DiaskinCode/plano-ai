/**
 * ProgressCard Component
 *
 * Displays user progress statistics:
 * - Overall progress percentage
 * - Category breakdown
 * - Streak information
 * - Recent activity
 */

import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, ActivityIndicator } from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { authAPI } from '@/services/api';

interface ProgressData {
  overall: {
    total_tasks: number;
    completed_tasks: number;
    remaining_tasks: number;
    progress_percentage: number;
  };
  streak: {
    current_streak: number;
    longest_streak: number;
    total_days_active: number;
  };
  timeline: {
    completed_this_week: number;
    completed_this_month: number;
    upcoming_tasks: number;
    overdue_tasks: number;
  };
}

interface ProgressCardProps {
  style?: any;
}

export const ProgressCard: React.FC<ProgressCardProps> = ({ style }) => {
  const [progress, setProgress] = useState<ProgressData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadProgress();
  }, []);

  const loadProgress = async () => {
    try {
      const response = await authAPI.getProgress();
      setProgress(response.data);
    } catch (error) {
      console.error('Failed to load progress:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <View style={[styles.container, style]}>
        <ActivityIndicator size="small" color="#3B82F6" />
      </View>
    );
  }

  if (!progress) {
    return null;
  }

  return (
    <View style={[styles.container, style]}>
      {/* Overall Progress */}
      <View style={styles.progressHeader}>
        <View style={styles.progressCircle}>
          <Text style={styles.progressPercentage}>
            {progress.overall.progress_percentage}%
          </Text>
          <Text style={styles.progressLabel}>Complete</Text>
        </View>
        <View style={styles.progressDetails}>
          <View style={styles.progressRow}>
            <Text style={styles.progressNumber}>{progress.overall.completed_tasks}</Text>
            <Text style={styles.progressText}>completed</Text>
          </View>
          <View style={styles.progressRow}>
            <Text style={styles.progressNumber}>{progress.overall.remaining_tasks}</Text>
            <Text style={styles.progressText}>remaining</Text>
          </View>
        </View>
      </View>

      {/* Streak */}
      <View style={styles.streakRow}>
        <MaterialCommunityIcons name="fire" size={24} color="#F59E0B" />
        <View style={styles.streakInfo}>
          <Text style={styles.streakCount}>{progress.streak.current_streak} day streak</Text>
          <Text style={styles.streakSubtext}>Best: {progress.streak.longest_streak} days</Text>
        </View>
      </View>

      {/* Activity Stats */}
      <View style={styles.activityRow}>
        <View style={styles.activityItem}>
          <Text style={styles.activityNumber}>{progress.timeline.completed_this_week}</Text>
          <Text style={styles.activityLabel}>This week</Text>
        </View>
        <View style={styles.activityItem}>
          <Text style={styles.activityNumber}>{progress.timeline.completed_this_month}</Text>
          <Text style={styles.activityLabel}>This month</Text>
        </View>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#1E1E1E',
    borderRadius: 12,
    padding: 16,
  },
  progressHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  progressCircle: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: '#3B82F6',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 16,
  },
  progressPercentage: {
    fontSize: 24,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  progressLabel: {
    fontSize: 10,
    color: 'rgba(255, 255, 255, 0.8)',
  },
  progressDetails: {
    flex: 1,
  },
  progressRow: {
    flexDirection: 'row',
    alignItems: 'baseline',
    marginBottom: 4,
  },
  progressNumber: {
    fontSize: 20,
    fontWeight: '700',
    color: '#ECECEC',
    marginRight: 8,
  },
  progressText: {
    fontSize: 14,
    color: '#8E8E8E',
  },
  streakRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#2A2A2A',
    borderRadius: 8,
    padding: 12,
    marginBottom: 12,
  },
  streakInfo: {
    flex: 1,
    marginLeft: 12,
  },
  streakCount: {
    fontSize: 14,
    fontWeight: '600',
    color: '#ECECEC',
  },
  streakSubtext: {
    fontSize: 12,
    color: '#8E8E8E',
    marginTop: 2,
  },
  activityRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  activityItem: {
    alignItems: 'center',
  },
  activityNumber: {
    fontSize: 18,
    fontWeight: '700',
    color: '#10B981',
  },
  activityLabel: {
    fontSize: 12,
    color: '#8E8E8E',
    marginTop: 2,
  },
});
