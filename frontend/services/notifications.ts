import * as Notifications from 'expo-notifications';
import * as Device from 'expo-device';
import { Platform } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import api from './api';

export interface NotificationPreferences {
  task_reminders_enabled: boolean;
  deadline_notifications_enabled: boolean;
  ai_motivation_enabled: boolean;
  daily_pulse_reminder_enabled: boolean;
  meeting_reminders_enabled: boolean;
  task_reminder_minutes_before: number;
  daily_pulse_time: string; // HH:MM format
  quiet_hours_enabled: boolean;
  quiet_hours_start: string | null; // HH:MM format
  quiet_hours_end: string | null; // HH:MM format
}

class NotificationService {
  private pushToken: string | null = null;
  private notificationListener: any = null;
  private responseListener: any = null;

  /**
   * Register for push notifications and get Expo push token
   * Returns the push token or null if registration failed
   */
  async registerForPushNotifications(): Promise<string | null> {
    try {
      // Check if running on physical device
      if (!Device.isDevice) {
        console.warn('Push notifications only work on physical devices');
        return null;
      }

      // Get existing permission status
      const { status: existingStatus } = await Notifications.getPermissionsAsync();
      let finalStatus = existingStatus;

      // Request permission if not granted
      if (existingStatus !== 'granted') {
        const { status } = await Notifications.requestPermissionsAsync();
        finalStatus = status;
      }

      // Check if permission was granted
      if (finalStatus !== 'granted') {
        console.warn('Push notification permission not granted');
        return null;
      }

      // Get Expo push token
      const tokenData = await Notifications.getExpoPushTokenAsync({
        projectId: '3909a1af-1b9b-49d2-b617-3f3b7e17341a'
      });

      this.pushToken = tokenData.data;

      // Store token locally
      await AsyncStorage.setItem('expo_push_token', this.pushToken);

      // Configure notification channel for Android
      if (Platform.OS === 'android') {
        await Notifications.setNotificationChannelAsync('default', {
          name: 'default',
          importance: Notifications.AndroidImportance.MAX,
          vibrationPattern: [0, 250, 250, 250],
          lightColor: '#FF231F7C',
        });
      }

      console.log('Push token obtained:', this.pushToken);
      return this.pushToken;

    } catch (error) {
      console.error('Error registering for push notifications:', error);
      return null;
    }
  }

  /**
   * Send push token to backend for registration
   */
  async sendTokenToBackend(token: string): Promise<boolean> {
    try {
      const response = await api.post('/notifications/register-token/', {
        push_token: token,
      });

      console.log('Push token registered with backend:', response.data);
      return true;
    } catch (error) {
      console.error('Error sending push token to backend:', error);
      return false;
    }
  }

  /**
   * Setup notification listeners for handling incoming notifications
   */
  setupNotificationListeners(
    onNotificationReceived?: (notification: Notifications.Notification) => void,
    onNotificationResponse?: (response: Notifications.NotificationResponse) => void
  ) {
    // Listener for notifications received while app is in foreground
    this.notificationListener = Notifications.addNotificationReceivedListener((notification) => {
      console.log('Notification received:', notification);
      if (onNotificationReceived) {
        onNotificationReceived(notification);
      }
    });

    // Listener for user interactions with notifications
    this.responseListener = Notifications.addNotificationResponseReceivedListener((response) => {
      console.log('Notification response:', response);

      const data = response.notification.request.content.data;

      // Handle different notification types
      if (data.type === 'task_reminder' && data.task_id) {
        // Navigate to task detail or open task
        console.log('Task reminder clicked:', data.task_id);
      } else if (data.type === 'deadline' && data.task_id) {
        // Navigate to task detail
        console.log('Deadline notification clicked:', data.task_id);
      } else if (data.type === 'daily_pulse') {
        // Navigate to daily pulse screen
        console.log('Daily pulse reminder clicked');
      } else if (data.type === 'ai_motivation') {
        // Open app or chat
        console.log('AI motivation clicked');
      } else if (data.type === 'meeting_reminder' && data.booking_id) {
        // Handle meeting reminder - open meeting URL or navigate to bookings
        console.log('Meeting reminder clicked:', data.booking_id);
        if (data.meeting_url) {
          console.log('Opening meeting URL:', data.meeting_url);
          // TODO: Open meeting URL in WebBrowser or navigate to booking details
        }
      }

      if (onNotificationResponse) {
        onNotificationResponse(response);
      }
    });
  }

