import { Easing } from 'react-native-reanimated';

// Animation durations in milliseconds
export const DURATIONS = {
  instant: 100,
  fast: 200,
  normal: 300,
  slow: 500,
  verySlow: 800,
  stagger: 32, // Delay between staggered elements
} as const;

// Spring configurations for Reanimated
export const SPRING_CONFIGS = {
  // Smooth, iOS-native feeling
  default: {
    damping: 15,
    stiffness: 150,
    mass: 1,
  },
  // Bouncy, playful feeling
  bouncy: {
    damping: 10,
    stiffness: 150,
    mass: 1,
  },
  // Stiff, snappy feeling
  stiff: {
    damping: 20,
    stiffness: 300,
    mass: 1,
  },
  // For message animations (v0 style)
  message: {
    damping: 18,
    stiffness: 180,
    mass: 1,
  },
  // For keyboard transitions
  keyboard: {
    damping: 20,
    stiffness: 250,
    mass: 1,
  },
} as const;

// Timing configurations
export const TIMING_CONFIGS = {
  fadeIn: {
    duration: DURATIONS.normal,
    easing: Easing.out(Easing.cubic),
  },
  fadeOut: {
    duration: DURATIONS.fast,
    easing: Easing.in(Easing.cubic),
  },
  slideIn: {
    duration: DURATIONS.normal,
    easing: Easing.out(Easing.cubic),
  },
  scale: {
    duration: DURATIONS.fast,
    easing: Easing.out(Easing.cubic),
  },
} as const;

// Pool limits for staggered animations
export const POOL_LIMITS = {
  // Max concurrent message fade animations
  messageFade: 2,
  // Max concurrent text word animations
  textFade: 4,
  // Max concurrent list item animations
  listItem: 3,
} as const;

// Animation progress states
export const ANIMATION_STATES = {
  idle: -1,
  animating: 0,
  complete: 1,
} as const;

export type SpringConfig = typeof SPRING_CONFIGS[keyof typeof SPRING_CONFIGS];
export type TimingConfig = typeof TIMING_CONFIGS[keyof typeof TIMING_CONFIGS];
