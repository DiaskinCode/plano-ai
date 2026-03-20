import React, { useState, Children, useCallback } from 'react';
import { Text, TextStyle, StyleProp } from 'react-native';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withTiming,
  runOnJS,
} from 'react-native-reanimated';
import { useTextFadePool, createUsePool } from './usePool';
import { useTextStagger } from './useStaggeredAnimation';
import { DURATIONS } from './constants';

// Create a separate pool specifically for text fade with smaller limit
const useTextWordPool = createUsePool(4);

interface TextFadeInProps {
  text: string;
  onFadedIn?: () => void;
  style?: StyleProp<TextStyle>;
}

/**
 * Single text segment with fade-in animation.
 */
function TextFadeIn({ text, onFadedIn, style }: TextFadeInProps) {
  const opacity = useSharedValue(0);

  const startAnimation = useCallback(() => {
    opacity.value = withTiming(1, { duration: DURATIONS.fast }, () => {
      if (onFadedIn) {
        runOnJS(onFadedIn)();
      }
    });
  }, [onFadedIn, opacity]);

  useTextStagger(startAnimation);

  const animatedStyle = useAnimatedStyle(() => ({
    opacity: opacity.value,
  }));

  return (
    <Animated.Text style={[style, animatedStyle]}>{text}</Animated.Text>
  );
}

interface TextFadeInStaggeredProps {
  text: string;
  style?: StyleProp<TextStyle>;
}

/**
 * Staggered text fade-in using pool management.
 * Each word fades in sequentially with pool limiting.
 */
function TextFadeInStaggered({ text, style }: TextFadeInStaggeredProps) {
  const { isActive, evict } = useTextWordPool();

  if (!isActive) {
    // Render text directly while waiting in queue
    return <Text style={style}>{text}</Text>;
  }

  return <TextFadeIn text={text} onFadedIn={evict} style={style} />;
}

interface AnimatedFadeInTextProps {
  text: string;
  style?: StyleProp<TextStyle>;
}

/**
 * Splits text into words and animates each word with staggered fade-in.
 */
function AnimatedFadeInText({ text, style }: AnimatedFadeInTextProps) {
  const chunks = text.split(' ');

  return (
    <>
      {chunks.map((chunk, i) => (
        <TextFadeInStaggered
          key={`${i}-${chunk}`}
          text={i < chunks.length - 1 ? chunk + ' ' : chunk}
          style={style}
        />
      ))}
    </>
  );
}

interface TextFadeInStaggeredIfStreamingProps {
  children: React.ReactNode;
  isStreaming: boolean;
  style?: StyleProp<TextStyle>;
}

/**
 * Main component for streaming text fade-in (v0 pattern).
 * Wraps text content and applies staggered fade-in during streaming.
 * After streaming completes, renders text directly.
 *
 * Features:
 * - Chunks text into words for individual animation
 * - Uses pool to limit concurrent animations (max 4 words at once)
 * - Staggered delay between word animations
 * - Tracks which content has been animated to prevent re-animation
 */
export function TextFadeInStaggeredIfStreaming({
  children,
  isStreaming,
  style,
}: TextFadeInStaggeredIfStreamingProps) {
  const { isActive } = useTextFadePool();
  // Capture streaming state at mount to determine if we should animate
  const [shouldFade] = useState(isActive && isStreaming);

  if (!shouldFade || !children) {
    return <Text style={style}>{children}</Text>;
  }

  // Process children to apply fade animation to text
  const processedChildren = Children.map(children, (child, i) => {
    if (typeof child === 'string') {
      return <AnimatedFadeInText key={i} text={child} style={style} />;
    }
    return child;
  });

  return <>{processedChildren}</>;
}

interface DisableFadeContextType {
  isFadeDisabled: boolean;
}

const DisableFadeContext = React.createContext<DisableFadeContextType>({
  isFadeDisabled: false,
});

/**
 * Provider to disable fade animations for already-seen content.
 * Wrap content that shouldn't re-animate when component remounts.
 */
export function DisableFadeProvider({
  children,
  disabled = true,
}: {
  children: React.ReactNode;
  disabled?: boolean;
}) {
  return (
    <DisableFadeContext.Provider value={{ isFadeDisabled: disabled }}>
      {children}
    </DisableFadeContext.Provider>
  );
}

/**
 * Hook to check if fade animations should be disabled.
 */
export function useDisableFadeContext() {
  const context = React.useContext(DisableFadeContext);
  return context.isFadeDisabled;
}

export default TextFadeInStaggeredIfStreaming;
