import React from 'react';
import { View, Image, StyleSheet } from 'react-native';
import { BlurView } from 'expo-blur';
import { colors, spacing } from '@/theme';
import { LiquidGlassButton } from '../LiquidGlassButton';

interface ChatHeaderProps {
  onMenuPress: () => void;
  onBackPress?: () => void;
  onActionPress?: () => void;
}

/**
 * Chat header component with Liquid Glass navigation (v0 inspired).
 * Features:
 * - Liquid Glass menu and action buttons
 * - Progressive blur background
 * - Smooth morphing animations
 */
export function ChatHeader({ onMenuPress, onBackPress, onActionPress }: ChatHeaderProps) {
  return (
    <View style={styles.container}>
      {/* Progressive blur background */}
      <BlurView intensity={50} tint="dark" style={styles.blur} />

      <View style={styles.content}>
        {/* Left section: Back button (optional) and Menu button */}
        <View style={styles.leftSection}>
          {onBackPress && (
            <LiquidGlassButton
              icon="arrow-left"
              onPress={onBackPress}
              size={40}
              iconSize={24}
              style={styles.buttonSpacing}
            />
          )}
          <LiquidGlassButton
            icon="menu"
            onPress={onMenuPress}
            size={40}
            iconSize={24}
          />
        </View>

        <Image
          source={require('@/assets/logo-plano.png')}
          style={styles.logo}
          resizeMode="contain"
        />

        {/* Liquid Glass action button */}
        {onActionPress && (
          <LiquidGlassButton
            icon="chart-line"
            onPress={onActionPress}
            size={40}
            iconSize={24}
          />
        )}
        {!onActionPress && <View style={{ width: 40 }} />}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    position: 'relative',
    zIndex: 10,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255, 255, 255, 0.1)',
  },
  blur: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
  },
  content: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: spacing.lg,
    paddingTop: 60,
    paddingBottom: spacing.md,
  },
  leftSection: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  buttonSpacing: {
    marginRight: 8,
  },
  logo: {
    height: 32,
    width: 120,
  },
});

export default ChatHeader;
