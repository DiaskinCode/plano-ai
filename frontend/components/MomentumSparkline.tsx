import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import Svg, { Circle, Line } from 'react-native-svg';

const COLORS = {
  primary: '#5B6AFF',
  surface: '#2A2A2A',
  text: '#ECECEC',
  textSecondary: '#8E8E8E',
  border: '#3E3E3E',
};

interface DayData {
  date: string;
  focusMinutes: number;
  milestoneCriticalCount: number;
}

interface MomentumSparklineProps {
  data: DayData[];
  maxValue?: number;
}

export default function MomentumSparkline({ data, maxValue }: MomentumSparklineProps) {
  const dotRadius = 4;
  const spacing = 40;
  const height = 40;
  const width = (data.length - 1) * spacing + dotRadius * 2;

  const max = maxValue || Math.max(...data.map(d => d.focusMinutes), 1);

  return (
    <View style={styles.container}>
      <Svg width={width} height={height}>
        {/* Connect dots with lines */}
        {data.map((point, index) => {
          if (index === data.length - 1) return null;
          const nextPoint = data[index + 1];
          const x1 = index * spacing + dotRadius;
          const y1 = height - (point.focusMinutes / max) * (height - dotRadius * 2) - dotRadius;
          const x2 = (index + 1) * spacing + dotRadius;
          const y2 = height - (nextPoint.focusMinutes / max) * (height - dotRadius * 2) - dotRadius;

          return (
            <Line
              key={`line-${index}`}
              x1={x1}
              y1={y1}
              x2={x2}
              y2={y2}
              stroke={COLORS.primary}
              strokeWidth={2}
              opacity={0.3}
            />
          );
        })}

        {/* Draw dots */}
        {data.map((point, index) => {
          const x = index * spacing + dotRadius;
          const y = height - (point.focusMinutes / max) * (height - dotRadius * 2) - dotRadius;

          return (
            <Circle
              key={`dot-${index}`}
              cx={x}
              cy={y}
              r={dotRadius}
              fill={COLORS.primary}
            />
          );
        })}
      </Svg>
      <View style={styles.labelsContainer}>
        {data.map((point, index) => (
          <View key={`label-${index}`} style={[styles.labelWrapper, { width: spacing }]}>
            <Text style={styles.dayLabel}>
              {new Date(point.date).toLocaleDateString('en-US', { weekday: 'short' })[0]}
            </Text>
          </View>
        ))}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    paddingVertical: 8,
  },
  labelsContainer: {
    flexDirection: 'row',
    marginTop: 4,
  },
  labelWrapper: {
    alignItems: 'center',
  },
  dayLabel: {
    fontSize: 10,
    color: COLORS.textSecondary,
  },
});
