import { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ActivityIndicator } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { BlurView } from 'expo-blur';
import { useRouter } from 'expo-router';
import { weeklyReviewAPI } from '@/services/api';

interface WeeklyReportBannerProps {
  onPress?: () => void;
}

export default function WeeklyReportBanner({ onPress }: WeeklyReportBannerProps) {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [reportData, setReportData] = useState<any>(null);

  useEffect(() => {
    loadWeeklyReport();
  }, []);

  const loadWeeklyReport = async () => {
    try {
      setLoading(true);
      // Get last Monday
      const today = new Date();
      const dayOfWeek = today.getDay();
      const diff = today.getDate() - dayOfWeek + (dayOfWeek === 0 ? -6 : 1);
      const monday = new Date(today.setDate(diff));
      const weekStart = monday.toISOString().split('T')[0];

      const response = await weeklyReviewAPI.statsOnly(weekStart);
      setReportData(response.data);
    } catch (error: any) {
      console.error('Failed to load weekly report:', error);
      console.error('Error details:', error.response?.data);
    } finally {
      setLoading(false);
    }
  };

  if (loading || !reportData) {
    return (
      <View style={styles.container}>
        <LinearGradient
          colors={['rgba(91, 106, 255, 0.15)', 'rgba(91, 106, 255, 0.05)']}
          style={styles.gradient}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
        >
          <BlurView intensity={20} tint="dark" style={styles.blur}>
            <View style={styles.loadingContainer}>
              <ActivityIndicator size="small" color="#5B6AFF" />
              <Text style={styles.loadingText}>Loading your week...</Text>
            </View>
          </BlurView>
        </LinearGradient>
      </View>
    );
  }

  const { stats, streaks } = reportData;

  const handlePress = () => {
    if (onPress) {
      onPress();
    } else {
      router.push('/(main)/weekly-review');
    }
  };

  return (
    <TouchableOpacity
      style={styles.container}
      onPress={handlePress}
      activeOpacity={0.9}
    >
      <LinearGradient
        colors={['rgba(91, 106, 255, 0.2)', 'rgba(91, 106, 255, 0.1)', 'rgba(91, 106, 255, 0.05)']}
        style={styles.gradient}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
      >
        <BlurView intensity={30} tint="dark" style={styles.blur}>
          {/* Header */}
          <View style={styles.header}>
            <View style={styles.headerLeft}>
              <MaterialCommunityIcons name="chart-line" size={20} color="#5B6AFF" />
              <Text style={styles.title}>Your Weekly Report</Text>
            </View>
            <MaterialCommunityIcons name="chevron-right" size={20} color="#8E8E8E" />
          </View>

          {/* Stats Row */}
          <View style={styles.statsRow}>
            {/* Completion Rate */}
            <View style={styles.statItem}>
              <View style={styles.statIconContainer}>
                <MaterialCommunityIcons name="check-circle" size={24} color="#34C759" />
              </View>
              <Text style={styles.statValue}>{stats?.completion_rate || 0}%</Text>
              <Text style={styles.statLabel}>Success</Text>
            </View>

            {/* Divider */}
            <View style={styles.divider} />

            {/* Tasks Completed */}
            <View style={styles.statItem}>
              <View style={styles.statIconContainer}>
                <MaterialCommunityIcons name="checkbox-marked-circle-outline" size={24} color="#007AFF" />
              </View>
              <Text style={styles.statValue}>{stats?.completed || 0}</Text>
              <Text style={styles.statLabel}>Completed</Text>
            </View>

            {/* Divider */}
            <View style={styles.divider} />

            {/* Streak */}
            <View style={styles.statItem}>
              <View style={styles.statIconContainer}>
                <Text style={styles.streakEmoji}>🔥</Text>
              </View>
              <Text style={styles.statValue}>{streaks?.current_streak || 0}</Text>
              <Text style={styles.statLabel}>Day Streak</Text>
            </View>
          </View>

          {/* Progress Bar */}
          {stats?.total_tasks > 0 && (
            <View style={styles.progressContainer}>
              <View style={styles.progressBar}>
                <View
                  style={[
                    styles.progressFill,
                    { width: `${stats.completion_rate}%` }
                  ]}
                />
              </View>
              <Text style={styles.progressText}>
                {stats.completed}/{stats.total_tasks} tasks this week
              </Text>
            </View>
          )}

          {/* Footer Badge */}
          <View style={styles.footer}>
            <View style={styles.badge}>
              <MaterialCommunityIcons name="trophy" size={14} color="#FFD700" />
              <Text style={styles.badgeText}>
                {stats?.total_hours > 0 ? `${stats.total_hours}h invested` : 'Keep building!'}
              </Text>
            </View>
          </View>
        </BlurView>
      </LinearGradient>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  container: {
    margin: 16,
    marginTop: 8,
    borderRadius: 20,
    overflow: 'hidden',
    position: 'relative',
  },
  gradient: {
    borderRadius: 20,
    padding: 1,
  },
  blur: {
    borderRadius: 20,
    padding: 20,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
    backgroundColor: 'rgba(26, 26, 26, 0.6)',
  },
  loadingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 12,
    paddingVertical: 20,
  },
  loadingText: {
    fontSize: 14,
    color: '#8E8E8E',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  title: {
    fontSize: 16,
    fontWeight: '600',
    color: '#ECECEC',
  },
  statsRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    alignItems: 'center',
    marginBottom: 16,
  },
  statItem: {
    alignItems: 'center',
    flex: 1,
  },
  statIconContainer: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 8,
  },
  streakEmoji: {
    fontSize: 24,
  },
  statValue: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#ECECEC',
    marginBottom: 4,
  },
  statLabel: {
    fontSize: 11,
    color: '#8E8E8E',
    fontWeight: '500',
  },
  divider: {
    width: 1,
    height: 40,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
  },
  progressContainer: {
    marginBottom: 12,
  },
  progressBar: {
    height: 6,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 3,
    overflow: 'hidden',
    marginBottom: 8,
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#5B6AFF',
    borderRadius: 3,
  },
  progressText: {
    fontSize: 12,
    color: '#8E8E8E',
    textAlign: 'center',
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'center',
  },
  badge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 12,
    paddingVertical: 6,
    backgroundColor: 'rgba(255, 215, 0, 0.1)',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: 'rgba(255, 215, 0, 0.2)',
  },
  badgeText: {
    fontSize: 12,
    color: '#FFD700',
    fontWeight: '600',
  },
});
