import React, { useState, useCallback } from 'react';
import {
  View,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Platform,
} from 'react-native';
import { BlurView } from 'expo-blur';
import { KeyboardStickyView } from '@/lib/keyboard';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import Animated, {
  useAnimatedStyle,
  withTiming,
  useSharedValue,
} from 'react-native-reanimated';
import { useComposerHeight, useSyncLayoutHandler } from '@/lib/chat';
import { colors, spacing, borderRadius } from '@/theme';

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

  return (
    <KeyboardStickyView
      style={styles.stickyContainer}
      offset={{ closed: TAB_BAR_HEIGHT, opened: -spacing.sm }}
    >
      <View
        ref={ref}
        onLayout={onLayout}
        style={[
          styles.container,
          { paddingBottom: spacing.md },
        ]}
      >
        {/* Glass background */}
        <BlurView intensity={80} tint="dark" style={styles.blurBackground} />

        {/* Inner content */}
        <View style={styles.innerContainer}>
          {/* Input container with glass effect */}
          <View style={[styles.inputWrapper, isFocused && styles.inputWrapperFocused]}>
            <TextInput
              style={styles.input}
              value={value}
              onChangeText={onChangeText}
              placeholder={placeholder}
              placeholderTextColor={colors.textTertiary}
              multiline
              maxLength={4000}
              onFocus={() => setIsFocused(true)}
              onBlur={() => setIsFocused(false)}
              onSubmitEditing={handleSend}
              blurOnSubmit={false}
              editable={!isLoading}
              returnKeyType="send"
            />
          </View>

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
  stickyContainer: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    zIndex: 1000,
  },
  container: {
    paddingHorizontal: spacing.md,
    paddingTop: spacing.sm,
  },
  blurBackground: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
  },
  innerContainer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    gap: spacing.sm,
  },
  inputWrapper: {
    flex: 1,
    backgroundColor: colors.glass,
    borderWidth: 1,
    borderColor: colors.glassBorder,
    borderRadius: borderRadius.xl,
    paddingHorizontal: spacing.md,
    paddingVertical: Platform.select({ ios: spacing.sm + 2, android: spacing.xs }),
    minHeight: 44,
    maxHeight: 120,
    justifyContent: 'center',
  },
  inputWrapperFocused: {
    borderColor: colors.primary,
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
    backgroundColor: colors.glass,
    borderWidth: 1,
    borderColor: colors.glassBorder,
    justifyContent: 'center',
    alignItems: 'center',
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
  },
  sendButtonDisabled: {
    backgroundColor: colors.surfaceElevated,
    opacity: 0.5,
  },
});

export default Composer;
