// Design tokens for PathAI - v0 inspired design system

export const colors = {
  // Backgrounds
  bg: '#000000',
  background: '#000000', // Alias for bg
  surface: '#1A1A1A',
  card: '#1A1A1A', // Alias for surface
  surfaceElevated: '#2A2A2A',
  surfacePressed: '#3A3A3A',

  // Borders
  border: '#3E3E3E',
  borderSubtle: '#2E2E2E',

  // Text
  text: '#FFFFFF',
  textSecondary: '#8E8E8E',
  textTertiary: '#6E6E6E',
  textInverse: '#000000',

  // Primary (accent)
  primary: '#5B6AFF',
  primaryHover: '#4A59E8',
  primaryPressed: '#3948D1',
  primarySubtle: 'rgba(91, 106, 255, 0.15)',
  primaryLight: 'rgba(91, 106, 255, 0.1)',

  // Semantic colors
  success: '#34C759',
  successSubtle: 'rgba(52, 199, 89, 0.15)',
  successLight: 'rgba(52, 199, 89, 0.1)',
  warning: '#FF9500',
  warningSubtle: 'rgba(255, 149, 0, 0.15)',
  warningLight: 'rgba(255, 149, 0, 0.1)',
  error: '#FF3B30',
  errorSubtle: 'rgba(255, 59, 48, 0.15)',
  errorLight: 'rgba(255, 59, 48, 0.1)',
  danger: '#EF4444',
  dangerSubtle: 'rgba(239, 68, 68, 0.15)',
  info: '#3B82F6',
  infoSubtle: 'rgba(59, 130, 246, 0.15)',

  // Additional colors
  purple: '#AF52DE',

  // Chat specific
  userBubble: '#3A3A3A',
  aiBubble: '#1A1A1A',

  // Overlay
  overlay: 'rgba(0, 0, 0, 0.5)',
  overlayLight: 'rgba(0, 0, 0, 0.3)',

  // Glass effect (basic)
  glass: 'rgba(255, 255, 255, 0.05)',
  glassBorder: 'rgba(255, 255, 255, 0.1)',

  // Liquid Glass effects (v0 inspired)
  liquidGlass: {
    // Base glass with higher opacity for interactive elements
    base: 'rgba(255, 255, 255, 0.03)',
    hover: 'rgba(255, 255, 255, 0.08)',
    pressed: 'rgba(255, 255, 255, 0.12)',

    // Progressive blur intensities
    blurLight: 20,
    blurMedium: 40,
    blurHeavy: 60,
    blurIntense: 80,

    // Glass borders with subtle shimmer - cleaner white
    borderLight: 'rgba(255, 255, 255, 0.08)',
    borderMedium: 'rgba(255, 255, 255, 0.12)',
    borderHeavy: 'rgba(255, 255, 255, 0.2)',

    // Glass overlays - neutral black
    overlayLight: 'rgba(0, 0, 0, 0.2)',
    overlayMedium: 'rgba(0, 0, 0, 0.4)',
    overlayHeavy: 'rgba(0, 0, 0, 0.7)',
  },
} as const;

export const spacing = {
  xxs: 2,
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
  xxl: 48,
  xxxl: 64,
} as const;

export const borderRadius = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 20,
  xxl: 24,
  full: 9999,
} as const;

export const typography = {
  // Display
  displayLarge: {
    fontSize: 34,
    fontWeight: '700' as const,
    lineHeight: 41,
    letterSpacing: 0.25,
  },
  displayMedium: {
    fontSize: 28,
    fontWeight: '700' as const,
    lineHeight: 34,
    letterSpacing: 0,
  },
  displaySmall: {
    fontSize: 24,
    fontWeight: '600' as const,
    lineHeight: 29,
    letterSpacing: 0,
  },

  // Headlines
  headlineLarge: {
    fontSize: 22,
    fontWeight: '600' as const,
    lineHeight: 28,
    letterSpacing: 0,
  },
  headlineMedium: {
    fontSize: 20,
    fontWeight: '600' as const,
    lineHeight: 25,
    letterSpacing: 0.15,
  },
  headlineSmall: {
    fontSize: 17,
    fontWeight: '600' as const,
    lineHeight: 22,
    letterSpacing: -0.41,
  },

  // Body
  bodyLarge: {
    fontSize: 17,
    fontWeight: '400' as const,
    lineHeight: 22,
    letterSpacing: -0.41,
  },
  bodyMedium: {
    fontSize: 15,
    fontWeight: '400' as const,
    lineHeight: 20,
    letterSpacing: -0.24,
  },
  bodySmall: {
    fontSize: 13,
    fontWeight: '400' as const,
    lineHeight: 18,
    letterSpacing: -0.08,
  },

  // Labels
  labelLarge: {
    fontSize: 15,
    fontWeight: '500' as const,
    lineHeight: 20,
    letterSpacing: -0.24,
  },
  labelMedium: {
    fontSize: 13,
    fontWeight: '500' as const,
    lineHeight: 18,
    letterSpacing: -0.08,
  },
  labelSmall: {
    fontSize: 11,
    fontWeight: '500' as const,
    lineHeight: 13,
    letterSpacing: 0.07,
  },

  // Caption
  caption: {
    fontSize: 12,
    fontWeight: '400' as const,
    lineHeight: 16,
    letterSpacing: 0,
  },
} as const;

export const shadows = {
  sm: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.18,
    shadowRadius: 1.0,
    elevation: 1,
  },
  md: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.23,
    shadowRadius: 2.62,
    elevation: 4,
  },
  lg: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.30,
    shadowRadius: 4.65,
    elevation: 8,
  },
  xl: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.37,
    shadowRadius: 7.49,
    elevation: 12,
  },
} as const;

export const animation = {
  duration: {
    instant: 100,
    fast: 200,
    normal: 300,
    slow: 500,
    verySlow: 800,
  },
  easing: {
    // Standard easing curves
    standard: 'cubic-bezier(0.4, 0.0, 0.2, 1)',
    decelerate: 'cubic-bezier(0.0, 0.0, 0.2, 1)',
    accelerate: 'cubic-bezier(0.4, 0.0, 1, 1)',
    // iOS native feeling
    spring: { damping: 15, stiffness: 150, mass: 1 },
    springBouncy: { damping: 10, stiffness: 150, mass: 1 },
    springStiff: { damping: 20, stiffness: 300, mass: 1 },
  },
  // Liquid Glass animation timings (v0 inspired)
  liquidGlass: {
    // Message fade-in stagger timing (32ms between elements)
    messageFadeStagger: 32,
    messageFadeDuration: 500,
    // Batch size for staggered animations
    staggerBatchSize: 2,
    staggerQueueThreshold: 10,
    // First message animation
    firstMessageDuration: 350,
    // Glass morphing
    morphDuration: 300,
    morphSpring: { damping: 18, stiffness: 200, mass: 0.8 },
  },
} as const;

export type Colors = typeof colors;
export type Spacing = typeof spacing;
export type BorderRadius = typeof borderRadius;
export type Typography = typeof typography;
export type Shadows = typeof shadows;
export type Animation = typeof animation;
