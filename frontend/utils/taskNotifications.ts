/**
 * Task Notification Helper
 *
 * Helper functions to integrate task creation/updates with local notification scheduling
 * This provides a seamless way to ensure tasks have both remote (Celery) and local notifications
 */

import notificationService from '@/services/notifications';

export interface Task {
  id: number;
  title: string;
  scheduled_date: string;
  scheduled_time?: string;
  reminder_time?: string;
  status?: string;
}

/**
 * Schedule local notification when a task is created or updated
 *
 * This should be called after successfully creating or updating a task via the API.
 * It will schedule a local notification as a fallback in case the remote push fails.
 *
 * @param task - Task object returned from API
 * @returns Promise<boolean> - true if notification was scheduled successfully
 *
 * @example
 * ```typescript
 * const response = await todosAPI.createTodo(taskData);
 * const task = response.data;
 * await scheduleNotificationForTask(task);
 * ```
 */
export async function scheduleNotificationForTask(task: Task): Promise<boolean> {
  try {
    // Skip if task is already done or skipped
    if (task.status && ['done', 'skipped'].includes(task.status)) {
      console.log(`Task ${task.id} is ${task.status}, skipping notification`);
      return false;
    }

    // Schedule local notification
    const notificationId = await notificationService.scheduleTaskReminder(task);

    if (notificationId) {
      console.log(`✅ Scheduled local notification for task ${task.id}: ${task.title}`);
      return true;
    } else {
      console.warn(`⚠️ Failed to schedule local notification for task ${task.id}`);
      return false;
    }
  } catch (error) {
    console.error(`❌ Error scheduling notification for task ${task.id}:`, error);
    return false;
  }
}

/**
 * Update local notification when a task is rescheduled
 *
 * This cancels the old notification and schedules a new one with updated time.
 *
 * @param task - Updated task object
 * @returns Promise<boolean> - true if notification was updated successfully
 *
 * @example
 * ```typescript
 * const response = await todosAPI.reschedule(taskId, newDate, newTime);
 * const task = response.data;
 * await updateNotificationForTask(task);
 * ```
 */
export async function updateNotificationForTask(task: Task): Promise<boolean> {
  try {
    const notificationId = await notificationService.updateTaskReminder(task);

    if (notificationId) {
      console.log(`✅ Updated local notification for task ${task.id}: ${task.title}`);
      return true;
    } else {
      console.warn(`⚠️ Failed to update local notification for task ${task.id}`);
      return false;
    }
  } catch (error) {
    console.error(`❌ Error updating notification for task ${task.id}:`, error);
    return false;
  }
}

/**
 * Cancel local notification when a task is completed, deleted, or skipped
 *
 * @param taskId - ID of the task
 * @returns Promise<void>
 *
 * @example
 * ```typescript
 * await todosAPI.markDone(taskId);
 * await cancelNotificationForTask(taskId);
 * ```
 */
export async function cancelNotificationForTask(taskId: number): Promise<void> {
  try {
    await notificationService.cancelTaskReminder(taskId);
    console.log(`✅ Cancelled local notification for task ${taskId}`);
  } catch (error) {
    console.error(`❌ Error cancelling notification for task ${taskId}:`, error);
  }
}

/**
 * Bulk schedule notifications for multiple tasks
 *
 * Useful when loading tasks from the API (e.g., daily planner, upcoming tasks)
 *
 * @param tasks - Array of tasks
 * @returns Promise<number> - Number of successfully scheduled notifications
 *
 * @example
 * ```typescript
 * const response = await todosAPI.getTodos('today');
 * const tasks = response.data.results;
 * const scheduled = await scheduleNotificationsForTasks(tasks);
 * console.log(`Scheduled ${scheduled} notifications`);
 * ```
 */
export async function scheduleNotificationsForTasks(tasks: Task[]): Promise<number> {
  let successCount = 0;

  for (const task of tasks) {
    const success = await scheduleNotificationForTask(task);
    if (success) {
      successCount++;
    }
  }

  console.log(`📅 Scheduled ${successCount}/${tasks.length} task notifications`);
  return successCount;
}

/**
 * Sync local notifications with server state
 *
 * This fetches upcoming tasks from the server and ensures all have local notifications scheduled.
 * Can be called on app start or when user changes notification settings.
 *
 * @param getTodosFunction - Function to fetch todos (e.g., todosAPI.getTodos)
 * @returns Promise<number> - Number of notifications synced
 *
 * @example
 * ```typescript
 * import { todosAPI } from '@/services/api';
 * const synced = await syncTaskNotifications(() => todosAPI.getTodos('upcoming'));
 * ```
 */
export async function syncTaskNotifications(
  getTodosFunction: () => Promise<any>
): Promise<number> {
  try {
    console.log('🔄 Syncing task notifications with server...');

    const response = await getTodosFunction();
    const tasks = response.data.results || response.data || [];

    // Filter tasks that need notifications
    const tasksNeedingNotifications = tasks.filter((task: Task) => {
      return (
        task.scheduled_time &&
        task.reminder_time &&
        task.status &&
        !['done', 'skipped'].includes(task.status)
      );
    });

    const synced = await scheduleNotificationsForTasks(tasksNeedingNotifications);

    console.log(`✅ Synced ${synced} task notifications`);
    return synced;
  } catch (error) {
    console.error('❌ Error syncing task notifications:', error);
    return 0;
  }
}

/**
 * Clear all local task notifications
 *
 * Use when user disables task reminders in settings
 *
 * @example
 * ```typescript
 * // When user toggles off task reminders
 * if (!taskRemindersEnabled) {
 *   await clearAllTaskNotifications();
 * }
 * ```
 */
export async function clearAllTaskNotifications(): Promise<void> {
  try {
    await notificationService.clearAllTaskReminders();
    console.log('✅ Cleared all task notifications');
  } catch (error) {
    console.error('❌ Error clearing task notifications:', error);
  }
}
