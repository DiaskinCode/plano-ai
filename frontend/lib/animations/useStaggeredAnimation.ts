import { useEffect, useRef } from 'react';
import { DURATIONS } from './constants';

type StaggerQueue = {
  delay: number;
  queue: (() => void)[];
  isProcessing: boolean;
  batchSize: number;
};

/**
 * Creates a staggered animation scheduler.
 * Animations are queued and executed with a delay between each batch.
 * If the queue grows large, batch size increases to prevent buildup.
 *
 * @param delay - Delay in ms between animation batches
 * @returns A hook that schedules animations in a staggered manner
 */
export function createUseStaggered(delay = DURATIONS.stagger) {
  const stagger: StaggerQueue = {
    delay,
    queue: [],
    isProcessing: false,
    batchSize: 2,
  };

  const processQueue = () => {
    if (stagger.queue.length === 0) {
      stagger.isProcessing = false;
      // Reset batch size when queue is empty
      stagger.batchSize = 2;
      return;
    }

    stagger.isProcessing = true;

    // Adjust batch size based on queue length to prevent buildup
    if (stagger.queue.length > 10) {
      stagger.batchSize = Math.min(stagger.queue.length, 5);
    } else if (stagger.queue.length > 5) {
      stagger.batchSize = 3;
    } else {
      stagger.batchSize = 2;
    }

    // Process a batch
    const batch = stagger.queue.splice(0, stagger.batchSize);
    batch.forEach((callback) => callback());

    // Schedule next batch
    setTimeout(processQueue, stagger.delay);
  };

  return function useStaggeredAnimation(startAnimation: () => void) {
    const hasScheduled = useRef(false);

    useEffect(() => {
      if (hasScheduled.current) return;
      hasScheduled.current = true;

      stagger.queue.push(startAnimation);

      if (!stagger.isProcessing) {
        processQueue();
      }

      return () => {
        // Remove from queue if unmounted before animation started
        const index = stagger.queue.indexOf(startAnimation);
        if (index !== -1) {
          stagger.queue.splice(index, 1);
        }
      };
    }, [startAnimation]);
  };
}

// Pre-configured staggered animation hooks
export const useMessageStagger = createUseStaggered(32);
export const useTextStagger = createUseStaggered(16);
export const useListStagger = createUseStaggered(50);
