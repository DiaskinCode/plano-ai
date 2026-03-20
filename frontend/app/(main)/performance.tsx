import { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  Dimensions,
  ActivityIndicator,
  RefreshControl,
} from 'react-native';
import { performanceAPI } from '@/services/api';
import { MaterialCommunityIcons } from '@expo/vector-icons';

const { width } = Dimensions.get('window');

interface PerformanceInsights {
  completion_rate: number;
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  optimal_schedule: {
    high_energy_hours: number[];
    low_energy_hours: number[];
    best_day: string;
    worst_day: string;
    completion_by_hour: Record<number, number>;
    completion_by_day: Record<string, number>;
  };
  task_type_performance: Record<string, {
    completed: number;
    total: number;
    rate: number;
  }>;
  energy_patterns: Record<string, {
    completed: number;
    total: number;
    rate: number;
  }>;
  blockers: Array<{
    task_id: number;
    title: string;
    task_type: string;
    days_overdue: number;
    status: string;
    pattern: string;
  }>;
  strengths: string[];
  warnings: string[];
  recommended_actions: string[];
  last_analysis: string;
  tasks_analyzed: number;
}

export default function PerformanceScreen() {
  const [insights, setInsights] = useState<PerformanceInsights | null>(null);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadPerformance();
  }, []);

  const loadPerformance = async () => {
    try {
      setLoading(true);
      const response = await performanceAPI.getInsights();
      setInsights(response.data);
    } catch (error) {
      console.error('Failed to load performance insights:', error);
    } finally {
      setLoading(false);
    }
  };

  const triggerAnalysis = async () => {
    try {
      setRefreshing(true);
      const response = await performanceAPI.triggerAnalysis();
      setInsights(response.data);
    } catch (error) {
      console.error('Failed to trigger analysis:', error);
    } finally {
      setRefreshing(false);
    }
  };

  if (loading && !insights) {
    return (
      <View style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#007AFF" />
          <Text style={styles.loadingText}>Analyzing your performance...</Text>
        </View>
      </View>
    );
  }

  const getRiskColor = (riskLevel: string) => {
    switch (riskLevel) {
      case 'low': return '#34C759';
      case 'medium': return '#FFD700';
      case 'high': return '#FF9500';
      case 'critical': return '#FF3B30';
      default: return '#8E8E93';
    }
  };

  const getRiskIcon = (riskLevel: string) => {
    switch (riskLevel) {
      case 'low': return 'check-circle';
      case 'medium': return 'alert-circle-outline';
      case 'high': return 'alert';
      case 'critical': return 'alert-octagon';
      default: return 'help-circle-outline';
    }
  };

  const formatHour = (hour: number) => {
    const period = hour >= 12 ? 'PM' : 'AM';
    const displayHour = hour > 12 ? hour - 12 : (hour === 0 ? 12 : hour);
    return `${displayHour}${period}`;
  };

  return (
    <View style={styles.container}>
      <ScrollView
        style={styles.scrollView}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={triggerAnalysis}
            tintColor="#007AFF"
          />
        }
      >
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.headerTitle}>Performance Insights</Text>
          <Text style={styles.headerSubtitle}>
            30-day analysis • {insights?.tasks_analyzed || 0} tasks
          </Text>
        </View>

        {/* Risk Level Card */}
        <View style={styles.card}>
          <View style={styles.riskHeader}>
            <MaterialCommunityIcons
              name={getRiskIcon(insights?.risk_level || 'low')}
              size={32}
              color={getRiskColor(insights?.risk_level || 'low')}
            />
            <View style={styles.riskInfo}>
              <Text style={styles.cardTitle}>Current Status</Text>
              <Text style={[styles.riskLevel, { color: getRiskColor(insights?.risk_level || 'low') }]}>
                {insights?.risk_level?.toUpperCase() || 'UNKNOWN'} RISK
              </Text>
            </View>
            <View style={styles.completionBadge}>
              <Text style={styles.completionRate}>
                {Math.round((insights?.completion_rate || 0) * 100)}%
              </Text>
              <Text style={styles.completionLabel}>Complete</Text>
            </View>
          </View>
        </View>

        {/* Strengths */}
        {insights?.strengths && insights.strengths.length > 0 && (
          <View style={styles.card}>
            <View style={styles.cardHeader}>
              <MaterialCommunityIcons name="star" size={20} color="#FFD700" />
              <Text style={styles.cardTitle}>Your Strengths</Text>
            </View>
            {insights.strengths.map((strength, index) => (
              <View key={index} style={styles.listItem}>
                <Text style={styles.listItemBullet}>✓</Text>
                <Text style={styles.listItemText}>{strength}</Text>
              </View>
            ))}
          </View>
        )}

        {/* Warnings */}
        {insights?.warnings && insights.warnings.length > 0 && (
          <View style={[styles.card, styles.warningCard]}>
            <View style={styles.cardHeader}>
              <MaterialCommunityIcons name="alert" size={20} color="#FF9500" />
              <Text style={styles.cardTitle}>Areas for Improvement</Text>
            </View>
            {insights.warnings.map((warning, index) => (
              <View key={index} style={styles.listItem}>
                <Text style={styles.warningBullet}>⚠</Text>
                <Text style={styles.listItemText}>{warning}</Text>
              </View>
            ))}
          </View>
        )}

        {/* Optimal Schedule */}
        {insights?.optimal_schedule && (
          <View style={styles.card}>
            <View style={styles.cardHeader}>
              <MaterialCommunityIcons name="clock-outline" size={20} color="#007AFF" />
              <Text style={styles.cardTitle}>Your Peak Hours</Text>
            </View>
            <View style={styles.hoursContainer}>
              <View style={styles.hoursRow}>
                <Text style={styles.hoursLabel}>High Energy</Text>
                <View style={styles.hoursList}>
                  {insights.optimal_schedule.high_energy_hours.map((hour) => (
                    <View key={hour} style={[styles.hourBadge, styles.highEnergyBadge]}>
                      <Text style={styles.hourBadgeText}>{formatHour(hour)}</Text>
                    </View>
                  ))}
                </View>
              </View>
              <View style={styles.hoursRow}>
                <Text style={styles.hoursLabel}>Low Energy</Text>
                <View style={styles.hoursList}>
                  {insights.optimal_schedule.low_energy_hours.slice(0, 3).map((hour) => (
                    <View key={hour} style={[styles.hourBadge, styles.lowEnergyBadge]}>
                      <Text style={styles.hourBadgeText}>{formatHour(hour)}</Text>
                    </View>
                  ))}
                </View>
              </View>
            </View>
            <View style={styles.divider} />
            <View style={styles.statsRow}>
              <View style={styles.statItem}>
                <Text style={styles.statLabel}>Best Day</Text>
                <Text style={styles.statValue}>{insights.optimal_schedule.best_day}</Text>
              </View>
              <View style={styles.statItem}>
                <Text style={styles.statLabel}>Worst Day</Text>
                <Text style={styles.statValue}>{insights.optimal_schedule.worst_day}</Text>
              </View>
            </View>
          </View>
        )}

        {/* Task Type Performance */}
        {insights?.task_type_performance && Object.keys(insights.task_type_performance).length > 0 && (
          <View style={styles.card}>
            <View style={styles.cardHeader}>
              <MaterialCommunityIcons name="format-list-checks" size={20} color="#007AFF" />
              <Text style={styles.cardTitle}>Task Type Performance</Text>
            </View>
            {Object.entries(insights.task_type_performance).map(([type, perf]) => (
              <View key={type} style={styles.performanceRow}>
                <View style={styles.performanceHeader}>
                  <Text style={styles.performanceType}>{type.toUpperCase()}</Text>
                  <Text style={styles.performanceRate}>
                    {Math.round(perf.rate * 100)}%
                  </Text>
                </View>
                <View style={styles.progressBar}>
                  <View
                    style={[
                      styles.progressFill,
                      {
                        width: `${perf.rate * 100}%`,
                        backgroundColor: perf.rate >= 0.7 ? '#34C759' : perf.rate >= 0.5 ? '#FFD700' : '#FF3B30',
                      },
                    ]}
                  />
                </View>
                <Text style={styles.performanceCount}>
                  {perf.completed} / {perf.total} completed
                </Text>
              </View>
            ))}
          </View>
        )}

        {/* Blockers */}
        {insights?.blockers && insights.blockers.length > 0 && (
          <View style={[styles.card, styles.blockersCard]}>
            <View style={styles.cardHeader}>
              <MaterialCommunityIcons name="block-helper" size={20} color="#FF3B30" />
              <Text style={styles.cardTitle}>Chronic Blockers</Text>
            </View>
            {insights.blockers.map((blocker) => (
              <View key={blocker.task_id} style={styles.blockerItem}>
                <View style={styles.blockerHeader}>
                  <Text style={styles.blockerTitle}>{blocker.title}</Text>
                  <Text style={styles.blockerDays}>{blocker.days_overdue}d overdue</Text>
                </View>
                <Text style={styles.blockerPattern}>{blocker.pattern}</Text>
              </View>
            ))}
          </View>
        )}

        {/* Recommended Actions */}
        {insights?.recommended_actions && insights.recommended_actions.length > 0 && (
          <View style={styles.card}>
            <View style={styles.cardHeader}>
              <MaterialCommunityIcons name="lightbulb-on" size={20} color="#FFD700" />
              <Text style={styles.cardTitle}>Recommended Actions</Text>
            </View>
            {insights.recommended_actions.map((action, index) => (
              <View key={index} style={styles.actionItem}>
                <Text style={styles.actionNumber}>{index + 1}</Text>
                <Text style={styles.actionText}>{action}</Text>
              </View>
            ))}
          </View>
        )}

        <View style={styles.footer}>
          <Text style={styles.footerText}>
            Last updated: {insights?.last_analysis ? new Date(insights.last_analysis).toLocaleString() : 'Never'}
          </Text>
          <Text style={styles.footerHint}>Pull down to refresh</Text>
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F2F2F7',
  },
  scrollView: {
    flex: 1,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: '#8E8E93',
  },
  header: {
    padding: 20,
    paddingTop: 60,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  headerTitle: {
    fontSize: 32,
    fontWeight: '700',
    color: '#000000',
    marginBottom: 4,
  },
  headerSubtitle: {
    fontSize: 14,
    color: '#8E8E93',
  },
  card: {
    backgroundColor: '#FFFFFF',
    marginHorizontal: 16,
    marginTop: 16,
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  warningCard: {
    backgroundColor: '#FFF8F0',
    borderLeftWidth: 4,
    borderLeftColor: '#FF9500',
  },
  blockersCard: {
    backgroundColor: '#FFF5F5',
    borderLeftWidth: 4,
    borderLeftColor: '#FF3B30',
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#000000',
    marginLeft: 8,
  },
  riskHeader: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  riskInfo: {
    flex: 1,
    marginLeft: 12,
  },
  riskLevel: {
    fontSize: 20,
    fontWeight: '700',
    marginTop: 4,
  },
  completionBadge: {
    alignItems: 'center',
  },
  completionRate: {
    fontSize: 24,
    fontWeight: '700',
    color: '#007AFF',
  },
  completionLabel: {
    fontSize: 12,
    color: '#8E8E93',
  },
  listItem: {
    flexDirection: 'row',
    marginBottom: 12,
  },
  listItemBullet: {
    fontSize: 16,
    color: '#34C759',
    marginRight: 8,
    fontWeight: '700',
  },
  warningBullet: {
    fontSize: 16,
    color: '#FF9500',
    marginRight: 8,
  },
  listItemText: {
    flex: 1,
    fontSize: 15,
    color: '#000000',
    lineHeight: 20,
  },
  hoursContainer: {
    gap: 16,
  },
  hoursRow: {
    gap: 8,
  },
  hoursLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#8E8E93',
    marginBottom: 8,
  },
  hoursList: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  hourBadge: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
  },
  highEnergyBadge: {
    backgroundColor: '#E8F5E9',
  },
  lowEnergyBadge: {
    backgroundColor: '#FFF3E0',
  },
  hourBadgeText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#000000',
  },
  divider: {
    height: 1,
    backgroundColor: '#E5E5EA',
    marginVertical: 16,
  },
  statsRow: {
    flexDirection: 'row',
    gap: 16,
  },
  statItem: {
    flex: 1,
  },
  statLabel: {
    fontSize: 12,
    color: '#8E8E93',
    marginBottom: 4,
  },
  statValue: {
    fontSize: 16,
    fontWeight: '600',
    color: '#000000',
  },
  performanceRow: {
    marginBottom: 16,
  },
  performanceHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  performanceType: {
    fontSize: 14,
    fontWeight: '600',
    color: '#000000',
  },
  performanceRate: {
    fontSize: 16,
    fontWeight: '700',
    color: '#007AFF',
  },
  progressBar: {
    height: 8,
    backgroundColor: '#E5E5EA',
    borderRadius: 4,
    overflow: 'hidden',
    marginBottom: 4,
  },
  progressFill: {
    height: '100%',
    borderRadius: 4,
  },
  performanceCount: {
    fontSize: 12,
    color: '#8E8E93',
  },
  blockerItem: {
    marginBottom: 16,
    paddingBottom: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  blockerHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  blockerTitle: {
    flex: 1,
    fontSize: 15,
    fontWeight: '600',
    color: '#000000',
  },
  blockerDays: {
    fontSize: 13,
    fontWeight: '600',
    color: '#FF3B30',
  },
  blockerPattern: {
    fontSize: 13,
    color: '#8E8E93',
    lineHeight: 18,
  },
  actionItem: {
    flexDirection: 'row',
    marginBottom: 12,
  },
  actionNumber: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: '#007AFF',
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: '700',
    textAlign: 'center',
    lineHeight: 24,
    marginRight: 12,
  },
  actionText: {
    flex: 1,
    fontSize: 15,
    color: '#000000',
    lineHeight: 20,
  },
  footer: {
    padding: 20,
    alignItems: 'center',
  },
  footerText: {
    fontSize: 12,
    color: '#8E8E93',
    marginBottom: 4,
  },
  footerHint: {
    fontSize: 12,
    color: '#C7C7CC',
  },
});
