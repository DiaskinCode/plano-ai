import axios from "axios";
import AsyncStorage from "@react-native-async-storage/async-storage";

const API_URL = process.env.EXPO_PUBLIC_API_URL
  ? `${process.env.EXPO_PUBLIC_API_URL}/api`
  : "http://192.168.0.210:8000/api";

const api = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Add auth token interceptor
api.interceptors.request.use(
  async (config) => {
    const token = await AsyncStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error),
);

// Add response interceptor for token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = await AsyncStorage.getItem("refresh_token");
        const response = await axios.post(`${API_URL}/auth/token/refresh/`, {
          refresh: refreshToken,
        });

        const { access } = response.data;
        await AsyncStorage.setItem("access_token", access);

        originalRequest.headers.Authorization = `Bearer ${access}`;
        return api(originalRequest);
      } catch (refreshError) {
        // Refresh failed, logout user
        await AsyncStorage.multiRemove([
          "access_token",
          "refresh_token",
          "user",
        ]);
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  },
);

// Auth API
export const authAPI = {
  register: (data: {
    email: string;
    username: string;
    password: string;
    password2: string;
    timezone?: string;
  }) => api.post("/auth/register/", data),
  login: (data: { email: string; password: string }) =>
    api.post("/auth/login/", data),
  getProfile: () => api.get("/auth/profile/"),
  updateProfile: (data: any) => api.patch("/auth/profile/", data),
  updateTimezone: (timezone: string) =>
    api.patch("/auth/profile/", { timezone }),
  completeOnboarding: (data: any) => api.post("/auth/onboarding/", data),
  deleteAccount: () => api.delete("/auth/delete-account/"),

  // Progress tracking
  getProgress: () => api.get("/auth/progress/"),
  updateProgress: () => api.post("/auth/progress/update/"),
  getStreak: () => api.get("/auth/progress/streak/"),
};

// AI API
export const aiAPI = {
  generateScenarios: () => api.post("/ai/generate_scenarios/"),
  selectScenario: (scenarioId: number) =>
    api.post("/ai/select_scenario/", { scenario_id: scenarioId }),
  generateVision: (scenarioId: number) =>
    api.post("/ai/generate_vision/", { scenario_id: scenarioId }),
  integrateTask: (task: string) => api.post("/ai/integrate_task/", { task }),
  eveningCheckin: (data: any) => api.post("/ai/evening_checkin/", data),
  analyzeOpportunity: (data: {
    title: string;
    description: string;
    date_occurred: string;
  }) => api.post("/ai/analyze_opportunity/", data),
  chat: (message: string, conversationId?: number) =>
    api.post("/ai/chat/", { message, conversation_id: conversationId }),
  defaults: {
    baseURL: API_URL,
  },
  transcribeAudio: (formData: FormData) =>
    api.post("/ai/transcribe_audio/", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    }),
  generateTaskDescription: (taskId: number) =>
    api.post("/ai/task-description/", { task_id: taskId }),
  askTaskAI: (
    taskId: number,
    question: string,
    conversationId?: number,
    mode?: "clarify" | "expand" | "research",
  ) =>
    api.post("/ai/task-assistant/", {
      task_id: taskId,
      question: question,
      conversation_id: conversationId,
      mode: mode || "clarify",
    }),
  getTaskConversation: (taskId: number) =>
    api.get(`/ai/task-conversation/${taskId}/`),
  createSubtasksFromAI: (parentTaskId: number, steps: string[]) =>
    api.post("/ai/create-subtasks/", {
      parent_task_id: parentTaskId,
      steps: steps,
    }),
  // Template-based task generation (Week 3 Day 15: Integration)
  generateAtomicTasks: (
    goalspecId: number,
    options?: {
      daysAhead?: number;
      useTemplates?: boolean;
      enhance?: boolean;
    },
  ) =>
    api.post("/ai/generate-atomic-tasks/", {
      goalspec_id: goalspecId,
      days_ahead: options?.daysAhead ?? 30,
      use_templates: options?.useTemplates ?? true,
      enhance: options?.enhance ?? false,
    }),
};

