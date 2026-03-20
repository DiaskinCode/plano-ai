import { useEffect, useRef, useState } from 'react';

type PoolMember = {
  id: number;
  activate: () => void;
};

type Pool = {
  limit: number;
  active: Set<number>;
  queue: PoolMember[];
  nextId: number;
};

/**
 * Creates a pool manager that limits concurrent animations.
 * Based on v0's pattern for staggered fade-in animations.
 *
 * @param limit - Maximum number of concurrent active animations
 * @returns A hook that can be used to join the pool
 */
export function createUsePool(limit = 2) {
  const pool: Pool = {
    limit,
    active: new Set(),
    queue: [],
    nextId: 0,
  };

  const tryActivateNext = () => {
    while (pool.active.size < pool.limit && pool.queue.length > 0) {
      const next = pool.queue.shift();
      if (next) {
        pool.active.add(next.id);
        next.activate();
      }
    }
  };

  return function useIsAnimatedInPool() {
    const [isActive, setIsActive] = useState(false);
    const idRef = useRef<number | null>(null);
    const mountedRef = useRef(true);

    useEffect(() => {
      mountedRef.current = true;

      // Assign unique ID
      const id = pool.nextId++;
      idRef.current = id;

      // Check if we can activate immediately
      if (pool.active.size < pool.limit) {
        pool.active.add(id);
        setIsActive(true);
      } else {
        // Join the queue
        pool.queue.push({
          id,
          activate: () => {
            if (mountedRef.current) {
              setIsActive(true);
            }
          },
        });
      }

      return () => {
        mountedRef.current = false;
        const myId = idRef.current;
        if (myId !== null) {
          // Remove from active set
          pool.active.delete(myId);
          // Remove from queue if still waiting
          const queueIndex = pool.queue.findIndex((m) => m.id === myId);
          if (queueIndex !== -1) {
            pool.queue.splice(queueIndex, 1);
          }
        }
      };
    }, []);

    const evict = () => {
      const myId = idRef.current;
      if (myId !== null) {
        pool.active.delete(myId);
        // Try to activate next in queue
        tryActivateNext();
      }
    };

    return { isActive, evict };
  };
}

// Pre-configured pools for common use cases
export const useMessageFadePool = createUsePool(2);
export const useTextFadePool = createUsePool(4);
export const useListItemPool = createUsePool(3);
