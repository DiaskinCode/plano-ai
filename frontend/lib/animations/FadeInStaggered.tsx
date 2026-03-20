import React, { useCallback, useState } from 'react';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withTiming,
  runOnJS,
} from 'react-native-reanimated';
import { ViewStyle, StyleProp } from 'react-native';
import { useMessageFadePool } from './usePool';
import { useMessageStagger } from './useStaggeredAnimation';
import { DURATIONS, TIMING_CONFIGS } from './constants';

interface FadeInProps {
  children: React.ReactNode;
  onFadedIn?: () => void;
  duration?: number;
  style?: StyleProp<ViewStyle>;
}

/**
 * Basic fade-in animation component.
 * Fades in children with configurable duration.
 */
export function FadeIn({
  children,
  onFadedIn,
  duration = DURATIONS.normal,
  style,
}: FadeInProps) {
  const opacity = useSharedValue(0);

  const startAnimation = useCallback(() => {
    opacity.value = withTiming(1, { duration }, () => {
      if (onFadedIn) {
        runOnJS(onFadedIn)();
      }
    });
  }, [duration, onFadedIn, opacity]);

  useMessageStagger(startAnimation);

  const animatedStyle = useAnimatedStyle(() => ({
    opacity: opacity.value,
  }));

  return (
    <Animated.View style={[animatedStyle, style]}>{children}</Animated.View>
  );
}

interface FadeInStaggeredProps {
  children: React.ReactNode;
  style?: StyleProp<ViewStyle>;
}

/**
 * Staggered fade-in animation component.
 * Uses pool management to limit concurrent animations (v0 pattern).
 * When an animation completes, it evicts itself from the pool,
 * allowing the next queued animation to start.
 */
export function FadeInStaggered({ children, style }: FadeInStaggeredProps) {
  const { isActive, evict } = useMessageFadePool();

  if (!isActive) {
    // Render children without animation while waiting in queue
    return <>{children}</>;
  }

  return (
    <FadeIn onFadedIn={evict} style={style}>
      {children}
    </FadeIn>
  );
}

interface FadeInIfStreamingProps {
  children: React.ReactNode;
  isStreaming: boolean;
  style?: StyleProp<ViewStyle>;
}

/**
 * Conditionally applies staggered fade-in animation only while streaming.
 * Once streaming is complete, renders children directly.
 */
export function FadeInIfStreaming({
  children,
  isStreaming,
  style,
}: FadeInIfStreamingProps) {
  const [shouldAnimate] = useState(isStreaming);

  if (!shouldAnimate) {
    return <>{children}</>;
  }

  return <FadeInStaggered style={style}>{children}</FadeInStaggered>;
}

interface FadeInSlideProps {
  children: React.ReactNode;
  from?: 'bottom' | 'top' | 'left' | 'right';
  distance?: number;
  duration?: number;
  delay?: number;
  style?: StyleProp<ViewStyle>;
}

/**
 * Fade-in with slide animation.
 * Content fades in while sliding from a specified direction.
 */
export function FadeInSlide({
  children,
  from = 'bottom',
  distance = 20,
  duration = DURATIONS.normal,
  delay = 0,
  style,
}: FadeInSlideProps) {
  const opacity = useSharedValue(0);
  const translateX = useSharedValue(from === 'left' ? -distance : from === 'right' ? distance : 0);
  const translateY = useSharedValue(from === 'bottom' ? distance : from === 'top' ? -distance : 0);

  React.useEffect(() => {
    const timeout = setTimeout(() => {
      opacity.value = withTiming(1, { duration });
      translateX.value = withTiming(0, { duration });
      translateY.value = withTiming(0, { duration });
    }, delay);

    return () => clearTimeout(timeout);
  }, [delay, distance, duration, opacity, translateX, translateY]);

  const animatedStyle = useAnimatedStyle(() => ({
    opacity: opacity.value,
    transform: [
      { translateX: translateX.value },
      { translateY: translateY.value },
    ],
  }));

  return (
    <Animated.View style={[animatedStyle, style]}>{children}</Animated.View>
  );
}

export default FadeInStaggered;
