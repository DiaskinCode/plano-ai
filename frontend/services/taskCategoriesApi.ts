/**
 * Task Categories API Service
 *
 * Handles application-specific task categories for college application platform
 */

import AsyncStorage from "@react-native-async-storage/async-storage";

const API_URL = (process.env.EXPO_PUBLIC_API_URL || "http://192.168.0.210:8000") + "/api";

// Types
export interface TaskCategory {
  id: number;
  name: string;
  icon: string;
  color: string;
  description: string;
  is_application_specific: boolean;
  order: number;
}

// Helper function to get auth token
const getAuthToken = async (): Promise<string | null> => {
  try {
    const token = await AsyncStorage.getItem("access_token");
    return token;
  } catch (error) {
    console.error("Error getting auth token:", error);
    return null;
  }
};

// Generic API request wrapper
const apiRequest = async (
  endpoint: string,
  method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE" = "GET",
  body?: any,
): Promise<any> => {
  const token = await getAuthToken();

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const config: RequestInit = {
    method,
    headers,
  };

  if (body && method !== "GET") {
    config.body = JSON.stringify(body);
  }

  try {
    const response = await fetch(`${API_URL}${endpoint}`, config);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error(`API Error [${method} ${endpoint}]:`, error);
    throw error;
  }
};

// ==================== Task Categories API ====================

/**
 * Get all task categories
 */
export const getTaskCategories = async (): Promise<TaskCategory[]> => {
  return apiRequest("/api/todos/categories/", "GET");
};

/**
 * Get a specific category by ID
 */
export const getTaskCategory = async (
  categoryId: number,
): Promise<TaskCategory> => {
  return apiRequest(`/api/todos/categories/${categoryId}/`, "GET");
};

// ==================== Local Cache ====================

const CATEGORIES_CACHE_KEY = "task_categories_cache";
const CATEGORIES_CACHE_TIMESTAMP_KEY = "task_categories_cache_timestamp";
const CACHE_DURATION = 24 * 60 * 60 * 1000; // 24 hours

/**
 * Get categories from cache (if available and fresh)
 */
export const getCachedCategories = async (): Promise<TaskCategory[] | null> => {
  try {
    const timestampStr = await AsyncStorage.getItem(
      CATEGORIES_CACHE_TIMESTAMP_KEY,
    );
    if (!timestampStr) return null;

    const timestamp = parseInt(timestampStr, 10);
    const now = Date.now();

    if (now - timestamp > CACHE_DURATION) {
      // Cache expired
      return null;
    }

    const cachedData = await AsyncStorage.getItem(CATEGORIES_CACHE_KEY);
    if (!cachedData) return null;

    return JSON.parse(cachedData);
  } catch (error) {
    console.error("Error reading cached categories:", error);
    return null;
  }
};

/**
 * Cache categories locally
 */
export const cacheCategories = async (
  categories: TaskCategory[],
): Promise<void> => {
  try {
    await AsyncStorage.setItem(
      CATEGORIES_CACHE_KEY,
      JSON.stringify(categories),
    );
    await AsyncStorage.setItem(
      CATEGORIES_CACHE_TIMESTAMP_KEY,
      Date.now().toString(),
    );
  } catch (error) {
    console.error("Error caching categories:", error);
  }
};

/**
 * Get categories with cache fallback
 */
export const getCategoriesWithCache = async (): Promise<TaskCategory[]> => {
  try {
    // Try API first
    const categories = await getTaskCategories();
    await cacheCategories(categories);
    return categories;
  } catch (error) {
    console.warn("Failed to fetch categories from API, using cache:", error);

    // Fallback to cache
    const cached = await getCachedCategories();
    if (cached) {
      return cached;
    }

    // If no cache, throw error
    throw error;
  }
};

// ==================== Category Utilities ====================

/**
 * Get category by name from list
 */
export const getCategoryByName = (
  categories: TaskCategory[],
  name: string,
): TaskCategory | undefined => {
  return categories.find(
    (cat) => cat.name.toLowerCase() === name.toLowerCase(),
  );
};

/**
 * Get category by ID from list
 */
export const getCategoryById = (
  categories: TaskCategory[],
  id: number,
): TaskCategory | undefined => {
  return categories.find((cat) => cat.id === id);
};

/**
 * Filter categories by type
 */
export const filterCategoriesByType = (
  categories: TaskCategory[],
  applicationSpecific: boolean,
): TaskCategory[] => {
  return categories.filter(
    (cat) => cat.is_application_specific === applicationSpecific,
  );
};

/**
 * Sort categories by order
 */
export const sortCategoriesByOrder = (
  categories: TaskCategory[],
): TaskCategory[] => {
  return [...categories].sort((a, b) => a.order - b.order);
};

export default {
  getTaskCategories,
  getTaskCategory,
  getCachedCategories,
  cacheCategories,
  getCategoriesWithCache,
  getCategoryByName,
  getCategoryById,
  filterCategoriesByType,
  sortCategoriesByOrder,
};
