import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import Animated, {
  useAnimatedStyle,
  withTiming,
  useSharedValue,
} from 'react-native-reanimated';
import { colors, spacing, typography } from '@/theme';

interface HeroSectionProps {
  headline: string;
  subtitle: string;
  visible?: boolean;
}

/**
 * Hero section for empty chat state.
 * Shows personalized headline with animated gradient background.
 */
export function HeroSection({ headline, subtitle, visible = true }: HeroSectionProps) {
  const opacity = useSharedValue(visible ? 1 : 0);

  React.useEffect(() => {
    opacity.value = withTiming(visible ? 1 : 0, { duration: 300 });
  }, [visible, opacity]);

  const animatedStyle = useAnimatedStyle(() => ({
    opacity: opacity.value,
    transform: [{ translateY: visible ? 0 : -20 }],
  }));

  return (
    <Animated.View style={[styles.container, animatedStyle]}>
      {/* Gradient background ellipse */}
      <LinearGradient
        colors={[
          'rgba(255, 255, 255, 0.3)',
          'rgba(147, 147, 147, 0.1)',
          'transparent',
        ]}
        style={styles.ellipse}
        start={{ x: 0.5, y: 0 }}
        end={{ x: 0.5, y: 1 }}
      />

      {/* Text content */}
      <View style={styles.textContainer}>
        <Text style={styles.title}>Ask anything</Text>
        {headline && <Text style={styles.headline}>{headline}</Text>}
        {subtitle && <Text style={styles.subtitle}>{subtitle}</Text>}
      </View>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  container: {
    paddingHorizontal: spacing.lg,
    paddingTop: 60,
    paddingBottom: 60,
    alignItems: 'center',
    overflow: 'hidden',
  },
  ellipse: {
    position: 'absolute',
    width: 300,
    height: 300,
    borderRadius: 150,
    top: 20,
    alignSelf: 'center',
  },
  textContainer: {
    alignItems: 'center',
    paddingHorizontal: spacing.lg,
    zIndex: 1,
  },
  title: {
    fontSize: 48,
    fontWeight: '700',
    color: colors.text,
    marginBottom: spacing.sm,
    textAlign: 'center',
  },
  headline: {
    fontSize: 20,
    fontWeight: '500',
    color: colors.textSecondary,
    marginBottom: spacing.xs,
    textAlign: 'center',
  },
  subtitle: {
    ...typography.bodyMedium,
    color: colors.textTertiary,
    textAlign: 'center',
    lineHeight: 20,
  },
});

export default HeroSection;
