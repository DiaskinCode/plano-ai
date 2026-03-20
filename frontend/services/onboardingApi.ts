/**
 * Onboarding API Service for College Application Platform
 *
 * Handles all onboarding-related API calls:
 * - Start/complete onboarding
 * - Save academic profile, test scores, activities
 * - Get AI university suggestions
 * - Generate AI plan
 * - Subscription management
 */

import AsyncStorage from "@react-native-async-storage/async-storage";

const API_URL = (process.env.EXPO_PUBLIC_API_URL || "http://192.168.0.210:8000") + "/api";

// Types
export interface OnboardingState {
  current_step: number;
  completed_steps: number[];
  data: Record<string, any>;
  selected_language: string;
  is_onboarding_complete: boolean;
}

export interface AcademicProfile {
  student_status: string;
  school_name: string;
  graduation_year: number;
  gpa: number;
  gpa_scale: number;
  specialization: string;
  favorite_subjects: string[];
}

export interface TestScores {
  sat_status?: string;
  sat_score?: number;
  sat_math?: number;
  sat_reading_writing?: number;
  sat_test_date?: string;
  act_status?: string;
  act_score?: number;
  act_test_date?: string;
  ielts_status?: string;
  ielts_score?: number;
  ielts_test_date?: string;
  toefl_status?: string;
  toefl_score?: number;
  toefl_test_date?: string;
}

export interface ExtracurricularActivity {
  category: string;
  title: string;
  organization: string;
  role: string;
  start_date: string;
  end_date?: string;
  is_ongoing: boolean;
  hours_per_week: number;
  description: string;
}

export interface GeneratedPlan {
  start_date: string;
  end_date: string;
  total_months: number;
  total_tasks: number;
  estimated_total_hours: number;
  is_preview?: boolean;
  visible_months?: number;
  total_tasks_in_preview?: number;
  total_tasks_hidden?: number;
  milestones: Milestone[];
  tasks: Task[];
  summary: PlanSummary;
}

export interface Milestone {
  month: number;
  title: string;
  focus: string;
  deliverables: string[];
  priority_tasks: number;
}

export interface Task {
  id: string;
  title: string;
  description: string;
  category: string;
  month: number;
  estimated_minutes: number;
  priority: string;
  dependencies?: string[];
}

export interface PlanSummary {
  total_tasks: number;
  tasks_by_category: Record<string, number>;
  tasks_by_month: Record<number, number>;
  target_university_count: number;
  estimated_weekly_hours: number;
}

