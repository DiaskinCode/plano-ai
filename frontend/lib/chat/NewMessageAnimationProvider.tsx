import React, { createContext, useContext, ReactNode } from 'react';
import { useSharedValue, SharedValue } from 'react-native-reanimated';

interface NewMessageAnimationContextValue {
  // Whether a message send animation is currently in progress
  isMessageSendAnimating: SharedValue<boolean>;

  // Whether the first assistant message should animate
  shouldAnimateFirstAssistant: SharedValue<boolean>;

  // Track if user message animation has completed
  didUserMessageAnimate: SharedValue<boolean>;

  // Reset animation state (called when changing chats)
  resetAnimationState: () => void;
}

const NewMessageAnimationContext = createContext<NewMessageAnimationContextValue | null>(null);

interface NewMessageAnimationProviderProps {
  children: ReactNode;
}

/**
 * Provider for managing new message animation state.
 * Coordinates the sequence of animations when sending a message:
 * 1. User message fades in and slides to top
 * 2. Once complete, assistant message fades in
 *
 * This follows v0's pattern of using shared values to coordinate
 * animations without re-renders.
 */
export function NewMessageAnimationProvider({ children }: NewMessageAnimationProviderProps) {
  // Main flag - set to true when user sends a message
  const isMessageSendAnimating = useSharedValue(false);

  // Set to true after user message animation completes
  const didUserMessageAnimate = useSharedValue(false);

  // Set to true to trigger assistant message fade-in
  const shouldAnimateFirstAssistant = useSharedValue(false);

  /**
   * Reset all animation state.
   * Called when switching between chats to prevent stale animations.
   */
  const resetAnimationState = React.useCallback(() => {
    isMessageSendAnimating.value = false;
    didUserMessageAnimate.value = false;
    shouldAnimateFirstAssistant.value = false;
  }, [isMessageSendAnimating, didUserMessageAnimate, shouldAnimateFirstAssistant]);

  const value: NewMessageAnimationContextValue = {
    isMessageSendAnimating,
    shouldAnimateFirstAssistant,
    didUserMessageAnimate,
    resetAnimationState,
  };

  return (
    <NewMessageAnimationContext.Provider value={value}>
      {children}
    </NewMessageAnimationContext.Provider>
  );
}

/**
 * Hook to access new message animation context.
 */
export function useNewMessageAnimation(): NewMessageAnimationContextValue {
  const context = useContext(NewMessageAnimationContext);
  if (!context) {
    throw new Error(
      'useNewMessageAnimation must be used within NewMessageAnimationProvider'
    );
  }
  return context;
}

export default NewMessageAnimationProvider;
