import { useAnimatedReaction, runOnJS } from 'react-native-reanimated';
import { useMessageList } from '../MessageListProvider';
import { useComposerHeight } from '../ComposerHeightProvider';

/**
 * Hook that scrolls to end when composer height changes.
 * This simulates the experience of a non-absolute-positioned input
 * when the user is already scrolled near the end of the chat.
 *
 * Behavior (v0 pattern):
 * - When composer grows (new lines typed), scroll to keep content visible
 * - Only scrolls if user is near the end of the chat
 * - If user has scrolled up in the chat, composer growth won't affect scroll
 */
export function useScrollWhenComposerSizeUpdates() {
  const { listRef, scrollToEnd, scrollOffset, contentHeight, scrollHeight } =
    useMessageList();
  const { composerHeight } = useComposerHeight();

  /**
   * Check if scrolled near the end and scroll if needed.
   */
  const autoscrollToEnd = () => {
    const list = listRef.current;
    if (!list) return;

    // Get current scroll state
    const currentOffset = scrollOffset.value;
    const currentContentHeight = contentHeight.value;
    const currentScrollHeight = scrollHeight.value;

    // Calculate distance from end
    const distanceFromEnd =
      currentContentHeight - currentOffset - currentScrollHeight;

    // If we're near the end (within threshold), scroll to end
    // Using negative check because contentInset can make this negative
    if (distanceFromEnd < 50) {
      scrollToEnd({ animated: false });

      // Wait a frame for layout update, then scroll again
      setTimeout(() => {
        scrollToEnd({ animated: false });
      }, 16);
    }
  };

  /**
   * React to composer height changes.
   */
  useAnimatedReaction(
    () => composerHeight.value,
    (height, prevHeight) => {
      // Only trigger when height actually changes and is valid
      if (height > 0 && prevHeight !== null && height !== prevHeight) {
        runOnJS(autoscrollToEnd)();
      }
    },
    []
  );
}

export default useScrollWhenComposerSizeUpdates;
