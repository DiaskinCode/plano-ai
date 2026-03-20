import { useCallback } from 'react';
import {
  useAnimatedProps,
  useAnimatedScrollHandler,
} from 'react-native-reanimated';
import { NativeSyntheticEvent, NativeScrollEvent } from 'react-native';
import { useMessageList } from '../MessageListProvider';
import { useKeyboardState } from '../../keyboard';
import { useComposerHeight } from '../ComposerHeightProvider';

interface ContentSizeChangeEvent {
  width: number;
  height: number;
}

/**
 * Hook that provides animated props and handlers for the message list.
 * Returns everything needed to make LegendList work with the chat system.
 *
 * Features:
 * - Animated contentInset based on blank size, composer height, and keyboard
 * - Scroll tracking for isAtEnd detection
 * - Content size change handling
 */
export function useMessageListProps() {
  const {
    listRef,
    blankSize,
    scrollOffset,
    contentHeight,
    scrollHeight,
    isAtEnd,
  } = useMessageList();

  const { height: keyboardHeight } = useKeyboardState();
  const { composerHeight } = useComposerHeight();

  /**
   * Animated props for contentInset.
   * This is the key to floating content and making room for composer.
   */
  const animatedProps = useAnimatedProps(() => {
    return {
      contentInset: {
        top: 0,
        left: 0,
        right: 0,
        // Bottom inset = blank size + composer + keyboard
        bottom:
          blankSize.value + composerHeight.value + keyboardHeight.value,
      },
      // Also set contentOffset to prevent iOS from auto-adjusting
      automaticallyAdjustContentInsets: false,
    };
  });

  /**
   * Scroll handler to track scroll position.
   */
  const scrollHandler = useAnimatedScrollHandler({
    onScroll: (event) => {
      scrollOffset.value = event.contentOffset.y;

      // Calculate if we're at the end
      const distanceFromEnd =
        contentHeight.value - event.contentOffset.y - scrollHeight.value;
      isAtEnd.value = distanceFromEnd < 50;
    },
  });

  /**
   * Handle content size changes.
   */
  const onContentSizeChange = useCallback(
    (width: number, height: number) => {
      contentHeight.value = height;
    },
    [contentHeight]
  );

  /**
   * Handle layout to track scroll view height.
   */
  const onLayout = useCallback(
    (event: { nativeEvent: { layout: { height: number } } }) => {
      scrollHeight.value = event.nativeEvent.layout.height;
    },
    [scrollHeight]
  );

  return {
    animatedProps,
    ref: listRef,
    onScroll: scrollHandler,
    onContentSizeChange,
    onLayout,
  };
}

export default useMessageListProps;
