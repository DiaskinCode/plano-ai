import React, { ReactNode, useEffect } from 'react';
import { ComposerHeightProvider } from './ComposerHeightProvider';
import { MessageListProvider } from './MessageListProvider';
import { NewMessageAnimationProvider, useNewMessageAnimation } from './NewMessageAnimationProvider';
import { KeyboardStateProvider } from '../keyboard';

interface ChatProviderProps {
  children: ReactNode;
  // Chat ID - when this changes, we reset animation state
  chatId?: string | number | null;
}

/**
 * Inner component that handles chat ID changes.
 */
function ChatProviderInner({
  children,
  chatId,
}: ChatProviderProps) {
  const { resetAnimationState } = useNewMessageAnimation();

  // Reset animation state when chat changes
  useEffect(() => {
    resetAnimationState();
  }, [chatId, resetAnimationState]);

  return <>{children}</>;
}

/**
 * Main chat provider that combines all chat-related context providers.
 * This follows v0's composable provider pattern.
 *
 * Providers included:
 * - KeyboardStateProvider: Tracks keyboard height and visibility
 * - ComposerHeightProvider: Tracks floating composer height
 * - MessageListProvider: Manages message list state and scroll
 * - NewMessageAnimationProvider: Coordinates message animations
 *
 * Usage:
 * ```tsx
 * <ChatProvider chatId={currentChatId}>
 *   <ChatScreen />
 * </ChatProvider>
 * ```
 */
export function ChatProvider({ children, chatId }: ChatProviderProps) {
  return (
    <KeyboardStateProvider>
      <ComposerHeightProvider>
        <MessageListProvider>
          <NewMessageAnimationProvider>
            <ChatProviderInner chatId={chatId}>
              {children}
            </ChatProviderInner>
          </NewMessageAnimationProvider>
        </MessageListProvider>
      </ComposerHeightProvider>
    </KeyboardStateProvider>
  );
}

export default ChatProvider;
