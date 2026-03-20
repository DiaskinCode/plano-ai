// Theme exports - v0 inspired design system
export * from './tokens';
export * from './themes/dark';

// Note: react-native-unistyles v3 requires proper NitroModules setup
// For now, use regular RN StyleSheet until native modules are configured
import { StyleSheet as RNStyleSheet } from 'react-native';
export const StyleSheet = RNStyleSheet;
export const breakpoints = {
  xs: 0,
  sm: 380,
  md: 428,
  lg: 768,
  xl: 1024,
};
export const themes = {};

// Re-export commonly used tokens for convenience
import { colors, spacing, borderRadius, typography, shadows, animation } from './tokens';

export const theme = {
  colors,
  spacing,
  borderRadius,
  typography,
  shadows,
  animation,
};