// Todos API
export const todosAPI = {
  getTodos: (filter?: string) => api.get("/todos/", { params: { filter } }),
  getTasks: (params?: any) => api.get("/todos/", { params }),
  list: (filter?: string, status?: string) =>
    api.get("/todos/", { params: { filter, status } }),
  createTodo: (data: any) => api.post("/todos/", data),
  create: (data: any) => api.post("/todos/", data),
  update: (id: number, data: any) => api.patch(`/todos/${id}/`, data),
  delete: (id: number) => api.delete(`/todos/${id}/`),
  markDone: (id: number) => api.post(`/todos/${id}/mark_done/`),
  // Enhanced task completion with result logging (Phase 1.2)
  completeTask: (
    id: number,
    data: {
      actual_duration_minutes?: number;
      difficulty_rating?: number;
      completion_status?: string;
      result_type?: string;
      result_data?: Record<string, any>;
      quality_rating?: number;
      time_of_day?: string;
      energy_level_at_completion?: string;
      notes?: string;
    },
  ) => api.post(`/todos/${id}/complete/`, data),
  skipTodo: (id: number, reason?: string) =>
    api.post(`/todos/${id}/skip/`, { reason }),
  skip: (id: number, reason?: string) =>
    api.post(`/todos/${id}/skip/`, { reason }),
  reschedule: (id: number, newDate: string, newTime?: string) =>
    api.post(`/todos/${id}/reschedule/`, {
      new_date: newDate,
      new_time: newTime,
    }),
  // OLD: generateTasks: () => api.post("/todos/generate/"), // REMOVED - Use eligibility flow instead
  checkEligibility: () => api.get("/todos/eligibility/check/"),
  setStrategyAndGenerate: (strategy: 'direct' | 'foundation' | 'change_shortlist') =>
    api.post("/todos/eligibility/generate/", { strategy }),
  getTaskStatus: (taskId: string) => api.get(`/todos/task-status/${taskId}/`),
};

// Vision API (Legacy - kept for backward compatibility)
export const visionAPI = {
  getVision: () => api.get("/vision/"),
  getVisionAnalytics: () => api.get("/vision/analytics/"),
  getDailyHeadline: () => api.get("/vision/daily-headline/"),
  updateVision: (id: number, data: any) => api.patch(`/vision/${id}/`, data),
  scheduleTasksForMilestone: (milestoneId: number) =>
    api.post(`/vision/milestones/${milestoneId}/schedule/`),
  addMilestoneBuffer: (milestoneId: number, days: number) =>
    api.post(`/vision/milestones/${milestoneId}/add-buffer/`, { days }),
  markMilestoneRisk: (milestoneId: number, note: string) =>
    api.post(`/vision/milestones/${milestoneId}/mark-risk/`, { note }),
};

// Goals API
export const goalsAPI = {
  getGoals: () => api.get("/goals/"),
  getGoal: (id: number) => api.get(`/goals/${id}/`),
  getGoalAnalytics: (id: number) => api.get(`/goals/${id}/analytics/`),
  createGoal: (data: any) => api.post("/goals/", data),
  updateGoal: (id: number, data: any) => api.patch(`/goals/${id}/`, data),
  deleteGoal: (id: number) => api.delete(`/goals/${id}/`),
  getAIRecommendations: (id: number) =>
    api.get(`/goals/${id}/ai-recommendations/`),
  replanGoal: (id: number) => api.post(`/goals/${id}/replan/`),
  accelerateGoal: (id: number, days: number) =>
    api.post(`/goals/${id}/accelerate/`, { days }),
  adjustFocus: (id: number, newFocus: string) =>
    api.post(`/goals/${id}/adjust-focus/`, { focus: newFocus }),
};

