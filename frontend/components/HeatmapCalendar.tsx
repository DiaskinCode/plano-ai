import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';

const COLORS = {
  bg: '#1A1A1A',
  surface: '#2A2A2A',
  border: '#3E3E3E',
  text: '#ECECEC',
  textSecondary: '#8E8E8E',
  primary: '#5B6AFF',
  heatLow: '#1E3A33',
  heatMid: '#2D5A4A',
  heatHigh: '#5B6AFF',
};

interface DayData {
  date: string;
  focusMinutes: number;
  budget: number;
  milestoneCriticalComplete: number;
  milestoneCriticalTotal: number;
}

interface HeatmapCalendarProps {
  data: DayData[];
  onDayPress?: (day: DayData) => void;
}

export default function HeatmapCalendar({ data, onDayPress }: HeatmapCalendarProps) {
  const getHeatColor = (day: DayData) => {
    if (day.budget === 0) return COLORS.surface;
    const ratio = day.focusMinutes / day.budget;
    if (ratio >= 0.8) return COLORS.heatHigh;
    if (ratio >= 0.5) return COLORS.heatMid;
    if (ratio > 0) return COLORS.heatLow;
    return COLORS.surface;
  };

  const weekDays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

  // Organize data by weeks
  const weeks: DayData[][] = [];
  let currentWeek: DayData[] = [];

  data.forEach((day, index) => {
    currentWeek.push(day);
    if (currentWeek.length === 7 || index === data.length - 1) {
      weeks.push([...currentWeek]);
      currentWeek = [];
    }
  });

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Weekly Focus Heatmap</Text>

      {/* Weekday headers */}
      <View style={styles.headerRow}>
        {weekDays.map(day => (
          <Text key={day} style={styles.headerText}>{day[0]}</Text>
        ))}
      </View>

      {/* Heatmap grid */}
      {weeks.map((week, weekIndex) => (
        <View key={weekIndex} style={styles.weekRow}>
          {week.map((day, dayIndex) => {
            const date = new Date(day.date);
            const isToday = day.date === new Date().toISOString().split('T')[0];

            return (
              <TouchableOpacity
                key={dayIndex}
                style={[
                  styles.dayCell,
                  { backgroundColor: getHeatColor(day) },
                  isToday && styles.todayCell,
                ]}
                onPress={() => onDayPress?.(day)}
              >
                <Text style={styles.dayNumber}>{date.getDate()}</Text>
              </TouchableOpacity>
            );
          })}
          {/* Fill empty cells for incomplete weeks */}
          {week.length < 7 && Array.from({ length: 7 - week.length }).map((_, i) => (
            <View key={`empty-${i}`} style={[styles.dayCell, styles.emptyCell]} />
          ))}
        </View>
      ))}

      {/* Legend */}
      <View style={styles.legend}>
        <Text style={styles.legendLabel}>Less</Text>
        <View style={[styles.legendBox, { backgroundColor: COLORS.surface }]} />
        <View style={[styles.legendBox, { backgroundColor: COLORS.heatLow }]} />
        <View style={[styles.legendBox, { backgroundColor: COLORS.heatMid }]} />
        <View style={[styles.legendBox, { backgroundColor: COLORS.heatHigh }]} />
        <Text style={styles.legendLabel}>More</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: 16,
    backgroundColor: COLORS.surface,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  title: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: 12,
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 8,
  },
  headerText: {
    fontSize: 10,
    color: COLORS.textSecondary,
    width: 32,
    textAlign: 'center',
  },
  weekRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 4,
  },
  dayCell: {
    width: 32,
    height: 32,
    borderRadius: 4,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  todayCell: {
    borderColor: COLORS.primary,
    borderWidth: 2,
  },
  emptyCell: {
    backgroundColor: 'transparent',
    borderColor: 'transparent',
  },
  dayNumber: {
    fontSize: 10,
    color: COLORS.text,
    fontWeight: '600',
  },
  legend: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 12,
    gap: 4,
  },
  legendLabel: {
    fontSize: 10,
    color: COLORS.textSecondary,
    marginHorizontal: 4,
  },
  legendBox: {
    width: 12,
    height: 12,
    borderRadius: 2,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
});
