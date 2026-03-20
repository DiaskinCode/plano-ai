import React, { createContext, useContext, ReactNode, useCallback } from 'react';
import { useSharedValue, SharedValue } from 'react-native-reanimated';
import { LayoutChangeEvent } from 'react-native';

interface ComposerHeightContextValue {
  // Current height of the composer
  composerHeight: SharedValue<number>;
  // Handler for layout changes
  onLayout: (event: LayoutChangeEvent) => void;
}

const ComposerHeightContext = createContext<ComposerHeightContextValue | null>(null);

interface ComposerHeightProviderProps {
  children: ReactNode;
  // Initial height (optional, useful for avoiding layout jumps)
  initialHeight?: number;
}

/**
 * Provider for tracking composer height.
 * The composer floats above the message list, so we need to track
 * its height to properly set content insets.
 */
export function ComposerHeightProvider({
  children,
  initialHeight = 0,
}: ComposerHeightProviderProps) {
  const composerHeight = useSharedValue(initialHeight);

  const onLayout = useCallback(
    (event: LayoutChangeEvent) => {
      const { height } = event.nativeEvent.layout;
      composerHeight.value = height;
    },
    [composerHeight]
  );

  return (
    <ComposerHeightContext.Provider value={{ composerHeight, onLayout }}>
      {children}
    </ComposerHeightContext.Provider>
  );
}

/**
 * Hook to access composer height context.
 */
export function useComposerHeight(): ComposerHeightContextValue {
  const context = useContext(ComposerHeightContext);
  if (!context) {
    throw new Error('useComposerHeight must be used within ComposerHeightProvider');
  }
  return context;
}

/**
 * Hook that provides layout handler for synchronous height measurement.
 * Uses ref.current.measure() for synchronous height on New Architecture.
 */
export function useSyncLayoutHandler(
  onHeight: (layout: { height: number; width: number }) => void
) {
  const ref = React.useRef<any>(null);

  // Use useLayoutEffect for synchronous measurement on mount
  React.useLayoutEffect(() => {
    if (ref.current?.measure) {
      ref.current.measure(
        (
          _x: number,
          _y: number,
          width: number,
          height: number
        ) => {
          if (height > 0) {
            onHeight({ height, width });
          }
        }
      );
    }
  }, [onHeight]);

  const handleLayout = useCallback(
    (event: LayoutChangeEvent) => {
      const { height, width } = event.nativeEvent.layout;
      onHeight({ height, width });
    },
    [onHeight]
  );

  return { ref, onLayout: handleLayout };
}

export default ComposerHeightProvider;
