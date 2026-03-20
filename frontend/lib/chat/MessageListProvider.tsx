import React, { createContext, useContext, ReactNode, useRef, useCallback } from 'react';
import { useSharedValue, SharedValue } from 'react-native-reanimated';
import type { LegendListRef } from '@legendapp/list';

interface ScrollToEndOptions {
  animated?: boolean;
  offset?: number;
}

interface MessageListContextValue {
  // Reference to the LegendList component
  listRef: React.RefObject<LegendListRef<any>>;

  // Scroll state shared values
  scrollOffset: SharedValue<number>;
  contentHeight: SharedValue<number>;
  scrollHeight: SharedValue<number>;
  isAtEnd: SharedValue<boolean>;

  // Blank size for floating messages to top
  blankSize: SharedValue<number>;

  // Index of the last message (for animations)
  lastMessageIndex: SharedValue<number>;

  // Methods
  scrollToEnd: (options?: ScrollToEndOptions) => void;
  scrollToIndex: (index: number, animated?: boolean) => void;
}

const MessageListContext = createContext<MessageListContextValue | null>(null);

interface MessageListProviderProps {
  children: ReactNode;
}

/**
 * Provider for message list state and methods.
 * Manages scroll state, references, and provides scroll methods.
 */
export function MessageListProvider({ children }: MessageListProviderProps) {
  const listRef = useRef<LegendListRef<any>>(null);

  // Scroll state
  const scrollOffset = useSharedValue(0);
  const contentHeight = useSharedValue(0);
  const scrollHeight = useSharedValue(0);
  const isAtEnd = useSharedValue(true);

  // Blank size for floating content to top
  const blankSize = useSharedValue(0);

  // Track last message index for animations
  const lastMessageIndex = useSharedValue(-1);

  /**
   * Scroll to the end of the message list.
   * Uses multiple scroll calls to handle dynamic heights (v0 pattern).
   */
  const scrollToEnd = useCallback(
    ({ animated = true, offset = 0 }: ScrollToEndOptions = {}) => {
      const list = listRef.current;
      if (!list) return;

      // First scroll attempt
      list.scrollToEnd({ animated });

      // Additional scroll calls for reliability with dynamic heights
      requestAnimationFrame(() => {
        list.scrollToEnd({ animated: false });
      });

      // One more just to be safe
      setTimeout(() => {
        list.scrollToEnd({ animated: false });
      }, 16);
    },
    []
  );

  /**
   * Scroll to a specific message index.
   */
  const scrollToIndex = useCallback(
    (index: number, animated = true) => {
      const list = listRef.current;
      if (!list) return;

      list.scrollToIndex({ index, animated, viewPosition: 0 });
    },
    []
  );

  const value: MessageListContextValue = {
    listRef,
    scrollOffset,
    contentHeight,
    scrollHeight,
    isAtEnd,
    blankSize,
    lastMessageIndex,
    scrollToEnd,
    scrollToIndex,
  };

  return (
    <MessageListContext.Provider value={value}>
      {children}
    </MessageListContext.Provider>
  );
}

/**
 * Hook to access message list context.
 */
export function useMessageList(): MessageListContextValue {
  const context = useContext(MessageListContext);
  if (!context) {
    throw new Error('useMessageList must be used within MessageListProvider');
  }
  return context;
}

export default MessageListProvider;