  /**
   * Remove notification listeners
   */
  removeNotificationListeners() {
    if (this.notificationListener) {
      this.notificationListener.remove();
    }
    if (this.responseListener) {
      this.responseListener.remove();
    }
  }

  /**
   * Schedule a local notification (fallback for offline scenarios)
   */
  async scheduleLocalNotification(
    title: string,
    body: string,
    trigger: Notifications.NotificationTriggerInput,
    data?: any
  ): Promise<string | null> {
    try {
      const notificationId = await Notifications.scheduleNotificationAsync({
        content: {
          title,
          body,
          data: data || {},
          sound: 'default',
        },
        trigger,
      });

      console.log('Local notification scheduled:', notificationId);
      return notificationId;
    } catch (error) {
      console.error('Error scheduling local notification:', error);
      return null;
    }
  }

  /**
   * Cancel a scheduled local notification
   */
  async cancelLocalNotification(notificationId: string): Promise<void> {
    try {
      await Notifications.cancelScheduledNotificationAsync(notificationId);
      console.log('Notification canceled:', notificationId);
    } catch (error) {
      console.error('Error canceling notification:', error);
    }
  }

  /**
   * Cancel all scheduled local notifications
   */
  async cancelAllLocalNotifications(): Promise<void> {
    try {
      await Notifications.cancelAllScheduledNotificationsAsync();
      console.log('All notifications canceled');
    } catch (error) {
      console.error('Error canceling all notifications:', error);
    }
  }

  /**
   * Get all scheduled local notifications
   */
  async getScheduledNotifications(): Promise<Notifications.NotificationRequest[]> {
    try {
      return await Notifications.getAllScheduledNotificationsAsync();
    } catch (error) {
      console.error('Error getting scheduled notifications:', error);
      return [];
    }
  }

  /**
   * Get badge count
   */
  async getBadgeCount(): Promise<number> {
    try {
      return await Notifications.getBadgeCountAsync();
    } catch (error) {
      console.error('Error getting badge count:', error);
      return 0;
    }
  }

  /**
   * Set badge count
   */
  async setBadgeCount(count: number): Promise<void> {
    try {
      await Notifications.setBadgeCountAsync(count);
    } catch (error) {
      console.error('Error setting badge count:', error);
    }
  }

  /**
   * Clear badge count
   */
  async clearBadge(): Promise<void> {
    await this.setBadgeCount(0);
  }

  /**
   * Schedule a local notification for a task reminder
   * This creates a fallback notification on the device in case remote push fails
   *
   * @param task - Task object with scheduled_date, scheduled_time, and reminder_time
   * @returns notificationId that can be used to cancel the notification later
   */
  async scheduleTaskReminder(task: {
    id: number;
    title: string;
    scheduled_date: string;
    scheduled_time?: string;
    reminder_time?: string;
  }): Promise<string | null> {
    try {
      // If no reminder_time, we can't schedule
      if (!task.reminder_time) {
        console.warn(`Task ${task.id} has no reminder_time, skipping local notification`);
        return null;
      }

      // Parse reminder_time (ISO format from backend)
      const reminderDate = new Date(task.reminder_time);

      // Check if reminder is in the future
      const now = new Date();
      if (reminderDate <= now) {
        console.warn(`Reminder time for task ${task.id} is in the past, skipping`);
        return null;
      }

      // Schedule the notification
      const notificationId = await this.scheduleLocalNotification(
        'Task Reminder',
        `'${task.title}' starts soon`,
        {
          date: reminderDate,
        },
        {
          type: 'task_reminder',
          task_id: task.id,
          task_title: task.title,
        }
      );

      if (notificationId) {
        // Store notification ID in AsyncStorage for later cancellation
        await AsyncStorage.setItem(
          `task_notification_${task.id}`,
          notificationId
        );

        console.log(`Scheduled local reminder for task ${task.id} at ${reminderDate.toISOString()}`);
      }

      return notificationId;
    } catch (error) {
      console.error(`Error scheduling local reminder for task ${task.id}:`, error);
      return null;
    }
  }

