import { useEffect, useRef } from 'react';
import {
  useSharedValue,
  useAnimatedReaction,
  runOnJS,
  SharedValue,
} from 'react-native-reanimated';
import { useMessageList } from '../MessageListProvider';

interface UseInitialScrollToEndOptions {
  // Whether there are messages to scroll to
  hasMessages: boolean;
  // Callback when scroll is complete (to fade in content)
  onScrollComplete?: () => void;
}

interface UseInitialScrollToEndResult {
  // Whether initial scroll has completed
  hasScrolledToEnd: SharedValue<boolean>;
}

/**
 * Hook that scrolls to end when opening an existing chat.
 * This creates an inverted-list-style experience where existing
 * chats start scrolled to the bottom.
 *
 * Implementation (v0 pattern):
 * - Calls scrollToEnd multiple times to handle dynamic heights
 * - Waits for blank size to be calculated before scrolling
 * - Sets hasScrolledToEnd flag when complete (for fade-in)
 */
export function useInitialScrollToEnd({
  hasMessages,
  onScrollComplete,
}: UseInitialScrollToEndOptions): UseInitialScrollToEndResult {
  const { scrollToEnd, blankSize } = useMessageList();

  const hasStartedScrolledToEnd = useSharedValue(false);
  const hasScrolledToEnd = useSharedValue(false);
  const scrollAttempts = useRef(0);

  /**
   * Perform scroll to end with multiple attempts.
   * v0 found this necessary due to dynamic content heights.
   */
  const performScrollToEnd = () => {
    if (scrollAttempts.current > 5) {
      // Max attempts reached, mark as complete anyway
      hasScrolledToEnd.value = true;
      onScrollComplete?.();
      return;
    }

    scrollAttempts.current += 1;

    // First scroll
    scrollToEnd({ animated: false });

    // Second scroll after frame
    requestAnimationFrame(() => {
      scrollToEnd({ animated: false });

      // Third scroll after short delay
      setTimeout(() => {
        scrollToEnd({ animated: false });

        // Fourth scroll and mark complete
        requestAnimationFrame(() => {
          scrollToEnd({ animated: false });
          hasScrolledToEnd.value = true;
          onScrollComplete?.();
        });
      }, 16);
    });
  };

  /**
   * Trigger initial scroll when blank size is ready.
   */
  useAnimatedReaction(
    () => {
      // Don't scroll if already started or no messages
      if (hasStartedScrolledToEnd.value || !hasMessages) {
        return false;
      }
      // Wait for blank size to be calculated
      return blankSize.value > 0;
    },
    (shouldScroll) => {
      if (shouldScroll) {
        hasStartedScrolledToEnd.value = true;
        runOnJS(performScrollToEnd)();
      }
    },
    [hasMessages]
  );

  /**
   * Fallback: scroll after mount if blank size never gets set.
   * This handles the case where chat is short and has no blank size.
   */
  useEffect(() => {
    if (!hasMessages) return;

    const timeout = setTimeout(() => {
      if (!hasStartedScrolledToEnd.value) {
        hasStartedScrolledToEnd.value = true;
        performScrollToEnd();
      }
    }, 100);

    return () => clearTimeout(timeout);
  }, [hasMessages]);

  return { hasScrolledToEnd };
}

export default useInitialScrollToEnd;
