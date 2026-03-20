/**
 * Onboarding Context Provider
 *
 * Manages global onboarding state across all onboarding screens.
 * Provides data persistence, progress tracking, and navigation.
 */

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useRouter } from 'expo-router';
import * as Haptics from 'expo-haptics';
import AsyncStorage from '@react-native-async-storage/async-storage';

import OnboardingApi, {
  OnboardingState as ApiOnboardingState,
  saveOnboardingProgress,
  getLocalOnboardingData,
} from '../../services/onboardingApi';

interface OnboardingContextType {
  currentStep: number;
  completedSteps: number[];
  onboardingData: Record<string, any>;
  isLoading: boolean;
  error: string | null;
  totalSteps: number;
  progress: number;

  // Actions
  nextStep: () => void;
  previousStep: () => void;
  goToStep: (step: number) => void;
  saveStep: (step: number, data: any) => Promise<void>;
  updateOnboardingData: (data: Record<string, any>) => void;
  completeOnboarding: () => Promise<void>;
  clearError: () => void;
}

const OnboardingContext = createContext<OnboardingContextType | undefined>(
  undefined
);

const TOTAL_STEPS = 14; // Total number of onboarding steps

export function OnboardingProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState(0);
  const [completedSteps, setCompletedSteps] = useState<number[]>([]);
  const [onboardingData, setOnboardingData] = useState<Record<string, any>>({});
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isInitialized, setIsInitialized] = useState(false);

  // Initialize onboarding state from backend
  useEffect(() => {
    initializeOnboarding();
  }, []);

  const initializeOnboarding = async () => {
    setIsLoading(true);
    setError(null);

    try {
      // First, load from AsyncStorage immediately for fast UI
      const localData = await AsyncStorage.getItem('onboarding_data');
      if (localData) {
        setOnboardingData(JSON.parse(localData));
      }

      // Then try to get state from backend (will sync in background)
      const state = await OnboardingApi.getOnboardingState();

      setCurrentStep(state.current_step);
      setCompletedSteps(state.completed_steps || []);

      // MERGE backend data with local data, preferring backend for fields that exist
      const backendData = state.data || {};
      const localParsed = localData ? JSON.parse(localData) : {};
      const mergedData = { ...localParsed, ...backendData };

      console.log('[OnboardingContext] Local data:', localParsed);
      console.log('[OnboardingContext] Backend data:', backendData);
      console.log('[OnboardingContext] Merged data:', mergedData);

      setOnboardingData(mergedData);
      setIsInitialized(true);
    } catch (err) {
      console.error('Failed to fetch onboarding state:', err);

      // Fallback to local storage
      const localData = await getLocalOnboardingData();
      setOnboardingData(localData);
      setIsInitialized(true);
    } finally {
      setIsLoading(false);
    }
  };

  const nextStep = () => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);

    if (currentStep < TOTAL_STEPS - 1) {
      const newStep = currentStep + 1;

      // Mark current step as completed
      const newCompleted = [...completedSteps];
      if (!newCompleted.includes(currentStep)) {
        newCompleted.push(currentStep);
      }

      setCurrentStep(newStep);
      setCompletedSteps(newCompleted);

      // Navigate to next step
      router.push(`/onboarding/step-${newStep + 1}`);
    }
  };

  const previousStep = () => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);

    if (currentStep > 0) {
      const newStep = currentStep - 1;
      setCurrentStep(newStep);
      router.push(`/onboarding/step-${newStep + 1}`);
    }
  };

  const goToStep = (step: number) => {
    if (step >= 0 && step < TOTAL_STEPS) {
      setCurrentStep(step);
      router.push(`/onboarding/step-${step + 1}`);
    }
  };

  const saveStep = async (step: number, data: any) => {
    setIsLoading(true);
    setError(null);

    const startTime = Date.now();

    try {
      // Save to backend
      await OnboardingApi.saveOnboardingStep(step, data);

      // Update local state
      const updatedData = {
        ...onboardingData,
        [`step_${step}`]: data,
      };
      setOnboardingData(updatedData);

      // Save to local storage as backup
      await saveOnboardingProgress(step, data);
    } catch (err: any) {
      console.error('Failed to save step:', err);
      setError(err.message || 'Failed to save progress');

      // Still save to local storage as backup
      await saveOnboardingProgress(step, data);
    } finally {
      setIsLoading(false);
    }
  };

  const completeOnboarding = async () => {
    setIsLoading(true);
    setError(null);

    try {
      await OnboardingApi.completeOnboarding();

      // Mark all steps as completed
      const allSteps = Array.from({ length: TOTAL_STEPS }, (_, i) => i);
      setCompletedSteps(allSteps);
      setCurrentStep(TOTAL_STEPS - 1);

      // Navigate to success/dashboard
      router.push('/(main)');
    } catch (err: any) {
      console.error('Failed to complete onboarding:', err);
      setError(err.message || 'Failed to complete onboarding');
    } finally {
      setIsLoading(false);
    }
  };

  const updateOnboardingData = (data: Record<string, any>) => {
    setOnboardingData((prev: Record<string, any>) => {
      const updated = {
        ...prev,
        ...data,
      };

      // Save to AsyncStorage for persistence
      AsyncStorage.setItem('onboarding_data', JSON.stringify(updated));

      return updated;
    });
  };

  const clearError = () => {
    setError(null);
  };

  const progress = Math.round(((currentStep + 1) / TOTAL_STEPS) * 100);

  const value: OnboardingContextType = {
    currentStep,
    completedSteps,
    onboardingData,
    isLoading,
    error,
    totalSteps: TOTAL_STEPS,
    progress,
    nextStep,
    previousStep,
    goToStep,
    saveStep,
    updateOnboardingData,
    completeOnboarding,
    clearError,
  };

  return (
    <OnboardingContext.Provider value={value}>
      {children}
    </OnboardingContext.Provider>
  );
}

export function useOnboarding() {
  const context = useContext(OnboardingContext);

  if (context === undefined) {
    throw new Error('useOnboarding must be used within OnboardingProvider');
  }

  return context;
}
