import React, { useState, Children } from 'react';
import { Text, StyleProp, TextStyle } from 'react-native';
import Animated, {
  useAnimatedStyle,
  withDelay,
  withTiming,
  useSharedValue,
  withSequence,
  Easing,
} from 'react-native-reanimated';

// Store to track if text fade should be disabled (e.g., when scrolling fast)
let globalDisableFade = false;

export const setDisableFade = (disable: boolean) => {
  globalDisableFade = disable;
};

export const useDisableFade = () => globalDisableFade;

// Pool for managing text fade state
interface TextFadePool {
  isActive: boolean;
}

const textFadePool: TextFadePool = {
  isActive: false,
};

export const setTextFadeActive = (isActive: boolean) => {
  textFadePool.isActive = isActive;
};

export const useTextFadePool = () => textFadePool;

/**
 * Animated text component that fades in character by character
 */
function AnimatedFadeInText({ text, style }: { text: string; style?: StyleProp<TextStyle> }) {
  const opacity = useSharedValue(0);

  React.useEffect(() => {
    opacity.value = withDelay(
      0,
      withTiming(1, {
        duration: 300,
        easing: Easing.inOut(Easing.ease),
      })
    );
  }, []);

  const animatedStyle = useAnimatedStyle(() => ({
    opacity: opacity.value,
  }));

  return (
    <Animated.Text style={[style, animatedStyle]}>
      {text}
    </Animated.Text>
  );
}

/**
 * Text fade-in component that renders text with staggered fade-in effect
 */
export interface TextFadeInStaggeredProps {
  children: string | string[];
  style?: StyleProp<TextStyle>;
  isStreaming?: boolean;
}

export function TextFadeInStaggered({ children, style }: TextFadeInStaggeredProps) {
  const isDisabled = useDisableFade();
  const { isActive } = useTextFadePool();

  // Only fade if active in pool and not disabled
  const [shouldFade] = useState(isActive && !isDisabled);

  let content = children;

  if (shouldFade && children) {
    if (Array.isArray(children)) {
      content = Children.map(children, (child, i) =>
        typeof child === 'string' ? <AnimatedFadeInText key={i} text={child} style={style} /> : child,
      );
    } else if (typeof children === 'string') {
      content = <AnimatedFadeInText text={children} style={style} />;
    }
    return <>{content}</>;
  }

  // If not fading, wrap in Text with style to ensure color is applied
  return <Text style={style}>{children}</Text>;
}

/**
 * Legacy component that splits text by newlines and fades in each chunk
 */
export function FadeInStaggeredIfStreaming({
  text,
  style,
  isStreaming,
}: {
  text: string;
  style?: any;
  isStreaming?: boolean;
}) {
  if (!isStreaming) {
    return <Text style={style}>{text}</Text>;
  }

  // Split by newlines and fade in each chunk
  const chunks = text.split('\n');

  return (
    <>
      {chunks.map((chunk, i) => (
        <TextFadeInStaggered key={i} isStreaming={isStreaming} style={style}>
          {chunk + '\n'}
        </TextFadeInStaggered>
      ))}{' '}
    </>
  );
}

/**
 * Component for rendering staggered fade-in text if streaming is enabled.
 * Falls back to regular Text if not streaming.
 */
export function TextFadeInStaggeredIfStreaming({
  children,
  isStreaming = false,
  style,
}: {
  children: string | string[];
  isStreaming?: boolean;
  style?: StyleProp<TextStyle>;
}) {
  const childrenArray = Array.isArray(children) ? children : [children];

  // Always wrap in Text component
  if (!isStreaming) {
    return <Text style={style}>{childrenArray.join('')}</Text>;
  }

  return <TextFadeInStaggered isStreaming={isStreaming} style={style}>{childrenArray}</TextFadeInStaggered>;
}

/**
 * @deprecated Use TextFadeInStaggeredIfStreaming instead
 */
export default FadeInStaggeredIfStreaming;
