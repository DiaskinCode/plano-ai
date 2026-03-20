import React, { useCallback, useEffect } from 'react';
import { View, StyleSheet } from 'react-native';
import { LegendList } from '@legendapp/list';
import Animated, {
  useAnimatedProps,
  useAnimatedScrollHandler,
} from 'react-native-reanimated';
import {
  useMessageList,
  useMessageListProps,
  useScrollWhenComposerSizeUpdates,
  useInitialScrollToEnd,
} from '@/lib/chat';
import { useKeyboardAwareMessageList, useKeyboardState } from '@/lib/keyboard';
import { useComposerHeight } from '@/lib/chat/ComposerHeightProvider';
import { colors, spacing } from '@/theme';
import UserMessage from './UserMessage';
import AssistantMessage from './AssistantMessage';

// Create animated version of LegendList
const AnimatedLegendList = Animated.createAnimatedComponent(LegendList);

interface Message {
  id?: string | number;
  role: 'user' | 'assistant' | 'optimistic-placeholder';
  content: string;
  created_at?: string;
}

interface MessagesListProps {
  messages: Message[];
  isStreaming?: boolean;
}

/**
 * Messages list component using LegendList (v0 pattern).
 * Features:
 * - Virtualized list with dynamic heights
 * - Animated contentInset for floating content
 * - Keyboard-aware scrolling
 * - Auto-scroll on new messages
 * - Initial scroll to end for existing chats
 */
export function MessagesList({ messages, isStreaming = false }: MessagesListProps) {
  const {
    listRef,
    blankSize,
    scrollOffset,
    contentHeight,
    scrollHeight,
    isAtEnd,
    scrollToEnd,
    lastMessageIndex,
  } = useMessageList();

  const { height: keyboardHeight } = useKeyboardState();
  const { composerHeight } = useComposerHeight();

  // Apply keyboard-aware behavior
  useKeyboardAwareMessageList({
    blankSize,
    scrollToEnd,
    isAtEnd,
    scrollOffset,
    contentHeight,
    scrollHeight,
  });

  // Auto-scroll when composer size changes
  useScrollWhenComposerSizeUpdates();

  // Initial scroll to end for existing chats
  const { hasScrolledToEnd } = useInitialScrollToEnd({
    hasMessages: messages.length > 0,
  });

  // Update last message index
  useEffect(() => {
    lastMessageIndex.value = messages.length - 1;
  }, [messages.length, lastMessageIndex]);

  // Animated props for contentInset
  const animatedProps = useAnimatedProps(() => ({
    contentInset: {
      top: 0,
      left: 0,
      right: 0,
      bottom: blankSize.value + composerHeight.value + keyboardHeight.value,
    },
    automaticallyAdjustContentInsets: false,
  }));

  // Scroll handler to track position
  const scrollHandler = useAnimatedScrollHandler({
    onScroll: (event) => {
      scrollOffset.value = event.contentOffset.y;
      const distanceFromEnd =
        contentHeight.value - event.contentOffset.y - scrollHeight.value;
      isAtEnd.value = distanceFromEnd < 50;
    },
  });

  // Content size change handler
  const onContentSizeChange = useCallback(
    (width: number, height: number) => {
      contentHeight.value = height;
    },
    [contentHeight]
  );

  // Layout handler
  const onLayout = useCallback(
    (event: { nativeEvent: { layout: { height: number } } }) => {
      scrollHeight.value = event.nativeEvent.layout.height;
    },
    [scrollHeight]
  );

  // Render message based on role
  const renderItem = useCallback(
    ({ item, index }: { item: Message; index: number }) => {
      const isLast = index === messages.length - 1;

      if (item.role === 'user') {
        return (
          <UserMessage
            message={item}
            index={index}
          />
        );
      }

      if (item.role === 'assistant') {
        return (
          <AssistantMessage
            message={item}
            index={index}
            isStreaming={isStreaming && isLast}
            isLast={isLast}
          />
        );
      }

      if (item.role === 'optimistic-placeholder') {
        return (
          <AssistantMessage
            message={{ ...item, content: '...' }}
            index={index}
            isStreaming={true}
            isLast={isLast}
          />
        );
      }

      return null;
    },
    [messages.length, isStreaming]
  );

  // Key extractor
  const keyExtractor = useCallback(
    (item: Message, index: number) => item.id?.toString() || index.toString(),
    []
  );

  return (
    <View style={styles.container}>
      <AnimatedLegendList
        ref={listRef}
        data={messages}
        renderItem={renderItem}
        keyExtractor={keyExtractor}
        animatedProps={animatedProps}
        onScroll={scrollHandler}
        onContentSizeChange={onContentSizeChange}
        onLayout={onLayout}
        contentContainerStyle={styles.contentContainer}
        showsVerticalScrollIndicator={false}
        scrollEnabled={true}
        keyboardShouldPersistTaps="handled"
        keyboardDismissMode="interactive"
        // Performance optimizations
        estimatedItemSize={100}
        recycleItems={true}
        // Avoid average calculation issues with dynamic heights
        enableAverages={false}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  contentContainer: {
    padding: spacing.md,
    paddingBottom: spacing.xxl,
  },
});

export default MessagesList;