// Chat API
export const chatAPI = {
  getConversations: () => api.get("/chat/conversations/"),
  createConversation: (title: string) =>
    api.post("/chat/conversations/", { title }),
  getConversation: (id: number) => api.get(`/chat/conversations/${id}/`),
  updateConversation: (id: number, data: { title: string }) =>
    api.patch(`/chat/conversations/${id}/`, data),
  deleteConversation: (id: number) => api.delete(`/chat/conversations/${id}/`),
  getMessages: (conversationId: number) =>
    api.get(`/chat/conversations/${conversationId}/messages/`),
};

// Analytics API
export const analyticsAPI = {
  getOverview: (range?: string) =>
    api.get("/analytics/overview/", { params: { range } }),
  getTimeFocus: (range?: string) =>
    api.get("/analytics/time-focus/", { params: { range } }),
  getTasksOutcomes: (range?: string) =>
    api.get("/analytics/tasks-outcomes/", { params: { range } }),
  getMilestonesPath: (range?: string) =>
    api.get("/analytics/milestones-path/", { params: { range } }),
  getHabitsQuality: (range?: string) =>
    api.get("/analytics/habits-quality/", { params: { range } }),
  getStreak: () => api.get("/analytics/streak/"),

  // Daily Pulse / Morning Brief
  getDailyPulse: () => api.get("/analytics/daily-pulse/"),
  generateDailyPulse: () => api.post("/analytics/daily-pulse/generate/"),
  markDailyPulseShown: (channel: "app" | "push" | "chat") =>
    api.post("/analytics/daily-pulse/mark-shown/", { channel }),
  sendDailyPulseToChat: () => api.post("/analytics/daily-pulse/send-to-chat/"),
};

// GoalSpec API (Atomic Task System)
export const goalSpecAPI = {
  list: () => api.get("/auth/goalspecs/"),
  create: (data: any) => api.post("/auth/goalspecs/", data),
  retrieve: (id: number) => api.get(`/auth/goalspecs/${id}/`),
  update: (id: number, data: any) => api.patch(`/auth/goalspecs/${id}/`, data),
  delete: (id: number) => api.delete(`/auth/goalspecs/${id}/`),
  complete: (id: number) => api.post(`/auth/goalspecs/${id}/complete/`),
  activate: (id: number) => api.post(`/auth/goalspecs/${id}/activate/`),
  deactivate: (id: number) => api.post(`/auth/goalspecs/${id}/deactivate/`),
  active: () => api.get("/auth/goalspecs/active/"),
  validateConstraints: (id: number) =>
    api.get(`/auth/goalspecs/${id}/validate_constraints/`),
  withStatistics: () => api.get("/auth/goalspecs/with_statistics/"),
  withMilestones: () => api.get("/auth/goalspecs/with_milestones/"),
};

// Daily Planner API (Atomic Task System)
export const dailyPlannerAPI = {
  generate: (targetDate?: string) =>
    api.post("/todos/daily-planner/generate/", { target_date: targetDate }),
  preview: (targetDate?: string) =>
    api.get("/todos/daily-planner/preview/", {
      params: { target_date: targetDate },
    }),
  allocation: () => api.get("/todos/daily-planner/allocation/"),
};

// Weekly Review API (Atomic Task System)
export const weeklyReviewAPI = {
  generate: (weekStart?: string) =>
    api.post("/todos/weekly-review/generate/", { week_start: weekStart }),
  formatted: (weekStart?: string) =>
    api.get("/todos/weekly-review/formatted/", {
      params: { week_start: weekStart },
    }),
  statsOnly: (weekStart?: string) =>
    api.get("/todos/weekly-review/stats_only/", {
      params: { week_start: weekStart },
    }),
};

// Task Evidence API (Atomic Task System)
export const evidenceAPI = {
  list: () => api.get("/todos/evidence/"),
  create: (data: any) => api.post("/todos/evidence/", data),
  delete: (id: number) => api.delete(`/todos/evidence/${id}/`),
  byTask: (taskId: number) =>
    api.get("/todos/evidence/by-task/", { params: { task_id: taskId } }),
  byType: (evidenceType: string) =>
    api.get("/todos/evidence/by-type/", {
      params: { evidence_type: evidenceType },
    }),
  updateNote: (id: number, note: string) =>
    api.patch(`/todos/evidence/${id}/update-note/`, { note }),
};

