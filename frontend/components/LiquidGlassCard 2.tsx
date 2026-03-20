/**
 * Liquid Glass Card Component (v0 inspired)
 *
 * A card container with interactive Liquid Glass morphing effect.
 * Features:
 * - Interactive glass morphing on press (optional)
 * - Progressive blur background
 * - Smooth hover/press animations
 */

import React from 'react';
import { View, TouchableOpacity, StyleSheet, ViewStyle } from 'react-native';
import Animated, {
  useAnimatedStyle,
  useSharedValue,
  withSpring,
  withTiming,
} from 'react-native-reanimated';
import { colors, spacing, borderRadius, animation, shadows } from '@/theme';

interface LiquidGlassCardProps {
  children: React.ReactNode;
  onPress?: () => void;
  interactive?: boolean;
  variant?: 'default' | 'elevated' | 'subtle';
  style?: ViewStyle;
  disabled?: boolean;
}

export function LiquidGlassCard({
  children,
  onPress,
  interactive = true,
  variant = 'default',
  disabled = false,
  style,
}: LiquidGlassCardProps) {
  const scale = useSharedValue(1);
  const opacity = useSharedValue(1);

  const handlePressIn = () => {
    if (!onPress || disabled) return;
    scale.value = withSpring(0.97, animation.easing.springStiff);
    opacity.value = withTiming(0.8, { duration: 100 });
  };

  const handlePressOut = () => {
    if (!onPress || disabled) return;
    scale.value = withSpring(1, animation.easing.spring);
    opacity.value = withTiming(1, { duration: 100 });
  };

  const animatedStyle = useAnimatedStyle(() => ({
    transform: [{ scale: scale.value }],
    opacity: opacity.value,
  }));

  const cardStyle = [
    styles.card,
    variant === 'elevated' && styles.cardElevated,
    variant === 'subtle' && styles.cardSubtle,
    disabled && styles.cardDisabled,
    style,
  ];

  const content = (
    <View style={cardStyle}>
      {children}
    </View>
  );

  if (onPress) {
    return (
      <Animated.View style={animatedStyle}>
        <TouchableOpacity
          onPress={onPress}
          onPressIn={handlePressIn}
          onPressOut={handlePressOut}
          disabled={disabled}
          activeOpacity={0.95}
        >
          {content}
        </TouchableOpacity>
      </Animated.View>
    );
  }

  return <>{content}</>;
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.liquidGlass.base,
    borderWidth: 1,
    borderColor: colors.liquidGlass.borderMedium,
    borderRadius: borderRadius.lg,
    padding: spacing.md,
    overflow: 'hidden',
  },
  cardElevated: {
    backgroundColor: colors.liquidGlass.hover,
    borderColor: colors.liquidGlass.borderHeavy,
    ...shadows.md,
  },
  cardSubtle: {
    backgroundColor: 'rgba(255, 255, 255, 0.03)',
    borderColor: colors.liquidGlass.borderLight,
  },
  cardDisabled: {
    opacity: 0.5,
  },
});

export default LiquidGlassCard;
