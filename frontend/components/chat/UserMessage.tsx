import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import Animated from 'react-native-reanimated';
import { useFirstMessageAnimation } from '@/lib/chat';
import { colors, spacing, borderRadius, typography } from '@/theme';

interface Message {
  id?: string | number;
  role: string;
  content: string;
  created_at?: string;
}

interface UserMessageProps {
  message: Message;
  index: number;
}

/**
 * User message bubble component.
 * Animates with fade-in and slide for the first message in a new chat (v0 pattern).
 */
export function UserMessage({ message, index }: UserMessageProps) {
  const isFirstUserMessage = index === 0;

  // Get animation props for first message
  const { style: animationStyle, ref, onLayout } = useFirstMessageAnimation({
    disabled: !isFirstUserMessage,
  });

  return (
    <Animated.View
      ref={ref}
      onLayout={onLayout}
      style={[styles.container, animationStyle]}
    >
      <View style={styles.bubble}>
        <Text style={styles.text}>{message.content}</Text>
      </View>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'flex-end',
    marginBottom: spacing.md,
  },
  bubble: {
    maxWidth: '80%',
    backgroundColor: colors.userBubble,
    borderRadius: borderRadius.xl,
    borderBottomRightRadius: borderRadius.xs,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm + 2,
  },
  text: {
    ...typography.bodyMedium,
    color: colors.text,
  },
});

export default UserMessage;