  /**
   * Cancel a scheduled task reminder
   *
   * @param taskId - ID of the task
   */
  async cancelTaskReminder(taskId: number): Promise<void> {
    try {
      // Get notification ID from AsyncStorage
      const notificationId = await AsyncStorage.getItem(`task_notification_${taskId}`);

      if (notificationId) {
        await this.cancelLocalNotification(notificationId);
        await AsyncStorage.removeItem(`task_notification_${taskId}`);
        console.log(`Cancelled local reminder for task ${taskId}`);
      }
    } catch (error) {
      console.error(`Error cancelling reminder for task ${taskId}:`, error);
    }
  }

  /**
   * Update a task reminder (cancel old and schedule new)
   * Use this when a task is rescheduled
   *
   * @param task - Updated task object
   */
  async updateTaskReminder(task: {
    id: number;
    title: string;
    scheduled_date: string;
    scheduled_time?: string;
    reminder_time?: string;
  }): Promise<string | null> {
    try {
      // Cancel existing reminder
      await this.cancelTaskReminder(task.id);

      // Schedule new reminder
      return await this.scheduleTaskReminder(task);
    } catch (error) {
      console.error(`Error updating reminder for task ${task.id}:`, error);
      return null;
    }
  }

  /**
   * Get all scheduled task reminders
   * Useful for debugging or showing user what's scheduled
   */
  async getScheduledTaskReminders(): Promise<{ taskId: string; notificationId: string }[]> {
    try {
      const allKeys = await AsyncStorage.getAllKeys();
      const taskNotificationKeys = allKeys.filter(key => key.startsWith('task_notification_'));

      const reminders = [];
      for (const key of taskNotificationKeys) {
        const notificationId = await AsyncStorage.getItem(key);
        if (notificationId) {
          const taskId = key.replace('task_notification_', '');
          reminders.push({ taskId, notificationId });
        }
      }

      return reminders;
    } catch (error) {
      console.error('Error getting scheduled task reminders:', error);
      return [];
    }
  }

  /**
   * Clear all task reminders
   * Use when user disables task reminders in settings
   */
  async clearAllTaskReminders(): Promise<void> {
    try {
      const reminders = await this.getScheduledTaskReminders();

      for (const { taskId, notificationId } of reminders) {
        await this.cancelLocalNotification(notificationId);
        await AsyncStorage.removeItem(`task_notification_${taskId}`);
      }

      console.log(`Cleared ${reminders.length} task reminders`);
    } catch (error) {
      console.error('Error clearing all task reminders:', error);
    }
  }

  /**
   * Schedule a local notification for a meeting reminder
   * This creates a fallback notification on the device in case remote push fails
   *
   * @param booking - Booking object with start_at_utc and meeting_url
   * @param minutesBefore - Minutes before meeting to send reminder (default: 15)
   * @returns notificationId that can be used to cancel the notification later
   */
  async scheduleMeetingReminder(
    booking: {
      id: number;
      mentor_title?: string;
      start_at_utc: string;
      meeting_url?: string;
    },
    minutesBefore: number = 15
  ): Promise<string | null> {
    try {
      // Calculate reminder time
      const meetingTime = new Date(booking.start_at_utc);
      const reminderTime = new Date(meetingTime.getTime() - minutesBefore * 60 * 1000);

      // Check if reminder is in the future
      const now = new Date();
      if (reminderTime <= now) {
        console.warn(`Reminder time for booking ${booking.id} is in the past, skipping`);
        return null;
      }

      // Schedule the notification
      const notificationId = await this.scheduleLocalNotification(
        '🔔 Meeting Starting Soon!',
        `Your session${booking.mentor_title ? ` with ${booking.mentor_title}` : ''} starts in ${minutesBefore} minutes. Get ready!`,
        {
          date: reminderTime,
        },
        {
          type: 'meeting_reminder',
          booking_id: booking.id,
          reminder_type: `${minutesBefore}min`,
          meeting_url: booking.meeting_url,
          mentor_name: booking.mentor_title,
        }
      );

      if (notificationId) {
        // Store notification ID in AsyncStorage for later cancellation
        await AsyncStorage.setItem(
          `meeting_notification_${booking.id}`,
          notificationId
        );

        console.log(`Scheduled local reminder for booking ${booking.id} at ${reminderTime.toISOString()}`);
      }

      return notificationId;
    } catch (error) {
      console.error(`Error scheduling local reminder for booking ${booking.id}:`, error);
      return null;
    }
  }

