/**
 * Liquid Glass Button Component (v0 inspired)
 *
 * A button with interactive Liquid Glass morphing effect.
 * Features:
 * - Interactive glass morphing on press
 * - Smooth scale animations
 * - Progressive blur background
 */

import React from 'react';
import { TouchableOpacity, StyleSheet, ViewStyle } from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import Animated, {
  useAnimatedStyle,
  useSharedValue,
  withSpring,
  withTiming,
} from 'react-native-reanimated';
import { colors, spacing, animation } from '@/theme';

interface LiquidGlassButtonProps {
  icon: keyof typeof MaterialCommunityIcons.glyphMap;
  onPress: () => void;
  size?: number;
  iconSize?: number;
  color?: string;
  variant?: 'default' | 'primary' | 'ghost';
  disabled?: boolean;
  style?: ViewStyle;
}

export function LiquidGlassButton({
  icon,
  onPress,
  size = 40,
  iconSize = 24,
  color = colors.text,
  variant = 'default',
  disabled = false,
  style,
}: LiquidGlassButtonProps) {
  const scale = useSharedValue(1);
  const opacity = useSharedValue(1);

  const handlePressIn = () => {
    scale.value = withSpring(0.92, animation.easing.springStiff);
    if (variant === 'ghost') {
      opacity.value = withTiming(0.6, { duration: 100 });
    }
  };

  const handlePressOut = () => {
    scale.value = withSpring(1, animation.easing.spring);
    if (variant === 'ghost') {
      opacity.value = withTiming(1, { duration: 100 });
    }
  };

  const animatedStyle = useAnimatedStyle(() => ({
    transform: [{ scale: scale.value }],
    opacity: opacity.value,
  }));

  const buttonStyle = [
    styles.button,
    {
      width: size,
      height: size,
      borderRadius: size / 2,
    },
    variant === 'primary' && styles.buttonPrimary,
    variant === 'ghost' && styles.buttonGhost,
    disabled && styles.buttonDisabled,
    style,
  ];

  return (
    <Animated.View style={animatedStyle}>
      <TouchableOpacity
        style={buttonStyle}
        onPress={onPress}
        onPressIn={handlePressIn}
        onPressOut={handlePressOut}
        disabled={disabled}
        activeOpacity={0.9}
      >
        <MaterialCommunityIcons
          name={icon}
          size={iconSize}
          color={disabled ? colors.textTertiary : color}
        />
      </TouchableOpacity>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  button: {
    backgroundColor: 'rgba(255, 255, 255, 0.12)',
    borderWidth: 1.5,
    borderColor: 'rgba(255, 255, 255, 0.2)',
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOpacity: 0.15,
    shadowRadius: 4,
    shadowOffset: { width: 0, height: 2 },
  },
  buttonPrimary: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
    shadowColor: colors.primary,
    shadowOpacity: 0.4,
    shadowRadius: 8,
  },
  buttonGhost: {
    backgroundColor: 'transparent',
    borderColor: 'transparent',
    shadowOpacity: 0,
  },
  buttonDisabled: {
    opacity: 0.4,
  },
});

export default LiquidGlassButton;
