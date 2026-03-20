/**
 * Liquid Glass Header Component (v0 inspired)
 *
 * A header with back button and title using Liquid Glass design.
 * Features:
 * - Interactive Liquid Glass back button
 * - Progressive blur background
 * - Smooth morphing animations
 */

import React from 'react';
import { View, Text, StyleSheet, Platform } from 'react-native';
import { BlurView } from 'expo-blur';
import { useRouter } from 'expo-router';
import { colors, spacing, borderRadius, typography } from '@/theme';
import { LiquidGlassButton } from './LiquidGlassButton';

interface LiquidGlassHeaderProps {
  title: string;
  subtitle?: string;
  onBack?: () => void;
  rightAction?: {
    icon: any;
    onPress: () => void;
  };
  variant?: 'default' | 'transparent';
}

export function LiquidGlassHeader({
  title,
  subtitle,
  onBack,
  rightAction,
  variant = 'default',
}: LiquidGlassHeaderProps) {
  const router = useRouter();

  const handleBack = () => {
    if (onBack) {
      onBack();
    } else {
      router.back();
    }
  };

  return (
    <View style={[styles.container, variant === 'transparent' && styles.containerTransparent]}>
      {variant === 'default' && (
        <>
          {/* Progressive blur background */}
          <BlurView intensity={colors.liquidGlass.blurMedium} tint="dark" style={styles.blur} />
          {/* Bottom border */}
          <View style={styles.bottomBorder} />
        </>
      )}

      <View style={styles.content}>
        {/* Liquid Glass back button */}
        <LiquidGlassButton
          icon="arrow-left"
          onPress={handleBack}
          size={40}
          iconSize={24}
        />

        {/* Title section */}
        <View style={styles.titleContainer}>
          <Text style={styles.title} numberOfLines={1}>
            {title}
          </Text>
          {subtitle && (
            <Text style={styles.subtitle} numberOfLines={1}>
              {subtitle}
            </Text>
          )}
        </View>

        {/* Right action or spacer */}
        {rightAction ? (
          <LiquidGlassButton
            icon={rightAction.icon}
            onPress={rightAction.onPress}
            size={40}
            iconSize={24}
          />
        ) : (
          <View style={{ width: 40 }} />
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    position: 'relative',
    zIndex: 10,
  },
  containerTransparent: {
    backgroundColor: 'transparent',
  },
  blur: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: colors.liquidGlass.overlayMedium,
  },
  bottomBorder: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    height: 1,
    backgroundColor: colors.liquidGlass.borderLight,
  },
  content: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: spacing.md,
    paddingTop: Platform.OS === 'ios' ? 60 : spacing.lg,
    paddingBottom: spacing.md,
  },
  titleContainer: {
    flex: 1,
    alignItems: 'center',
    paddingHorizontal: spacing.sm,
  },
  title: {
    ...typography.headlineMedium,
    color: colors.text,
    textAlign: 'center',
  },
  subtitle: {
    ...typography.labelMedium,
    color: colors.textSecondary,
    marginTop: 2,
    textAlign: 'center',
  },
});

export default LiquidGlassHeader;
