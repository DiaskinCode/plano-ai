import { View, Text, StyleSheet } from 'react-native';
import Svg, { Circle } from 'react-native-svg';
import { useEffect, useRef } from 'react';
import { Animated } from 'react-native';

const COLORS = {
  primary: '#5B6AFF',
  primaryCelebration: '#34D399',
  surface: '#2A2A2A',
  text: '#ECECEC',
  textSecondary: '#8E8E8E',
};

interface ProgressRingProps {
  completed: number;
  total: number;
  size?: number;
  strokeWidth?: number;
}

export default function ProgressRing({
  completed,
  total,
  size = 120,
  strokeWidth = 12
}: ProgressRingProps) {
  const progress = total > 0 ? (completed / total) * 100 : 0;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const progressOffset = circumference - (progress / 100) * circumference;

  // 240° arc (2/3 of circle)
  const arcLength = (240 / 360) * circumference;
  const strokeDasharray = `${arcLength} ${circumference}`;

  // Animation for celebration at 80%
  const pulseAnim = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    if (progress >= 80) {
      Animated.loop(
        Animated.sequence([
          Animated.timing(pulseAnim, {
            toValue: 1.05,
            duration: 500,
            useNativeDriver: true,
          }),
          Animated.timing(pulseAnim, {
            toValue: 1,
            duration: 500,
            useNativeDriver: true,
          }),
        ])
      ).start();
    }
  }, [progress]);

  const ringColor = progress >= 80 ? COLORS.primaryCelebration : COLORS.primary;

  return (
    <Animated.View style={[styles.container, { transform: [{ scale: pulseAnim }] }]}>
      <Svg width={size} height={size} style={styles.svg}>
        {/* Background arc */}
        <Circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={COLORS.surface}
          strokeWidth={strokeWidth}
          fill="none"
          strokeDasharray={strokeDasharray}
          strokeDashoffset={0}
          rotation="-210"
          origin={`${size / 2}, ${size / 2}`}
          strokeLinecap="round"
        />
        {/* Progress arc */}
        <Circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={ringColor}
          strokeWidth={strokeWidth}
          fill="none"
          strokeDasharray={strokeDasharray}
          strokeDashoffset={progressOffset * (240 / 360)}
          rotation="-210"
          origin={`${size / 2}, ${size / 2}`}
          strokeLinecap="round"
        />
      </Svg>
      <View style={styles.textContainer}>
        <Text style={styles.percentage}>{Math.round(progress)}%</Text>
        <Text style={styles.details}>
          {completed}m / {total}m
        </Text>
      </View>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  svg: {
    position: 'absolute',
  },
  textContainer: {
    alignItems: 'center',
  },
  percentage: {
    fontSize: 28,
    fontWeight: 'bold',
    color: COLORS.text,
  },
  details: {
    fontSize: 12,
    color: COLORS.textSecondary,
    marginTop: 4,
  },
});
