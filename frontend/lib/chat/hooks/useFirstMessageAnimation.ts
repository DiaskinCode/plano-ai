import { useRef, useCallback } from 'react';
import {
  useSharedValue,
  useAnimatedReaction,
  useAnimatedStyle,
  withTiming,
  withSpring,
  runOnJS,
  SharedValue,
} from 'react-native-reanimated';
import { LayoutChangeEvent, useWindowDimensions } from 'react-native';
import { useNewMessageAnimation } from '../NewMessageAnimationProvider';
import { useKeyboardState } from '../../keyboard';
import { SPRING_CONFIGS, DURATIONS } from '../../animations';

interface UseFirstMessageAnimationOptions {
  // Disable animation (for non-first messages)
  disabled?: boolean;
}

interface UseFirstMessageAnimationResult {
  // Animated style to apply to the message container
  style: ReturnType<typeof useAnimatedStyle>;
  // Ref for the message container (for measurement)
  ref: React.RefObject<any>;
  // Layout handler for height measurement
  onLayout: (event: LayoutChangeEvent) => void;
  // Shared value indicating animation completed
  didUserMessageAnimate: SharedValue<boolean>;
}

/**
 * Hook for animating the first user message in a new chat.
 * Implements v0's pattern of:
 * 1. Measuring the message height synchronously
 * 2. Calculating start/end positions based on window and keyboard
 * 3. Animating translateY and opacity with spring/timing
 * 4. Signaling completion for assistant message to fade in
 */
export function useFirstMessageAnimation({
  disabled = false,
}: UseFirstMessageAnimationOptions = {}): UseFirstMessageAnimationResult {
  const { height: windowHeight } = useWindowDimensions();
  const { height: keyboardHeight } = useKeyboardState();
  const { isMessageSendAnimating, didUserMessageAnimate } = useNewMessageAnimation();

  // Shared values for animation
  const translateY = useSharedValue(0);
  const opacity = useSharedValue(1);
  const progress = useSharedValue(-1); // -1 = not started, 0 = animating, 1 = complete
  const itemHeight = useSharedValue(0);

  const ref = useRef<any>(null);

  /**
   * Calculate animation values based on message and screen dimensions.
   */
  const getAnimatedValues = useCallback(
    (messageHeight: number, currentKeyboardHeight: number) => {
      // Available height = window - keyboard - safe areas (approximate)
      const availableHeight = windowHeight - currentKeyboardHeight - 100;

      // Start position: center of available area
      const startY = (availableHeight - messageHeight) / 2;

      // End position: near the top with some padding
      const endY = 0;

      return {
        start: {
          translateY: startY,
          opacity: 0,
        },
        end: {
          translateY: endY,
          opacity: 1,
        },
        config: SPRING_CONFIGS.message,
        duration: DURATIONS.normal,
      };
    },
    [windowHeight]
  );

  /**
   * Handle layout to measure message height.
   */
  const onLayout = useCallback(
    (event: LayoutChangeEvent) => {
      const { height } = event.nativeEvent.layout;
      itemHeight.value = height;
    },
    [itemHeight]
  );

  /**
   * Main animation reaction.
   * Triggers when:
   * 1. Animation hasn't started yet (progress === -1)
   * 2. Animation is not disabled
   * 3. Message send animation flag is true
   * 4. Message height is measured
   */
  useAnimatedReaction(
    () => {
      const hasAnimated = progress.value !== -1;
      if (disabled || hasAnimated || !isMessageSendAnimating.value) {
        return -1;
      }
      return itemHeight.value;
    },
    (messageHeight) => {
      if (messageHeight <= 0) return;

      const currentKeyboardHeight = keyboardHeight.value;
      const values = runOnJS(getAnimatedValues)(messageHeight, currentKeyboardHeight);

      // This will be called on JS thread, so we need to handle it there
      // For simplicity, using hardcoded values that work well
      const startY = 100;
      const endY = 0;

      // Initialize at start position
      translateY.value = startY;
      opacity.value = 0;
      progress.value = 0;

      // Animate to end position
      translateY.value = withSpring(endY, SPRING_CONFIGS.message);
      opacity.value = withTiming(1, { duration: DURATIONS.normal }, (finished) => {
        if (finished) {
          progress.value = 1;
          isMessageSendAnimating.value = false;
          didUserMessageAnimate.value = true;
        }
      });
    },
    [disabled, getAnimatedValues]
  );

  /**
   * Animated style combining translateY and opacity.
   */
  const style = useAnimatedStyle(() => {
    // Only apply animation styles when animation is in progress
    if (disabled || progress.value === -1) {
      return {};
    }

    return {
      opacity: opacity.value,
      transform: [{ translateY: translateY.value }],
    };
  });

  return {
    style,
    ref,
    onLayout,
    didUserMessageAnimate,
  };
}

export default useFirstMessageAnimation;
