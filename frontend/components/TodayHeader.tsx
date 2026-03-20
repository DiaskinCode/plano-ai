import { View, Text, StyleSheet, TouchableOpacity, ScrollView } from 'react-native';
import ProgressRing from './ProgressRing';
import MomentumSparkline from './MomentumSparkline';
import { MaterialCommunityIcons } from '@expo/vector-icons';

const COLORS = {
  bg: '#1A1A1A',
  surface: '#2A2A2A',
  border: '#3E3E3E',
  text: '#ECECEC',
  textSecondary: '#8E8E8E',
  primary: '#5B6AFF',
  warning: '#F59E0B',
};

interface TodayHeaderProps {
  focusMinutesCompleted: number;
  todayTimeBudget: number;
  milestoneDone: number;
  milestoneTotal: number;
  weekData: Array<{
    date: string;
    focusMinutes: number;
    milestoneCriticalCount: number;
  }>;
  reasonFeed: Array<{
    id: string;
    message: string;
    timestamp: string;
  }>;
  shortWinsCount: number;
  streakDays: number;
  streakTotal: number;
  onInsertMicroWins?: () => void;
}

export default function TodayHeader({
  focusMinutesCompleted,
  todayTimeBudget,
  milestoneDone,
  milestoneTotal,
  weekData,
  reasonFeed,
  shortWinsCount,
  streakDays,
  streakTotal,
  onInsertMicroWins,
}: TodayHeaderProps) {
  return (
    <View style={styles.container}>
      {/* Progress Ring and Sparkline Row */}
      <View style={styles.topRow}>
        <View style={styles.ringContainer}>
          <ProgressRing
            completed={focusMinutesCompleted}
            total={todayTimeBudget}
            size={120}
            strokeWidth={12}
          />
          <Text style={styles.subtitle}>
            Milestone-critical done: {milestoneDone}/{milestoneTotal}
          </Text>
        </View>

        <View style={styles.sparklineContainer}>
          <Text style={styles.sparklineLabel}>7-Day Momentum</Text>
          <MomentumSparkline data={weekData} />
        </View>
      </View>

      {/* Reason Feed */}
      {reasonFeed.length > 0 && (
        <View style={styles.reasonFeed}>
          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={styles.reasonScrollContent}
          >
            {reasonFeed.slice(0, 2).map((reason) => (
              <View key={reason.id} style={styles.reasonCard}>
                <MaterialCommunityIcons name="information" size={14} color={COLORS.textSecondary} />
                <Text style={styles.reasonText} numberOfLines={2}>
                  {reason.message}
                </Text>
              </View>
            ))}
          </ScrollView>
        </View>
      )}

      {/* Micro-wins and Streak Row */}
      <View style={styles.bottomRow}>
        {shortWinsCount > 0 && (
          <TouchableOpacity
            style={styles.microWinsButton}
            onPress={onInsertMicroWins}
          >
            <MaterialCommunityIcons name="lightning-bolt" size={16} color={COLORS.primary} />
            <Text style={styles.microWinsText}>
              {shortWinsCount} short wins left (≤15m)
            </Text>
          </TouchableOpacity>
        )}

        <View style={styles.streakBadge}>
          <MaterialCommunityIcons name="fire" size={16} color={COLORS.warning} />
          <Text style={styles.streakText}>
            {streakDays} of last {streakTotal} days planned
          </Text>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: COLORS.surface,
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  topRow: {
    flexDirection: 'row',
    marginBottom: 16,
  },
  ringContainer: {
    alignItems: 'center',
    marginRight: 24,
  },
  subtitle: {
    fontSize: 11,
    color: COLORS.textSecondary,
    marginTop: 8,
    textAlign: 'center',
  },
  sparklineContainer: {
    flex: 1,
    justifyContent: 'center',
  },
  sparklineLabel: {
    fontSize: 12,
    color: COLORS.textSecondary,
    marginBottom: 8,
    fontWeight: '600',
  },
  reasonFeed: {
    marginBottom: 12,
  },
  reasonScrollContent: {
    paddingRight: 16,
  },
  reasonCard: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: COLORS.bg,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 8,
    padding: 10,
    marginRight: 8,
    maxWidth: 280,
  },
  reasonText: {
    fontSize: 11,
    color: COLORS.text,
    marginLeft: 6,
    flex: 1,
  },
  bottomRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  microWinsButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.bg,
    borderWidth: 1,
    borderColor: COLORS.primary,
    borderRadius: 8,
    paddingVertical: 8,
    paddingHorizontal: 12,
  },
  microWinsText: {
    fontSize: 12,
    color: COLORS.primary,
    marginLeft: 6,
    fontWeight: '600',
  },
  streakBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.bg,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 8,
    paddingVertical: 8,
    paddingHorizontal: 12,
  },
  streakText: {
    fontSize: 12,
    color: COLORS.textSecondary,
    marginLeft: 6,
  },
});
