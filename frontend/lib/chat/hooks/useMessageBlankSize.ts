import { useCallback, useRef, useLayoutEffect } from 'react';
import {
  useSharedValue,
  useAnimatedReaction,
  runOnJS,
} from 'react-native-reanimated';
import { LayoutChangeEvent, useWindowDimensions } from 'react-native';
import { useMessageList } from '../MessageListProvider';
import { useKeyboardState } from '../../keyboard';
import { useComposerHeight } from '../ComposerHeightProvider';

interface UseMessageBlankSizeOptions {
  // Index of this message in the list
  index: number;
  // Whether this is the last message
  isLast?: boolean;
}

interface UseMessageBlankSizeResult {
  // Ref for the message container
  ref: React.RefObject<any>;
  // Layout handler
  onLayout: (event: LayoutChangeEvent) => void;
}

/**
 * Hook for calculating and setting blank size for a message.
 * Blank size is the distance between the bottom of the last message
 * and the end of the chat - it floats content to the top of the screen.
 *
 * Calculation (v0 pattern):
 * 1. Measure assistant message height
 * 2. Measure preceding user message height
 * 3. Calculate minimum blank size to push content to top
 * 4. Adjust for keyboard open/closed states
 */
export function useMessageBlankSize({
  index,
  isLast = false,
}: UseMessageBlankSizeOptions): UseMessageBlankSizeResult {
  const { height: windowHeight } = useWindowDimensions();
  const { blankSize } = useMessageList();
  const { height: keyboardHeight, isVisible: isKeyboardVisible } = useKeyboardState();
  const { composerHeight } = useComposerHeight();

  // Track message height
  const messageHeight = useSharedValue(0);
  const ref = useRef<any>(null);

  // Store height for when keyboard is open vs closed
  const blankSizeWithKeyboard = useSharedValue(0);
  const blankSizeWithoutKeyboard = useSharedValue(0);

  /**
   * Calculate blank size to float content to top.
   */
  const calculateBlankSize = useCallback(
    (msgHeight: number, kbHeight: number, cmpHeight: number) => {
      if (msgHeight <= 0) return 0;

      // Available height = window - keyboard - composer - safe area padding
      const safeAreaPadding = 100; // Approximate for status bar + bottom
      const availableHeight = windowHeight - kbHeight - cmpHeight - safeAreaPadding;

      // Blank size = available height - message height
      // This pushes the message to the top of the available area
      const calculatedBlankSize = Math.max(0, availableHeight - msgHeight);

      return calculatedBlankSize;
    },
    [windowHeight]
  );

  /**
   * Handle layout changes.
   */
  const onLayout = useCallback(
    (event: LayoutChangeEvent) => {
      const { height } = event.nativeEvent.layout;
      messageHeight.value = height;
    },
    [messageHeight]
  );

  /**
   * Synchronous height measurement on mount (New Architecture).
   */
  useLayoutEffect(() => {
    if (ref.current?.measure) {
      ref.current.measure(
        (_x: number, _y: number, _width: number, height: number) => {
          if (height > 0) {
            messageHeight.value = height;
          }
        }
      );
    }
  }, [messageHeight]);

  /**
   * Update blank size when message height changes.
   */
  useAnimatedReaction(
    () => ({
      msgHeight: messageHeight.value,
      kbHeight: keyboardHeight.value,
      cmpHeight: composerHeight.value,
      kbVisible: isKeyboardVisible.value,
    }),
    (current) => {
      // Only calculate for last message
      if (!isLast) return;

      const { msgHeight, kbHeight, cmpHeight, kbVisible } = current;

      if (msgHeight <= 0) return;

      // Calculate blank size
      const newBlankSize = runOnJS(calculateBlankSize)(
        msgHeight,
        kbHeight,
        cmpHeight
      );

      // Store for both keyboard states
      if (kbVisible) {
        blankSizeWithKeyboard.value = newBlankSize;
      } else {
        blankSizeWithoutKeyboard.value = newBlankSize;
      }

      // Update the shared blank size
      blankSize.value = newBlankSize;
    },
    [isLast, calculateBlankSize]
  );

  return { ref, onLayout };
}

export default useMessageBlankSize;
