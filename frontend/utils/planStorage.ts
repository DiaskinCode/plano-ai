/**
 * Plan Storage Utility
 *
 * Manages user subscription plan persistence using AsyncStorage
 * Provides a frontend-only solution until backend subscription API is ready
 */

import AsyncStorage from '@react-native-async-storage/async-storage';

const PLAN_STORAGE_KEY = '@user_plan';

export type UserPlan = 'basic' | 'pro' | 'premium';

export const planStorage = {
  /**
   * Get the current user's plan from AsyncStorage
   * Returns 'basic' if no plan is stored
   */
  async getPlan(): Promise<UserPlan> {
    try {
      const plan = await AsyncStorage.getItem(PLAN_STORAGE_KEY);
      return (plan as UserPlan) || 'basic';
    } catch (error) {
      console.error('Error loading user plan:', error);
      return 'basic';
    }
  },

  /**
   * Save the user's plan to AsyncStorage
   */
  async setPlan(plan: UserPlan): Promise<void> {
    try {
      await AsyncStorage.setItem(PLAN_STORAGE_KEY, plan);
      console.log('User plan set to:', plan);
    } catch (error) {
      console.error('Error saving user plan:', error);
    }
  },

  /**
   * Remove the stored plan (reset to basic)
   */
  async clearPlan(): Promise<void> {
    try {
      await AsyncStorage.removeItem(PLAN_STORAGE_KEY);
      console.log('User plan cleared');
    } catch (error) {
      console.error('Error clearing user plan:', error);
    }
  },
};
