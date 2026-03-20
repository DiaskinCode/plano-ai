/**
 * Liquid Glass Card Component (v0 inspired)
 *
 * A card container with interactive Liquid Glass morphing effect.
 * Features:
 * - Interactive glass morphing on press (optional)
 * - Progressive blur background
 * - Smooth hover/press animations
 */

import { View, TouchableOpacity, StyleSheet, ViewStyle, StyleProp } from 'react-native';
import Animated, {
  useAnimatedStyle,
  useSharedValue,
  withSpring,
  withTiming,
} from 'react-native-reanimated';
import { BlurView } from 'expo-blur';
import { colors, spacing, borderRadius, animation } from '@/theme';

interface LiquidGlassCardProps {
  children: React.ReactNode;
  onPress?: () => void;
  interactive?: boolean;
  variant?: 'default' | 'elevated' | 'subtle';
  intensity?: 'light' | 'medium' | 'heavy';
  style?: StyleProp<ViewStyle>;
  disabled?: boolean;
}

export function LiquidGlassCard({
  children,
  onPress,
  interactive = true,
  variant = 'default',
  intensity = 'medium',
  disabled = false,
  style,
}: LiquidGlassCardProps) {
  const scale = useSharedValue(1);
  const opacity = useSharedValue(1);

  const handlePressIn = () => {
    if (!onPress || disabled) return;
    scale.value = withSpring(0.98, animation.easing.springStiff);
    opacity.value = withTiming(0.9, { duration: 100 });
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

  const getBlurIntensity = () => {
    switch (intensity) {
      case 'light': return colors.liquidGlass.blurLight;
      case 'heavy': return colors.liquidGlass.blurHeavy;
      default: return colors.liquidGlass.blurMedium;
    }
  };

  const cardStyle = [
    styles.card,
    variant === 'elevated' && styles.cardElevated,
    variant === 'subtle' && styles.cardSubtle,
    disabled && styles.cardDisabled,
  ];

  const content = (
    <View style={cardStyle}>
      <BlurView
        intensity={getBlurIntensity()}
        tint="dark"
        style={StyleSheet.absoluteFill}
      />
      <View style={styles.contentContainer}>
        {children}
      </View>
    </View>
  );

  if (onPress) {
    return (
      <Animated.View style={[animatedStyle, style]}>
        <TouchableOpacity
          onPress={onPress}
          onPressIn={handlePressIn}
          onPressOut={handlePressOut}
          disabled={disabled}
          activeOpacity={1}
        >
          {content}
        </TouchableOpacity>
      </Animated.View>
    );
  }

  return <View style={style}>{content}</View>;
}

const styles = StyleSheet.create({
  card: {
    width: '100%',
    backgroundColor: colors.liquidGlass.base,
    borderWidth: 1,
    borderColor: colors.liquidGlass.borderMedium,
    borderRadius: borderRadius.lg,
    overflow: 'hidden',
  },
  contentContainer: {
    padding: spacing.md,
    zIndex: 1,
  },
  cardElevated: {
    backgroundColor: colors.liquidGlass.hover,
    borderColor: colors.liquidGlass.borderHeavy,
    borderWidth: 1.5,
    shadowColor: '#000',
    shadowOpacity: 0.3,
    shadowRadius: 12,
    shadowOffset: { width: 0, height: 4 },
  },
  cardSubtle: {
    backgroundColor: 'transparent',
    borderColor: colors.liquidGlass.borderLight,
    borderWidth: 0.5,
  },
  cardDisabled: {
    opacity: 0.5,
  },
});

export default LiquidGlassCard;
