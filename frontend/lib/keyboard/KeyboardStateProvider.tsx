import React, { createContext, useContext, ReactNode, useCallback, useRef, useEffect } from 'react';
import { useSharedValue, SharedValue, runOnJS } from 'react-native-reanimated';
import { AppState, AppStateStatus, Keyboard } from 'react-native';

// Try to import from keyboard-controller, gracefully fall back if not available
let useKeyboardHandler: any = null;
let KeyboardController: any = null;
let isKeyboardControllerAvailable = false;

try {
  const keyboardControllerModule = require('react-native-keyboard-controller');
  useKeyboardHandler = keyboardControllerModule.useKeyboardHandler;
  KeyboardController = keyboardControllerModule.KeyboardController;
  isKeyboardControllerAvailable = true;
} catch (e) {
  console.warn('react-native-keyboard-controller not available, keyboard state tracking disabled');
}

interface KeyboardState {
  // Current keyboard height (animated)
  height: SharedValue<number>;
  // Whether keyboard is currently visible
  isVisible: SharedValue<boolean>;
  // Progress of keyboard animation (0 to 1)
  progress: SharedValue<number>;
  // Whether keyboard is currently animating
  isAnimating: SharedValue<boolean>;
  // Dismiss the keyboard
  dismiss: () => void;
}

const KeyboardStateContext = createContext<KeyboardState | null>(null);

interface KeyboardStateProviderProps {
  children: ReactNode;
}

// Internal provider that uses the native keyboard handler
function NativeKeyboardStateProvider({ children }: KeyboardStateProviderProps) {
  const height = useSharedValue(0);
  const isVisible = useSharedValue(false);
  const progress = useSharedValue(0);
  const isAnimating = useSharedValue(false);

  const lastEventRef = useRef<{ type: string; height: number; timestamp: number } | null>(null);
  const appStateRef = useRef<AppStateStatus>(AppState.currentState);

  useEffect(() => {
    const subscription = AppState.addEventListener('change', (nextAppState) => {
      appStateRef.current = nextAppState;
    });
    return () => subscription.remove();
  }, []);

  const isDuplicateEvent = useCallback((type: string, newHeight: number) => {
    const now = Date.now();
    const last = lastEventRef.current;
    if (last && last.type === type && last.height === newHeight && now - last.timestamp < 100) {
      return true;
    }
    lastEventRef.current = { type, height: newHeight, timestamp: now };
    return false;
  }, []);

  useKeyboardHandler(
    {
      onStart: (e: any) => {
        'worklet';
        const isDupe = runOnJS(isDuplicateEvent)('start', e.height);
        if (isDupe) return;
        isAnimating.value = true;
        if (e.height > 0) {
          isVisible.value = true;
        }
      },
      onMove: (e: any) => {
        'worklet';
        height.value = e.height;
        progress.value = e.progress;
      },
      onEnd: (e: any) => {
        'worklet';
        const isDupe = runOnJS(isDuplicateEvent)('end', e.height);
        if (isDupe) return;
        isAnimating.value = false;
        height.value = e.height;
        progress.value = e.height > 0 ? 1 : 0;
        if (e.height === 0) {
          isVisible.value = false;
        }
      },
      onInteractive: (e: any) => {
        'worklet';
        height.value = e.height;
        progress.value = e.progress;
      },
    },
    []
  );

  const dismiss = useCallback(() => {
    KeyboardController.dismiss();
  }, []);

  const value: KeyboardState = { height, isVisible, progress, isAnimating, dismiss };

  return (
    <KeyboardStateContext.Provider value={value}>
      {children}
    </KeyboardStateContext.Provider>
  );
}

// Fallback provider using basic RN Keyboard API
function FallbackKeyboardStateProvider({ children }: KeyboardStateProviderProps) {
  const height = useSharedValue(0);
  const isVisible = useSharedValue(false);
  const progress = useSharedValue(0);
  const isAnimating = useSharedValue(false);

  useEffect(() => {
    const showSub = Keyboard.addListener('keyboardDidShow', (e) => {
      height.value = e.endCoordinates.height;
      isVisible.value = true;
      progress.value = 1;
    });

    const hideSub = Keyboard.addListener('keyboardDidHide', () => {
      height.value = 0;
      isVisible.value = false;
      progress.value = 0;
    });

    return () => {
      showSub.remove();
      hideSub.remove();
    };
  }, [height, isVisible, progress]);

  const dismiss = useCallback(() => {
    Keyboard.dismiss();
  }, []);

  const value: KeyboardState = { height, isVisible, progress, isAnimating, dismiss };

  return (
    <KeyboardStateContext.Provider value={value}>
      {children}
    </KeyboardStateContext.Provider>
  );
}

/**
 * Provider for keyboard state management.
 * Uses react-native-keyboard-controller when available, falls back to basic RN Keyboard API.
 */
export function KeyboardStateProvider({ children }: KeyboardStateProviderProps) {
  if (isKeyboardControllerAvailable) {
    return <NativeKeyboardStateProvider>{children}</NativeKeyboardStateProvider>;
  }
  return <FallbackKeyboardStateProvider>{children}</FallbackKeyboardStateProvider>;
}

/**
 * Hook to access keyboard state.
 * Must be used within KeyboardStateProvider.
 */
export function useKeyboardState(): KeyboardState {
  const context = useContext(KeyboardStateContext);
  if (!context) {
    throw new Error('useKeyboardState must be used within KeyboardStateProvider');
  }
  return context;
}

/**
 * Hook to get current keyboard height as a shared value.
 */
export function useKeyboardHeight(): SharedValue<number> {
  const { height } = useKeyboardState();
  return height;
}

/**
 * Hook to check if keyboard is currently visible.
 */
export function useKeyboardVisible(): SharedValue<boolean> {
  const { isVisible } = useKeyboardState();
  return isVisible;
}

export default KeyboardStateProvider;
