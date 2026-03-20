import { Mixpanel } from 'mixpanel-react-native';
import { Platform } from 'react-native';
import * as Application from 'expo-application';

const MIXPANEL_TOKEN = '6a235fefccdb4cb6daba5f680c56b420';

class AnalyticsService {
  private mixpanel: Mixpanel | null = null;
  private isInitialized = false;

  async initialize() {
    if (this.isInitialized) return;

    try {
      this.mixpanel = new Mixpanel(MIXPANEL_TOKEN, true);
      // Use EU endpoint
      this.mixpanel.setServerURL('https://api-eu.mixpanel.com');
      await this.mixpanel.init();

      // Set super properties that will be sent with every event
      this.mixpanel.registerSuperProperties({
        platform: Platform.OS,
        app_version: Application.nativeApplicationVersion || '1.0.0',
        build_number: Application.nativeBuildVersion || '1',
      });

      this.isInitialized = true;
      console.log('Mixpanel analytics initialized');
    } catch (error) {
      console.error('Failed to initialize Mixpanel:', error);
    }
  }

  // User Identification
  identify(userId: string, userProperties?: Record<string, any>) {
    if (!this.mixpanel) return;

    this.mixpanel.identify(userId);

    if (userProperties) {
      this.mixpanel.getPeople().set(userProperties);
    }
  }

  // Set user properties
  setUserProperties(properties: Record<string, any>) {
    if (!this.mixpanel) return;
    this.mixpanel.getPeople().set(properties);
  }

  // Increment a user property
  incrementUserProperty(property: string, value: number = 1) {
    if (!this.mixpanel) return;
    this.mixpanel.getPeople().increment(property, value);
  }

  // Reset on logout
  reset() {
    if (!this.mixpanel) return;
    this.mixpanel.reset();
  }

  // Generic event tracking
  track(eventName: string, properties?: Record<string, any>) {
    if (!this.mixpanel) return;
    this.mixpanel.track(eventName, properties);
  }

  // Time an event (call timeEvent before and track after)
  timeEvent(eventName: string) {
    if (!this.mixpanel) return;
    this.mixpanel.timeEvent(eventName);
  }

  // ===== AUTHENTICATION EVENTS =====

  trackUserRegistered(userId: string, email: string, username: string) {
    this.identify(userId, {
      $email: email,
      $name: username,
      username,
      registration_date: new Date().toISOString(),
      onboarding_completed: false,
    });
    this.track('user_registered', { email, username });
  }

  trackUserLoggedIn(userId: string, email: string) {
    this.identify(userId);
    this.track('user_logged_in', { email });
  }

  trackUserLoggedOut() {
    this.track('user_logged_out');
    this.reset();
  }

  // ===== ONBOARDING EVENTS =====

  trackOnboardingStarted() {
    this.timeEvent('onboarding_completed');
    this.track('onboarding_started');
  }

  trackOnboardingStepCompleted(stepNumber: number, stepName: string, properties?: Record<string, any>) {
    this.track('onboarding_step_completed', {
      step_number: stepNumber,
      step_name: stepName,
      ...properties,
    });
  }

  trackOnboardingWelcomeCompleted(userName: string) {
    this.track('onboarding_welcome_completed', { user_name: userName });
  }

  trackOnboardingCategorySelected(category: string, totalCategories: number) {
    this.track('onboarding_category_selected', {
      category,
      total_categories: totalCategories,
    });
  }

  trackOnboardingChatStarted(category: string) {
    this.track('onboarding_chat_started', { category });
  }

  trackOnboardingChatMessageSent(category: string, messageCount: number) {
    this.track('onboarding_chat_message_sent', {
      category,
      message_count: messageCount,
    });
  }

  trackOnboardingCategoryCompleted(category: string, messagesExchanged: number) {
    this.track('onboarding_category_completed', {
      category,
      messages_exchanged: messagesExchanged,
    });
  }

  trackOnboardingTaskGenerationStarted(categoriesCount: number) {
    this.track('onboarding_task_generation_started', {
      categories_count: categoriesCount,
    });
  }

  trackOnboardingCompleted(tasksGenerated: number, categoriesCompleted: number) {
    this.setUserProperties({
      onboarding_completed: true,
      onboarding_completed_date: new Date().toISOString(),
      initial_tasks_generated: tasksGenerated,
      categories_completed: categoriesCompleted,
    });
    this.track('onboarding_completed', {
      tasks_generated: tasksGenerated,
      categories_completed: categoriesCompleted,
    });
  }

  // ===== TASK EVENTS =====