// Task Runs API (Atomic Task System - Let's Go Sessions)
export const taskRunsAPI = {
  list: () => api.get("/todos/task-runs/"),
  create: (data: any) => api.post("/todos/task-runs/", data),
  update: (id: number, data: any) => api.patch(`/todos/task-runs/${id}/`, data),
  addMessage: (id: number, userInput?: string, aiResponse?: string) =>
    api.post(`/todos/task-runs/${id}/add-message/`, {
      user_input: userInput,
      ai_response: aiResponse,
    }),
  complete: (id: number, durationSeconds: number, artifactId?: number) =>
    api.post(`/todos/task-runs/${id}/complete/`, {
      duration_seconds: durationSeconds,
      artifact_id: artifactId,
    }),
  byTask: (taskId: number) =>
    api.get("/todos/task-runs/by-task/", { params: { task_id: taskId } }),
  recent: (limit: number = 10) =>
    api.get("/todos/task-runs/recent/", { params: { limit } }),
  transcript: (id: number) => api.get(`/todos/task-runs/${id}/transcript/`),
};

// AI Insights API (Smart Task System)
export const insightsAPI = {
  // Get category progress (study, language, sport, etc.)
  getCategoryProgress: () => api.get("/todos/insights/category-progress/"),

  // Analyze why user skips tasks
  getSkipPatterns: (daysBack: number = 14) =>
    api.get("/todos/insights/skip-patterns/", {
      params: { days_back: daysBack },
    }),

  // Get all AI-generated insights
  getInsights: (unreadOnly: boolean = false, category?: string) =>
    api.get("/todos/insights/", {
      params: { unread_only: unreadOnly, category },
    }),

  // Mark insight as read
  markRead: (insightId: number) =>
    api.post(`/todos/insights/${insightId}/read/`),

  // Dismiss insight
  dismiss: (insightId: number) =>
    api.post(`/todos/insights/${insightId}/dismiss/`),

  // 🎲 Smart task suggestion based on energy/time/mood
  suggestSmart: (data: {
    current_energy: "high" | "medium" | "low";
    available_minutes: number;
    current_mood?: "motivated" | "tired" | "stressed";
  }) => api.post("/todos/suggest-smart/", data),

  // Complete task with feedback for AI learning
  completeWithFeedback: (
    taskId: number,
    data: {
      completion_reason:
        | "completed"
        | "skipped_no_time"
        | "skipped_no_motivation"
        | "skipped_distracted"
        | "skipped_too_hard"
        | "skipped_other";
      difficulty_rating?: number; // 1-5
      actual_duration_minutes?: number;
      notes?: string;
      energy_level_at_completion?: "high" | "medium" | "low";
    },
  ) => api.post(`/todos/${taskId}/complete-with-feedback/`, data),
};

// Performance API (Adaptive Intelligence - Phase 2.1)
export const performanceAPI = {
  // Get 30-day performance analysis
  getInsights: () => api.get("/auth/performance/"),

  // Trigger fresh performance analysis
  triggerAnalysis: () => api.post("/auth/performance/"),
};

// Task Splitter API (Adaptive Intelligence - Phase 2.3)
export const taskSplitterAPI = {
  // Split a task into sub-tasks using AI
  splitTask: (taskId: number) => api.post(`/todos/${taskId}/split/`),

  // Get list of tasks that are candidates for splitting
  getCandidates: () => api.get("/todos/split/candidates/"),

  // Bulk split multiple tasks
  bulkSplit: (taskIds: number[]) =>
    api.post("/todos/split/bulk/", { task_ids: taskIds }),
};

// Voice Interface API (Adaptive Intelligence - Phase 4.2)
export const voiceAPI = {
  // Process voice command
  processCommand: (transcript: string, timestamp?: string) =>
    api.post("/ai/voice/process/", { transcript, timestamp }),

  // Voice query (coach/performance questions)
  query: (query: string, context?: string) =>
    api.post("/ai/voice/query/", { query, context }),

  // Get voice capabilities
  getCapabilities: () => api.get("/ai/voice/capabilities/"),
};