export interface SubscriptionPlan {
  name: string;
  price_monthly: number;
  price_yearly: number;
  features: string[];
  is_popular: boolean;
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
  method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE",
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

// ==================== Onboarding Flow APIs ====================

export const startOnboarding = async (): Promise<OnboardingState> => {
  return apiRequest("/onboarding/start/", "POST");
};

export const getOnboardingState = async (): Promise<OnboardingState> => {
  return apiRequest("/onboarding/state/", "GET");
};

export const saveOnboardingStep = async (
  step: number,
  data: Record<string, any>,
  timeSpentSeconds: number = 0,
  markComplete: boolean = true,
): Promise<any> => {
  return apiRequest("/onboarding/step/", "POST", {
    step,
    data,
    time_spent_seconds: timeSpentSeconds,
    mark_complete: markComplete,
  });
};

export const completeOnboarding = async (): Promise<any> => {
  return apiRequest("/onboarding/complete/", "POST");
};

// ==================== Academic Profile APIs ====================

export const saveAcademicProfile = async (
  profile: AcademicProfile,
): Promise<any> => {
  return apiRequest("/onboarding/academic-profile/", "POST", profile);
};

export const saveTestScores = async (scores: TestScores): Promise<any> => {
  return apiRequest("/onboarding/test-scores/", "POST", scores);
};

// ==================== Extracurriculars APIs ====================

export const getExtracurriculars = async (): Promise<
  ExtracurricularActivity[]
> => {
  return apiRequest("/onboarding/extracurriculars/all/", "GET");
};

export const createExtracurricular = async (
  activity: Omit<ExtracurricularActivity, "id">,
): Promise<ExtracurricularActivity> => {
  return apiRequest("/onboarding/extracurriculars/", "POST", activity);
};

export const updateExtracurricular = async (
  id: number,
  activity: Partial<ExtracurricularActivity>,
): Promise<ExtracurricularActivity> => {
  return apiRequest(`/onboarding/extracurriculars/${id}/`, "PUT", activity);
};

export const deleteExtracurricular = async (id: number): Promise<void> => {
  return apiRequest(`/onboarding/extracurriculars/${id}/`, "DELETE");
};

export const bulkCreateExtracurriculars = async (
  activities: ExtracurricularActivity[],
): Promise<any> => {
  return apiRequest("/onboarding/extracurriculars/bulk_create/", "POST", {
    universities: activities,
  });
};

// ==================== Plan Generation APIs ====================

export const savePlanSelection = async (selection: {
  selectedPlans: string[];
  examTypes: string[];
  languageTestTypes: string[];
}): Promise<any> => {
  return apiRequest("/onboarding/plan-selection/", "POST", {
    selected_plans: selection.selectedPlans,
    exam_types: selection.examTypes,
    language_test_types: selection.languageTestTypes,
  });
};

export const generateAIPlan = async (options: {
  includeTimeline?: boolean;
  includeTasks?: boolean;
  includeMilestones?: boolean;
  startDate?: string;
  examTypes?: string[];
  onboardingData?: Record<string, any>;
}): Promise<{
  detail: string;
  plan: GeneratedPlan;
  paywall?: any;
  subscription?: any;
}> => {
  return apiRequest("/onboarding/generate-plan/", "POST", {
    include_timeline: options.includeTimeline !== false,
    include_tasks: options.includeTasks !== false,
    include_milestones: options.includeMilestones !== false,
    start_date: options.startDate || new Date().toISOString(),
    exam_types: options.examTypes || ["SAT"],
    onboardingData: options.onboardingData,
  });
};

// ==================== Subscription APIs ====================

export const getSubscriptionPlans = async (): Promise<{
  plans: SubscriptionPlan[];
}> => {
  return apiRequest("/subscription/plans/", "GET");
};

export const getCurrentSubscription = async (): Promise<any> => {
  return apiRequest("/subscription/current/", "GET");
};

export const activateSubscription = async (
  planName: "basic" | "pro" | "premium",
  billingCycle: "monthly" | "yearly" = "monthly",
): Promise<any> => {
  return apiRequest("/subscription/create-checkout-session/", "POST", {
    plan_name: planName,
    billing_cycle: billingCycle,
  });
};

export const cancelSubscription = async (
  cancelAtPeriodEnd: boolean = true,
): Promise<any> => {
  return apiRequest("/subscription/cancel/", "POST", {
    cancel_at_period_end: cancelAtPeriodEnd,
  });
};

// ==================== Analytics APIs ====================

export const getOnboardingAnalytics = async (): Promise<{
  current_step: number;
  completed_steps: number[];
  progress_percentage: number;
  total_time_seconds: number;
  total_time_minutes: number;
  snapshot_count: number;
  started_at: string;
  last_updated: string;
}> => {
  return apiRequest("/onboarding/analytics/", "GET");
};

// ==================== Helper Functions ====================

export const saveOnboardingProgress = async (
  step: number,
  data: any,
): Promise<void> => {
  // Save to local storage as backup
  try {
    const currentData = await AsyncStorage.getItem("onboarding_data");
    const parsedData = currentData ? JSON.parse(currentData) : {};
    const updatedData = {
      ...parsedData,
      [`step_${step}`]: data,
      last_updated: new Date().toISOString(),
    };
    await AsyncStorage.setItem("onboarding_data", JSON.stringify(updatedData));
  } catch (error) {
    console.error("Error saving local onboarding data:", error);
  }
};

export const getLocalOnboardingData = async (): Promise<
  Record<string, any>
> => {
  try {
    const data = await AsyncStorage.getItem("onboarding_data");
    return data ? JSON.parse(data) : {};
  } catch (error) {
    console.error("Error getting local onboarding data:", error);
    return {};
  }
};

export const clearOnboardingData = async (): Promise<void> => {
  try {
    await AsyncStorage.removeItem("onboarding_data");
  } catch (error) {
    console.error("Error clearing onboarding data:", error);
  }
};

export default {
  startOnboarding,
  getOnboardingState,
  saveOnboardingStep,
  completeOnboarding,
  saveAcademicProfile,
  saveTestScores,
  getExtracurriculars,
  createExtracurricular,
  updateExtracurricular,
  deleteExtracurricular,
  bulkCreateExtracurriculars,
  savePlanSelection,
  generateAIPlan,
  getSubscriptionPlans,
  getCurrentSubscription,
  activateSubscription,
  cancelSubscription,
  getOnboardingAnalytics,
  saveOnboardingProgress,
  getLocalOnboardingData,
  clearOnboardingData,
};
