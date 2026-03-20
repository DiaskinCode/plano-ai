import { colors, spacing, borderRadius, typography, shadows, animation } from '../tokens';

export const darkTheme = {
  colors,
  spacing,
  borderRadius,
  typography,
  shadows,
  animation,

  // Semantic mappings for components
  components: {
    // Screen backgrounds
    screenBg: colors.bg,

    // Cards
    card: {
      bg: colors.surface,
      bgElevated: colors.surfaceElevated,
      border: colors.border,
      borderRadius: borderRadius.lg,
    },

    // Buttons
    button: {
      primary: {
        bg: colors.primary,
        bgPressed: colors.primaryPressed,
        text: colors.text,
      },
      secondary: {
        bg: colors.surfaceElevated,
        bgPressed: colors.surfacePressed,
        text: colors.text,
      },
      ghost: {
        bg: 'transparent',
        bgPressed: colors.glass,
        text: colors.primary,
      },
      danger: {
        bg: colors.danger,
        bgPressed: '#D93636',
        text: colors.text,
      },
    },

    // Text input
    input: {
      bg: colors.surfaceElevated,
      border: colors.border,
      borderFocused: colors.primary,
      placeholder: colors.textTertiary,
      text: colors.text,
      borderRadius: borderRadius.md,
    },

    // Chat
    chat: {
      userBubble: {
        bg: colors.userBubble,
        text: colors.text,
      },
      aiBubble: {
        bg: colors.aiBubble,
        border: colors.border,
        text: colors.text,
      },
      composer: {
        bg: colors.glass,
        border: colors.glassBorder,
      },
    },

    // Tab bar
    tabBar: {
      bg: colors.glass,
      border: colors.glassBorder,
      active: colors.primary,
      inactive: colors.textSecondary,
    },

    // Modal/Sheet
    modal: {
      bg: colors.surface,
      overlay: colors.overlay,
      border: colors.border,
    },

    // Task card
    task: {
      bg: colors.surface,
      border: colors.border,
      priority: {
        high: colors.danger,
        medium: colors.warning,
        low: colors.success,
      },
    },

    // Progress
    progress: {
      bg: colors.surfaceElevated,
      fill: colors.primary,
      success: colors.success,
    },
  },
} as const;

export type DarkTheme = typeof darkTheme;