// Contextual Pulse API (Adaptive Intelligence - Phase 3.2)
export const contextualPulseAPI = {
  // Generate context-aware daily pulse using 30-day performance data
  generate: () => api.post("/analytics/daily-pulse/contextual/"),
};

// Conversational Onboarding API
export const onboardingChatAPI = {
  // Initialize chat for a category
  init: (category: string) =>
    api.post("/auth/onboarding/chat/init/", { category }),

  // Send message and get AI response
  send: (data: {
    category: string;
    message: string;
    conversation_history: Array<{ role: string; content: string }>;
    extracted_data: Record<string, any>;
  }) => api.post("/auth/onboarding/chat/send/", data),

  // Complete onboarding - save category data
  complete: (data: { category: string; extracted_data: Record<string, any> }) =>
    api.post("/auth/onboarding/chat/complete/", data),

  // Finalize onboarding - generate tasks for all categories
  // IMPORTANT: 10 minute timeout because task generation takes 2-4 minutes
  finalize: () =>
    api.post(
      "/auth/onboarding/finalize/",
      {},
      {
        timeout: 600000, // 10 minutes in milliseconds
      },
    ),

  // Get onboarding status
  status: () => api.get("/auth/onboarding/status/"),
};

// Community API
export const communityAPI = {
  // Communities
  getCommunities: (params?: {
    type?: "region" | "topic";
    search?: string;
    sort?: "popular" | "new" | "active";
  }) => api.get("/communities/", { params }),

  getCommunity: (id: number) => api.get(`/communities/${id}/`),

  joinCommunity: (id: number) => api.post(`/communities/${id}/join/`),

  leaveCommunity: (id: number) => api.post(`/communities/${id}/leave/`),

  getCommunityPosts: (
    id: number,
    params?: {
      sort?: "hot" | "new" | "top";
      flair?: string;
    },
  ) => api.get(`/communities/${id}/posts/`, { params }),

  getMyCommunities: (params?: { sort?: "visited" | "joined" }) =>
    api.get("/communities/my_communities/", { params }),

  // Posts
  getPosts: (params?: {
    community?: number;
    user?: number;
    flair?: string;
    sort?: "hot" | "new" | "top";
  }) => api.get("/posts/", { params }),

  getPost: (id: number) => api.get(`/posts/${id}/`),

  createPost: (data: {
    community: number;
    title: string;
    content: string;
    flair?: string;
    images?: string[];
    files?: Array<{ url: string; name: string }>;
  }) => api.post("/posts/", data),

  updatePost: (id: number, data: any) => api.patch(`/posts/${id}/`, data),

  deletePost: (id: number) => api.delete(`/posts/${id}/`),

  upvotePost: (id: number) => api.post(`/posts/${id}/upvote/`),

  downvotePost: (id: number) => api.post(`/posts/${id}/downvote/`),

  getPostComments: (id: number) => api.get(`/posts/${id}/comments/`),

  // Comments
  getComments: (params?: { post?: number }) =>
    api.get("/comments/", { params }),

  getComment: (id: number) => api.get(`/comments/${id}/`),

  createComment: (data: {
    post: number;
    parent_comment?: number;
    content: string;
  }) => api.post("/comments/", data),

  updateComment: (id: number, data: { content: string }) =>
    api.patch(`/comments/${id}/`, data),

  deleteComment: (id: number) => api.delete(`/comments/${id}/`),

  upvoteComment: (id: number) => api.post(`/comments/${id}/upvote/`),

  downvoteComment: (id: number) => api.post(`/comments/${id}/downvote/`),

  getCommentReplies: (id: number) => api.get(`/comments/${id}/replies/`),
};

