// Keyboard management utilities - v0 patterns

export {
  KeyboardStateProvider,
  useKeyboardState,
  useKeyboardHeight,
  useKeyboardVisible,
} from './KeyboardStateProvider';

export { useKeyboardAwareMessageList } from './useKeyboardAwareMessageList';
export { SafeKeyboardProvider } from './SafeKeyboardProvider';

// Safe re-exports from keyboard-controller (with fallbacks for Expo Go)
export {
  SafeKeyboardStickyView as KeyboardStickyView,
  SafeKeyboardAvoidingView as KeyboardAvoidingView,
} from './SafeKeyboardComponents';
