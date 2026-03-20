/**
 * Staggered Fade-in Animation System (v0 inspired)
 *
 * Implements pool-based staggered animations for streaming content.
 * Features:
 * - Limited concurrent animations to prevent performance issues
 * - Automatic batching based on queue size
 * - Eviction after animation completes
 */

import { useState, useEffect, useCallback } from 'react';
import { useSharedValue, withTiming, Easing } from 'react-native-reanimated';
import { animation } from '@/theme';

// Pool state management (outside React for global coordination)
class AnimationPool {
  private activeItems: Set<number> = new Set();
  private queue: Array<{ id: number; callback: () => void }> = [];
  private maxConcurrent: number;
  private nextId = 0;

  constructor(maxConcurrent: number = Infinity) {
    this.maxConcurrent = maxConcurrent;
  }

  request(callback: () => void): { id: number; isActive: boolean } {
    const id = this.nextId++;

    if (this.activeItems.size < this.maxConcurrent) {
      this.activeItems.add(id);
      setTimeout(callback, this.activeItems.size * animation.liquidGlass.messageFadeStagger);
      return { id, isActive: true };
    }

    this.queue.push({ id, callback });
    return { id, isActive: false };
  }

  evict(id: number) {
    this.activeItems.delete(id);
    this.processQueue();
  }

  private processQueue() {
    while (this.queue.length > 0 && this.activeItems.size < this.maxConcurrent) {
      const item = this.queue.shift();
      if (item) {
        this.activeItems.add(item.id);
        setTimeout(item.callback, 0);
      }
    }
  }

  reset() {
    this.activeItems.clear();
    this.queue = [];
  }

  getQueueSize() {
    return this.queue.length;
  }
}

// Global pool instances
const textFadePool = new AnimationPool(4); // Max 4 text elements at once
const elementFadePool = new AnimationPool(); // No limit for elements

/**
 * Create a custom hook that uses a specific animation pool
 */
export function createUsePool(maxConcurrent?: number) {
  const pool = new AnimationPool(maxConcurrent);

  return function usePool() {
    const [isActive, setIsActive] = useState(false);
    const [poolId, setPoolId] = useState<number | null>(null);

    useEffect(() => {
      const result = pool.request(() => {
        setIsActive(true);
      });

      setPoolId(result.id);

      if (result.isActive) {
        setIsActive(true);
      }

      return () => {
        if (poolId !== null) {
          pool.evict(poolId);
        }
      };
    }, []);

    const evict = useCallback(() => {
      if (poolId !== null) {
        pool.evict(poolId);
        setIsActive(false);
      }
    }, [poolId]);

    return { isActive, evict };
  };
}

/**
 * Hook for text fade-in animations (limited to 4 concurrent)
 */
export function useTextFadePool() {
  const [isActive, setIsActive] = useState(false);
  const [poolId, setPoolId] = useState<number | null>(null);

  useEffect(() => {
    const result = textFadePool.request(() => {
      setIsActive(true);
    });

    setPoolId(result.id);

    if (result.isActive) {
      setIsActive(true);
    }

    return () => {
      if (poolId !== null) {
        textFadePool.evict(poolId);
      }
    };
  }, []);

  const evict = useCallback(() => {
    if (poolId !== null) {
      textFadePool.evict(poolId);
      setIsActive(false);
    }
  }, [poolId]);

  return { isActive, evict };
}

/**
 * Hook for element fade-in animations (no limit)
 */
export function useElementFadePool() {
  const [isActive, setIsActive] = useState(false);
  const [poolId, setPoolId] = useState<number | null>(null);

  useEffect(() => {
    const result = elementFadePool.request(() => {
      setIsActive(true);
    });

    setPoolId(result.id);

    if (result.isActive) {
      setIsActive(true);
    }

    return () => {
      if (poolId !== null) {
        elementFadePool.evict(poolId);
      }
    };
  }, []);

  const evict = useCallback(() => {
    if (poolId !== null) {
      elementFadePool.evict(poolId);
      setIsActive(false);
    }
  }, [poolId]);

  return { isActive, evict };
}

/**
 * Staggered animation hook with dynamic batching
 * Increases batch size based on queue length
 */
export function createUseStaggered(delayMs: number = 32) {
  let staggerIndex = 0;
  let lastBatchTime = 0;

  return function useStaggered(callback: () => void) {
    useEffect(() => {
      const now = Date.now();
      const timeSinceLastBatch = now - lastBatchTime;

      // Reset batch if enough time has passed
      if (timeSinceLastBatch > 1000) {
        staggerIndex = 0;
      }

      lastBatchTime = now;
      const delay = staggerIndex * delayMs;
      staggerIndex++;

      const timeoutId = setTimeout(callback, delay);

      return () => clearTimeout(timeoutId);
    }, [callback]);
  };
}

/**
 * Fade-in animation with Reanimated
 */
export function useFadeInAnimation(duration: number = animation.liquidGlass.messageFadeDuration) {
  const opacity = useSharedValue(0);

  const startFade = useCallback(() => {
    opacity.value = withTiming(1, {
      duration,
      easing: Easing.out(Easing.cubic),
    });
  }, [opacity, duration]);

  return { opacity, startFade };
}
