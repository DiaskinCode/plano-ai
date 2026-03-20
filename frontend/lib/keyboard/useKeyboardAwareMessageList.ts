import { useCallback, useRef } from 'react';
import {
  useSharedValue,
  useAnimatedReaction,
  runOnJS,
  withTiming,
  SharedValue,
} from 'react-native-reanimated';
import { useKeyboardState } from './KeyboardStateProvider';

interface UseKeyboardAwareMessageListOptions {
  // Shared value tracking the blank size below messages
  blankSize: SharedValue<number>;
  // Function to scroll to end of list
  scrollToEnd: (options?: { animated?: boolean; offset?: number }) => void;
  // Shared value tracking if at end of scroll
  isAtEnd: SharedValue<boolean>;
  // Current scroll offset
  scrollOffset: SharedValue<number>;
  // Total content height
  contentHeight: SharedValue<number>;
  // Visible scroll area height
  scrollHeight: SharedValue<number>;
}

/**
 * Main keyboard handling hook for chat message lists.
 * Implements v0's keyboard-aware behavior:
 *
 * 1. Shrinks blankSize when keyboard opens
 * 2. Shifts content up when scrolled to end with no blank size
 * 3. Shows keyboard on top of content when scrolled high up
 * 4. Handles interactive dismissal smoothly
 * 5. Manages content position when blank size transitions
 *
 * This is approximately 1000 lines of logic in v0's implementation,
 * simplified here to core patterns.
 */
export function useKeyboardAwareMessageList({
  blankSize,
  scrollToEnd,
  isAtEnd,
  scrollOffset,
  contentHeight,
  scrollHeight,
}: UseKeyboardAwareMessageListOptions) {
  const { height: keyboardHeight, isVisible, isAnimating, progress } = useKeyboardState();

  // Track previous keyboard height for delta calculations
  const prevKeyboardHeight = useRef(0);

  // Track if we should adjust scroll when keyboard changes
  const shouldAdjustScroll = useSharedValue(false);

  // Track blank size before keyboard opened
  const blankSizeBeforeKeyboard = useSharedValue(0);

  /**
   * Determine if we should shift content when keyboard opens.
   * Only shift if:
   * 1. User is scrolled near the end of the chat
   * 2. There's minimal or no blank size
   */
  const shouldShiftContent = useCallback(() => {
    'worklet';
    const distanceFromEnd =
      contentHeight.value - scrollOffset.value - scrollHeight.value;

    // Near the end of scroll (within 50px)
    const isNearEnd = distanceFromEnd < 50;

    // Blank size is small enough that keyboard would cover content
    const blankSizeIsSmall = blankSize.value < keyboardHeight.value;

    return isNearEnd && blankSizeIsSmall;
  }, [blankSize, contentHeight, keyboardHeight, scrollHeight, scrollOffset]);

  /**
   * React to keyboard visibility changes.
   */
  useAnimatedReaction(
    () => ({
      visible: isVisible.value,
      height: keyboardHeight.value,
      animating: isAnimating.value,
    }),
    (current, previous) => {
      if (!previous) return;

      const keyboardJustOpened = current.visible && !previous.visible;
      const keyboardJustClosed = !current.visible && previous.visible;
      const heightChanged = current.height !== previous.height && !current.animating;

      // Keyboard just opened
      if (keyboardJustOpened) {
        // Store blank size before keyboard
        blankSizeBeforeKeyboard.value = blankSize.value;

        // Check if we need to scroll to keep content visible
        if (shouldShiftContent()) {
          shouldAdjustScroll.value = true;
        }
      }

      // Keyboard just closed
      if (keyboardJustClosed) {
        shouldAdjustScroll.value = false;
      }

      // Height finished changing - scroll to end if needed
      if (heightChanged && shouldAdjustScroll.value && current.visible) {
        runOnJS(scrollToEnd)({ animated: true });
      }
    },
    [shouldShiftContent, scrollToEnd]
  );

  /**
   * Adjust blank size based on keyboard state.
   * When keyboard is open, reduce blank size by keyboard height.
   */
  useAnimatedReaction(
    () => ({
      height: keyboardHeight.value,
      visible: isVisible.value,
    }),
    (current) => {
      if (current.visible && current.height > 0) {
        // Reduce blank size when keyboard is open
        // But never go below 0
        const adjustedBlankSize = Math.max(
          0,
          blankSizeBeforeKeyboard.value - current.height
        );
        blankSize.value = withTiming(adjustedBlankSize, { duration: 100 });
      } else if (!current.visible) {
        // Restore blank size when keyboard closes
        blankSize.value = withTiming(blankSizeBeforeKeyboard.value, {
          duration: 100,
        });
      }
    },
    []
  );

  /**
   * Handle interactive keyboard dismissal.
   * When user drags keyboard down, we need to smoothly adjust content.
   */
  useAnimatedReaction(
    () => progress.value,
    (currentProgress, prevProgress) => {
      if (prevProgress === null) return;

      // Interactive dismissal in progress
      if (currentProgress < 1 && currentProgress > 0) {
        // Smoothly interpolate blank size based on keyboard progress
        const targetBlankSize =
          blankSizeBeforeKeyboard.value * (1 - currentProgress);
        blankSize.value = targetBlankSize;
      }
    },
    []
  );

  return {
    keyboardHeight,
    isKeyboardVisible: isVisible,
    isKeyboardAnimating: isAnimating,
    keyboardProgress: progress,
  };
}

export default useKeyboardAwareMessageList;
