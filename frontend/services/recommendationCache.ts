/**
 * Recommendation Caching Service
 *
 * Caches university recommendations to reduce API costs and improve performance.
 * Cache is stored in AsyncStorage with expiration timestamps.
 */

import AsyncStorage from '@react-native-async-storage/async-storage';

const CACHE_KEY_PREFIX = '@recommendations_';
const CACHE_EXPIRY_MS = 48 * 60 * 60 * 1000; // 48 hours

interface CachedRecommendations {
  data: any;
  timestamp: number;
  userId: string;
  profileHash: string;
}

/**
 * Generate a hash of the user's profile to use as part of the cache key
 */
async function generateProfileHash(): Promise<string> {
  try {
    // Get relevant profile data that affects recommendations
    const keys = [
      '@user_profile_gpa',
      '@user_profile_sat',
      '@user_profile_act',
      '@user_profile_major',
      '@user_profile_country',
      '@user_profile_budget',
    ];

    const values = await Promise.all(
      keys.map(async (key) => {
        const value = await AsyncStorage.getItem(key);
        return value || '';
      })
    );

    // Simple hash of profile values
    const profileString = values.join('|');
    return btoa(profileString).substring(0, 16);
  } catch (error) {
    console.warn('Error generating profile hash:', error);
    return 'default';
  }
}

/**
 * Get the current user ID from AsyncStorage
 */
async function getUserId(): Promise<string> {
  try {
    const userId = await AsyncStorage.getItem('@user_id');
    return userId || 'anonymous';
  } catch (error) {
    return 'anonymous';
  }
}

/**
 * Get the full cache key for the current user and profile
 */
async function getCacheKey(): Promise<string> {
  const userId = await getUserId();
  const profileHash = await generateProfileHash();
  return `${CACHE_KEY_PREFIX}${userId}_${profileHash}`;
}

/**
 * Save recommendations to cache
 */
export async function saveRecommendations(data: any): Promise<void> {
  try {
    const cacheKey = await getCacheKey();
    const userId = await getUserId();
    const profileHash = await generateProfileHash();

    const cacheData: CachedRecommendations = {
      data,
      timestamp: Date.now(),
      userId,
      profileHash,
    };

    await AsyncStorage.setItem(cacheKey, JSON.stringify(cacheData));
    console.log('Recommendations cached successfully');
  } catch (error) {
    console.error('Error saving recommendations to cache:', error);
  }
}

/**
 * Load recommendations from cache
 * Returns null if cache is expired, doesn't exist, or profile has changed
 */
export async function loadRecommendations(): Promise<any | null> {
  try {
    const cacheKey = await getCacheKey();
    const cachedData = await AsyncStorage.getItem(cacheKey);

    if (!cachedData) {
      return null;
    }

    const parsed: CachedRecommendations = JSON.parse(cachedData);
    const now = Date.now();
    const age = now - parsed.timestamp;

    // Check if cache is expired
    if (age > CACHE_EXPIRY_MS) {
      console.log('Cache expired, removing...');
      await AsyncStorage.removeItem(cacheKey);
      return null;
    }

    console.log(`Using cached recommendations (age: ${Math.round(age / 1000 / 60)} minutes old)`);
    return parsed.data;
  } catch (error) {
    console.error('Error loading recommendations from cache:', error);
    return null;
  }
}

/**
 * Check if cached recommendations exist and are valid
 */
export async function hasValidCache(): Promise<boolean> {
  const cached = await loadRecommendations();
  return cached !== null;
}

/**
 * Get cache age in minutes
 */
export async function getCacheAge(): Promise<number | null> {
  try {
    const cacheKey = await getCacheKey();
    const cachedData = await AsyncStorage.getItem(cacheKey);

    if (!cachedData) {
      return null;
    }

    const parsed: CachedRecommendations = JSON.parse(cachedData);
    const now = Date.now();
    return Math.round((now - parsed.timestamp) / 1000 / 60); // minutes
  } catch (error) {
    return null;
  }
}

/**
 * Clear the recommendation cache
 */
export async function clearCache(): Promise<void> {
  try {
    const cacheKey = await getCacheKey();
    await AsyncStorage.removeItem(cacheKey);
    console.log('Recommendation cache cleared');
  } catch (error) {
    console.error('Error clearing cache:', error);
  }
}

/**
 * Clear all recommendation caches (for cleanup or logout)
 */
export async function clearAllCaches(): Promise<void> {
  try {
    const allKeys = await AsyncStorage.getAllKeys();
    const recommendationKeys = allKeys.filter(key => key.startsWith(CACHE_KEY_PREFIX));

    if (recommendationKeys.length > 0) {
      await AsyncStorage.multiRemove(recommendationKeys);
      console.log(`Cleared ${recommendationKeys.length} recommendation caches`);
    }
  } catch (error) {
    console.error('Error clearing all caches:', error);
  }
}