  trackTaskCreated(taskId: number, properties?: {
    title?: string;
    goalspec_id?: number;
    category?: string;
    priority?: number;
    scheduled_date?: string;
  }) {
    this.incrementUserProperty('total_tasks_created');
    this.track('task_created', {
      task_id: taskId,
      ...properties,
    });
  }

  trackTaskCompleted(taskId: number, properties?: {
    title?: string;
    goalspec_id?: number;
    category?: string;
    difficulty_rating?: number;
    actual_duration_minutes?: number;
  }) {
    this.incrementUserProperty('total_tasks_completed');
    this.track('task_completed', {
      task_id: taskId,
      ...properties,
    });
  }

  trackTaskSkipped(taskId: number, reason?: string) {
    this.incrementUserProperty('total_tasks_skipped');
    this.track('task_skipped', {
      task_id: taskId,
      reason,
    });
  }

  trackTaskFeedbackSubmitted(taskId: number, feedbackType: 'completed' | 'skipped', properties?: Record<string, any>) {
    this.track('task_feedback_submitted', {
      task_id: taskId,
      feedback_type: feedbackType,
      ...properties,
    });
  }

  trackTaskDetailViewed(taskId: number, title?: string) {
    this.track('task_detail_viewed', {
      task_id: taskId,
      title,
    });
  }

  trackTaskAIQuestionAsked(taskId: number, mode: string) {
    this.track('task_ai_question_asked', {
      task_id: taskId,
      mode,
    });
  }

  trackTaskSubtasksCreated(taskId: number, subtasksCount: number) {
    this.track('task_subtasks_created', {
      task_id: taskId,
      subtasks_count: subtasksCount,
    });
  }

  trackTasksGeneratedFromVision() {
    this.track('tasks_generated_from_vision');
  }

  // ===== CHAT/AI EVENTS =====

  trackChatMessageSent(conversationId?: number, messageLength?: number) {
    this.incrementUserProperty('total_messages_sent');
    this.track('chat_message_sent', {
      conversation_id: conversationId,
      message_length: messageLength,
    });
  }

  trackVoiceRecordingStarted() {
    this.track('voice_recording_started');
  }

  trackVoiceRecordingStopped(durationSeconds: number) {
    this.track('voice_recording_stopped', {
      duration_seconds: durationSeconds,
    });
  }

  trackSmartSuggestionRequested(energyLevel: string, availableTime: number) {
    this.track('smart_suggestion_requested', {
      energy_level: energyLevel,
      available_time: availableTime,
    });
  }

  trackConversationCreated() {
    this.track('conversation_created');
  }

  trackConversationDeleted(conversationId: number) {
    this.track('conversation_deleted', {
      conversation_id: conversationId,
    });
  }

  // ===== GOAL EVENTS =====

  trackGoalViewed(goalId: number, title?: string, category?: string) {
    this.track('goal_viewed', {
      goal_id: goalId,
      title,
      category,
    });
  }

  trackGoalsScreenViewed(goalsCount: number) {
    this.track('goals_screen_viewed', {
      goals_count: goalsCount,
    });
  }

  // ===== SCREEN VIEW EVENTS =====

  trackScreenView(screenName: string, properties?: Record<string, any>) {
    this.track('screen_viewed', {
      screen_name: screenName,
      ...properties,
    });
  }

  // ===== SETTINGS EVENTS =====

  trackLanguageChanged(oldLanguage: string, newLanguage: string) {
    this.setUserProperties({ preferred_language: newLanguage });
    this.track('language_changed', {
      old_language: oldLanguage,
      new_language: newLanguage,
    });
  }

  trackNotificationTapped(notificationType: string, taskId?: number) {
    this.track('notification_tapped', {
      notification_type: notificationType,
      task_id: taskId,
    });
  }

  trackInterventionApplied(interventionType: string) {
    this.track('intervention_applied', {
      intervention_type: interventionType,
    });
  }

  trackInterventionDismissed(interventionType: string) {
    this.track('intervention_dismissed', {
      intervention_type: interventionType,
    });
  }

  // ===== DAILY PULSE =====

  trackDailyPulseSent() {
    this.track('daily_pulse_sent');
  }

  trackDailyPulseViewed() {
    this.track('daily_pulse_viewed');
  }

  // ===== WEEKLY REPORT =====

  trackWeeklyReportViewed(completionRate: number, tasksCompleted: number) {
    this.track('weekly_report_viewed', {
      completion_rate: completionRate,
      tasks_completed: tasksCompleted,
    });
  }
}

// Export singleton instance
export const analytics = new AnalyticsService();
export default analytics;
