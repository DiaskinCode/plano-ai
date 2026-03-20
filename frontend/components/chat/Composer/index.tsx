import React, { useState, useCallback } from 'react';
import {
  View,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Platform,
} from 'react-native';
import { BlurView } from 'expo-blur';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import Animated, {
  useAnimatedStyle,
  withTiming,
  withSpring,
  useSharedValue,
  interpolate,
} from 'react-native-reanimated';
import { KeyboardStickyView } from 'react-native-keyboard-controller';
import { useComposerHeight, useSyncLayoutHandler } from '@/lib/chat';
import { colors, spacing, borderRadius } from '@/theme';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

// Tab bar height for positioning above it
const TAB_BAR_HEIGHT = Platform.OS === 'ios' ? 88 : 70;

interface ComposerProps {
  value: string;
  onChangeText: (text: string) => void;
  onSend: () => void;
  onVoiceStart?: () => void;
  onVoiceStop?: () => void;
  isRecording?: boolean;
  isLoading?: boolean;
  placeholder?: string;
}

/**
 * Floating composer with glass effect (v0 pattern).
 * Features:
 * - Floats above content with blur background
 * - Sticks to keyboard with KeyboardStickyView
 * - Animated send button
 * - Voice recording support
 */
export function Composer({
  value,
  onChangeText,
  onSend,
  onVoiceStart,
  onVoiceStop,
  isRecording = false,
  isLoading = false,
  placeholder = 'Message...',
}: ComposerProps) {
  const { composerHeight } = useComposerHeight();
  const insets = useSafeAreaInsets();

  // Track composer height for contentInset calculations
  const { ref, onLayout } = useSyncLayoutHandler((layout) => {
    composerHeight.value = layout.height;
  });

  // Input focus state for styling
  const [isFocused, setIsFocused] = useState(false);

  // Animated scale for send button
  const sendButtonScale = useSharedValue(1);

  const handleSend = useCallback(() => {
    if (value.trim() && !isLoading) {
      sendButtonScale.value = withTiming(0.9, { duration: 50 }, () => {
        sendButtonScale.value = withTiming(1, { duration: 100 });
      });
      onSend();
    }
  }, [value, isLoading, onSend, sendButtonScale]);

  const handleVoicePress = useCallback(() => {
    if (isRecording) {
      onVoiceStop?.();
    } else {
      onVoiceStart?.();
    }
  }, [isRecording, onVoiceStart, onVoiceStop]);

  // Animated style for send button
  const sendButtonAnimatedStyle = useAnimatedStyle(() => ({
    transform: [{ scale: sendButtonScale.value }],
  }));

  const canSend = value.trim().length > 0 && !isLoading;

  // Input wrapper animation for "liquid glass" effect
  const inputScale = useSharedValue(1);
  const inputAnimatedStyle = useAnimatedStyle(() => ({
    transform: [{ scale: inputScale.value }],
  }));

  const handleInputFocus = () => {
    setIsFocused(true);
    inputScale.value = withSpring(1.02, { damping: 15, stiffness: 150 });
  };

  const handleInputBlur = () => {
    setIsFocused(false);
    inputScale.value = withSpring(1, { damping: 15, stiffness: 150 });
  };

  // Keyboard animation handled by KeyboardStickyView

  return (
    <KeyboardStickyView
      offset={{ closed: -TAB_BAR_HEIGHT, opened: 0 }}
      style={[
        styles.keyboardSticky,
        { zIndex: 2000 }
      ]}
    >
      <View
        ref={ref}
        onLayout={onLayout}
        style={styles.container}
      >
        {/* Progressive blur background */}
        <BlurView intensity={100} tint="dark" style={styles.blurBackground} />

        {/* Inner content with spacing */}
        <View style={styles.innerContainer}>
          {/* Input container with liquid glass effect */}
          <Animated.View style={[{ flex: 1 }, inputAnimatedStyle]}>
            <View style={[styles.inputWrapper, isFocused && styles.inputWrapperFocused]}>
              <TextInput
                style={styles.input}
                value={value}
                onChangeText={onChangeText}
                placeholder={placeholder}
                placeholderTextColor={colors.textTertiary}
                multiline
                maxLength={4000}
                onFocus={handleInputFocus}
                onBlur={handleInputBlur}
                onSubmitEditing={handleSend}
                editable={!isLoading}
                returnKeyType="send"
              />
            </View>
          </Animated.View>

          {/* Action buttons */}
          <View style={styles.actions}>
            {/* Voice button */}
            <TouchableOpacity
              style={[
                styles.actionButton,
                isRecording && styles.recordingButton,
              ]}
              onPress={handleVoicePress}
              disabled={isLoading}
              activeOpacity={0.7}
            >
              <MaterialCommunityIcons
                name={isRecording ? 'stop-circle' : 'microphone'}
                size={22}
                color={isRecording ? colors.text : colors.textSecondary}
              />
            </TouchableOpacity>

            {/* Send button */}
            <Animated.View style={sendButtonAnimatedStyle}>
              <TouchableOpacity
                style={[
                  styles.sendButton,
                  !canSend && styles.sendButtonDisabled,
                ]}
                onPress={handleSend}
                disabled={!canSend}
                activeOpacity={0.7}
              >
                <MaterialCommunityIcons
                  name={isLoading ? 'loading' : 'arrow-up'}
                  size={20}
                  color={colors.text}
                />
              </TouchableOpacity>
            </Animated.View>
          </View>
        </View>
      </View>
    </KeyboardStickyView>
  );
}