  /**
   * Cancel a scheduled meeting reminder
   *
   * @param bookingId - ID of the booking
   */
  async cancelMeetingReminder(bookingId: number): Promise<void> {
    try {
      // Get notification ID from AsyncStorage
      const notificationId = await AsyncStorage.getItem(`meeting_notification_${bookingId}`);

      if (notificationId) {
        await this.cancelLocalNotification(notificationId);
        await AsyncStorage.removeItem(`meeting_notification_${bookingId}`);
        console.log(`Cancelled local reminder for booking ${bookingId}`);
      }
    } catch (error) {
      console.error(`Error cancelling reminder for booking ${bookingId}:`, error);
    }
  }

  /**
   * Update a meeting reminder (cancel old and schedule new)
   * Use this when a booking is rescheduled
   *
   * @param booking - Updated booking object
   * @param minutesBefore - Minutes before meeting to send reminder (default: 15)
   */
  async updateMeetingReminder(
    booking: {
      id: number;
      mentor_title?: string;
      start_at_utc: string;
      meeting_url?: string;
    },
    minutesBefore: number = 15
  ): Promise<string | null> {
    try {
      // Cancel existing reminder
      await this.cancelMeetingReminder(booking.id);

      // Schedule new reminder
      return await this.scheduleMeetingReminder(booking, minutesBefore);
    } catch (error) {
      console.error(`Error updating reminder for booking ${booking.id}:`, error);
      return null;
    }
  }

  /**
   * Initialize notification service
   * Call this on app start
   */
  async initialize(
    onNotificationReceived?: (notification: Notifications.Notification) => void,
    onNotificationResponse?: (response: Notifications.NotificationResponse) => void
  ): Promise<boolean> {
    try {
      // Configure notification handler for foreground notifications
      Notifications.setNotificationHandler({
        handleNotification: async () => ({
          shouldShowAlert: true,
          shouldPlaySound: true,
          shouldSetBadge: true,
        }),
      });

      // Setup listeners
      this.setupNotificationListeners(onNotificationReceived, onNotificationResponse);

      // Register for push notifications
      const token = await this.registerForPushNotifications();

      if (token) {
        // Send token to backend
        const success = await this.sendTokenToBackend(token);
        return success;
      }

      return false;
    } catch (error) {
      console.error('Error initializing notification service:', error);
      return false;
    }
  }

  /**
   * Get current push token
   */
  getPushToken(): string | null {
    return this.pushToken;
  }
}

// Notification API for backend communication
export const notificationsAPI = {
  /**
   * Register push token with backend
   */
  registerToken: (pushToken: string) =>
    api.post('/notifications/register-token/', { push_token: pushToken }),

  /**
   * Get notification preferences
   */
  getPreferences: () =>
    api.get<NotificationPreferences>('/notifications/preferences/'),

  /**
   * Update notification preferences
   */
  updatePreferences: (preferences: Partial<NotificationPreferences>) =>
    api.patch('/notifications/preferences/', preferences),

  /**
   * Send test notification
   */
  sendTest: () =>
    api.post('/notifications/test/'),
};

// Export singleton instance
export const notificationService = new NotificationService();

export default notificationService;