// Social API
export const socialAPI = {
  // Profiles
  getProfile: (userId: number) => api.get(`/social/profile/${userId}/`),
  getOwnProfile: () => api.get("/social/profile/"),
  updateProfile: (userId: number, data: any) =>
    api.patch(`/social/profile/${userId}/`, data),

  // Follow
  getFollowers: (userId?: number) =>
    api.get("/social/follows/followers/", { params: { user_id: userId } }),
  getFollowing: (userId?: number) =>
    api.get("/social/follows/following/", { params: { user_id: userId } }),
  followUser: (username: string) =>
    api.post(`/social/follow/${username}/follow/`),
  unfollowUser: (username: string) =>
    api.post(`/social/follow/${username}/unfollow/`),

  // Search
  searchUsers: (params: {
    search?: string;
    location?: string;
    target_university?: string;
    min_sat?: number;
    min_gpa?: number;
  }) => api.get("/social/search/", { params }),

  // Messaging
  getConversations: () => api.get("/social/messages/conversations/"),
  getMessagesWithUser: (userId: number) =>
    api.get("/social/messages/with_user/", { params: { user_id: userId } }),
  sendMessage: (data: {
    recipient: number;
    content: string;
    attachments?: Array<{ type: string; url: string; name?: string }>;
    reply_to?: number;
  }) => api.post("/social/messages/", data),

  // Blocking
  getBlockedUsers: () => api.get("/social/blocked/"),
  blockUser: (userId: number, reason?: string) =>
    api.post("/social/blocked/", { blocked: userId, reason }),
  unblockUser: (blockId: number) => api.delete(`/social/blocked/${blockId}/`),
};

// Mentor API
export const mentorAPI = {
  // List mentors
  getMentors: (params?: {
    featured?: boolean;
    expertise?: string;
    min_rating?: number;
    min_plan?: "pro" | "premium";
    search?: string;
    ordering?: "rating" | "reviews" | "price_asc" | "price_desc";
    page?: number;
    page_size?: number;
  }) => api.get("/mentors/", { params }),

  // Get mentor details
  getMentor: (id: number) => api.get(`/mentors/${id}/`),

  // Get mentor availability
  getAvailability: (
    mentorId: number,
    params: {
      start_date: string; // ISO 8601 date
      end_date: string; // ISO 8601 date
    },
  ) => api.get(`/mentors/${mentorId}/availability/`, { params }),

  // Get mentor reviews
  getReviews: (
    mentorId: number,
    params?: {
      page?: number;
      page_size?: number;
      ordering?: "-created_at" | "rating" | "-rating";
    },
  ) => api.get(`/mentors/${mentorId}/reviews/`, { params }),

  // Book a session
  bookSession: (
    mentorId: number,
    data: {
      slot_id: number;
      notes?: string;
    },
  ) => api.post(`/mentors/${mentorId}/book/`, data),

  // Get user's bookings
  getMyBookings: () => api.get("/mentors/my-bookings/"),

  // Cancel booking
  cancelBooking: (bookingId: number, reason?: string) =>
    api.post(`/mentors/bookings/${bookingId}/cancel/`, { reason }),
};

// Essays API
export const essaysAPI = {
  // Get all essay templates
  getTemplates: () => api.get("/todos/essay-templates/"),

  // Get essay projects
  getProjects: () => api.get("/todos/essay-projects/"),
  getProject: (id: number) => api.get(`/todos/essay-projects/${id}/`),

  // Start a new essay from template
  startEssay: (data: { template_id: number; target_university: string }) =>
    api.post("/todos/essay-projects/start_essay/", data),

  // AI brainstorming
  brainstorm: (id: number) =>
    api.post(`/todos/essay-projects/${id}/brainstorm/`),

  // Generate outline
  generateOutline: (id: number, data: { selected_topic: any }) =>
    api.post(`/todos/essay-projects/${id}/generate_outline/`, data),

  // Save draft
  saveDraft: (id: number, content: string) =>
    api.post(`/todos/essay-projects/${id}/save_draft/`, { content }),

  // Get AI feedback
  getFeedback: (id: number) =>
    api.post(`/todos/essay-projects/${id}/get_feedback/`),

  // Complete essay
  complete: (id: number) => api.post(`/todos/essay-projects/${id}/complete/`),
};

export default api;