const styles = StyleSheet.create({
  keyboardSticky: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    zIndex: 1000,
  },
  container: {
    paddingHorizontal: spacing.md,
    paddingTop: spacing.sm,
    paddingBottom: spacing.md,
  },
  blurBackground: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: colors.liquidGlass.overlayMedium,
  },
  innerContainer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    gap: spacing.sm,
  },
  inputWrapper: {
    flex: 1,
    backgroundColor: 'rgba(255, 255, 255, 0.15)',
    borderWidth: 1.5,
    borderColor: 'rgba(255, 255, 255, 0.25)',
    borderRadius: 24,
    paddingHorizontal: spacing.md,
    paddingVertical: Platform.select({ ios: spacing.sm + 2, android: spacing.xs }),
    minHeight: 44,
    maxHeight: 120,
    justifyContent: 'center',
    shadowColor: colors.primary,
    shadowOpacity: 0.15,
    shadowRadius: 8,
    shadowOffset: { width: 0, height: 2 },
  },
  inputWrapperFocused: {
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    borderColor: colors.primary,
    borderWidth: 2,
    shadowOpacity: 0.3,
    shadowRadius: 12,
  },
  input: {
    fontSize: 16,
    color: colors.text,
    lineHeight: 22,
    maxHeight: 100,
    ...Platform.select({
      ios: {},
      android: {
        paddingVertical: 8,
      },
    }),
  },
  actions: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs,
    paddingBottom: 4,
  },
  actionButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(255, 255, 255, 0.12)',
    borderWidth: 1.5,
    borderColor: 'rgba(255, 255, 255, 0.2)',
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOpacity: 0.2,
    shadowRadius: 6,
    shadowOffset: { width: 0, height: 2 },
  },
  recordingButton: {
    backgroundColor: colors.danger,
    borderColor: colors.danger,
  },
  sendButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: colors.primary,
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: colors.primary,
    shadowOpacity: 0.5,
    shadowRadius: 8,
    shadowOffset: { width: 0, height: 2 },
  },
  sendButtonDisabled: {
    backgroundColor: 'rgba(255, 255, 255, 0.08)',
    opacity: 0.4,
    shadowOpacity: 0,
  },
});

export default Composer;
