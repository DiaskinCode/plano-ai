import React, { createContext, useContext } from 'react';
import { View, Text, StyleSheet } from 'react-native';
import Animated, {
  useAnimatedStyle,
  withTiming,
} from 'react-native-reanimated';
import { useNewMessageAnimation, useMessageBlankSize } from '@/lib/chat';
import { TextFadeInStaggeredIfStreaming } from '@/lib/animations';
import { colors, spacing, borderRadius, typography } from '@/theme';

interface Message {
  id?: string | number;
  role: string;
  content: string;
  created_at?: string;
}

interface AssistantMessageProps {
  message: Message;
  index: number;
  isStreaming?: boolean;
  isLast?: boolean;
}

// Context to pass streaming state to text components
const MessageContext = createContext<{ isStreaming: boolean }>({
  isStreaming: false,
});

export function useMessageContext() {
  return useContext(MessageContext);
}

/**
 * Assistant message bubble component.
 * Features (v0 patterns):
 * - Fades in after user message animation completes
 * - Staggered text fade-in during streaming
 * - Blank size calculation for floating content
 */
export function AssistantMessage({
  message,
  index,
  isStreaming = false,
  isLast = false,
}: AssistantMessageProps) {
  const isFirstAssistantMessage = index === 1;
  const { didUserMessageAnimate } = useNewMessageAnimation();

  // Calculate blank size for last message
  const { ref, onLayout } = useMessageBlankSize({
    index,
    isLast,
  });

  // Fade in after user message animation (for first assistant message)
  const fadeStyle = useAnimatedStyle(() => {
    if (!isFirstAssistantMessage) {
      return { opacity: 1 };
    }

    // Wait for user message to finish animating
    return {
      opacity: didUserMessageAnimate.value
        ? withTiming(1, { duration: 350 })
        : 0,
    };
  });

  // Parse content into paragraphs for staggered animation
  const paragraphs = message.content.split('\n').filter(Boolean);

  return (
    <MessageContext.Provider value={{ isStreaming }}>
      <Animated.View
        ref={ref}
        onLayout={onLayout}
        style={[styles.container, fadeStyle]}
      >
        <View style={styles.bubble}>
          {paragraphs.map((paragraph, i) => (
            <TextFadeInStaggeredIfStreaming
              key={i}
              isStreaming={isStreaming}
              style={styles.text}
            >
              {paragraph}
              {i < paragraphs.length - 1 ? '\n' : ''}
            </TextFadeInStaggeredIfStreaming>
          ))}
          {paragraphs.length === 0 && (
            <Text style={styles.text}>{message.content || '...'}</Text>
          )}
        </View>
      </Animated.View>
    </MessageContext.Provider>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'flex-start',
    marginBottom: spacing.md,
  },
  bubble: {
    maxWidth: '85%',
    backgroundColor: colors.aiBubble,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: borderRadius.xl,
    borderBottomLeftRadius: borderRadius.xs,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm + 2,
  },
  text: {
    ...typography.bodyMedium,
    color: colors.text,
    lineHeight: 22,
  },
});

export default AssistantMessage;
