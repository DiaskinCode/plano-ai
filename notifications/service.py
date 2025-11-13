"""
Notification Service for sending push notifications via Expo
"""
from exponent_server_sdk import (
    DeviceNotRegisteredError,
    PushClient,
    PushMessage,
    PushServerError,
    PushTicketError,
)
from requests.exceptions import ConnectionError, HTTPError
import logging

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Service for sending push notifications to users
    Uses Expo Push Notification service
    """

    def __init__(self):
        self.client = PushClient()

    def send_push_notification(self, user, title, body, data=None):
        """
        Send a push notification to a user

        Args:
            user: User object with push_token
            title (str): Notification title
            body (str): Notification body/message
            data (dict): Optional data payload

        Returns:
            dict: {'success': bool, 'message': str, 'error': str}
        """
        if not user.push_token:
            logger.warning(f"User {user.email} has no push token")
            return {
                'success': False,
                'error': 'No push token registered'
            }

        if not user.push_enabled:
            logger.info(f"Push notifications disabled for user {user.email}")
            return {
                'success': False,
                'error': 'Push notifications disabled'
            }

        # Check quiet hours
        try:
            prefs = user.notification_preferences
            if prefs.is_quiet_hours():
                logger.info(f"Quiet hours active for user {user.email}")
                return {
                    'success': False,
                    'error': 'Quiet hours active'
                }
        except Exception as e:
            logger.warning(f"Could not check quiet hours for {user.email}: {e}")

        try:
            # Create push message
            message = PushMessage(
                to=user.push_token,
                title=title,
                body=body,
                data=data or {},
                sound='default',
                priority='high'
            )

            # Send the notification
            response = self.client.publish(message)

            logger.info(f"Push notification sent to {user.email}: {title}")
            return {
                'success': True,
                'message': 'Notification sent successfully',
                'ticket_id': response.id if hasattr(response, 'id') else None
            }

        except PushServerError as exc:
            # Expo responded with an error
            logger.error(f"Push server error for {user.email}: {exc.errors}")
            return {
                'success': False,
                'error': f'Push server error: {str(exc)}'
            }

        except (ConnectionError, HTTPError) as exc:
            # Network/HTTP errors
            logger.error(f"Network error sending push to {user.email}: {str(exc)}")
            return {
                'success': False,
                'error': f'Network error: {str(exc)}'
            }

        except DeviceNotRegisteredError:
            # The token is no longer valid, clear it
            logger.warning(f"Device not registered for {user.email}, clearing token")
            user.push_token = None
            user.save()
            return {
                'success': False,
                'error': 'Device not registered (token cleared)'
            }

        except Exception as exc:
            # Catch-all for unexpected errors
            logger.error(f"Unexpected error sending push to {user.email}: {str(exc)}")
            return {
                'success': False,
                'error': f'Unexpected error: {str(exc)}'
            }

    def send_task_reminder(self, task):
        """
        Send a reminder about an upcoming task

        Args:
            task: Todo object

        Returns:
            dict: Result of send_push_notification
        """
        user = task.user

        # Check if task reminders are enabled
        try:
            if not user.notification_preferences.task_reminders_enabled:
                return {'success': False, 'error': 'Task reminders disabled'}
        except:
            pass

        title = "Task Reminder"
        body = f"'{task.title}' starts soon"

        data = {
            'type': 'task_reminder',
            'task_id': task.id,
            'task_title': task.title,
            'scheduled_time': task.scheduled_time.isoformat() if task.scheduled_time else None
        }

        return self.send_push_notification(user, title, body, data)

    def send_deadline_notification(self, task, days_until=None):
        """
        Send notification about approaching deadline

        Args:
            task: Todo object
            days_until (int): Days until deadline

        Returns:
            dict: Result of send_push_notification
        """
        user = task.user

        # Check if deadline notifications are enabled
        try:
            if not user.notification_preferences.deadline_notifications_enabled:
                return {'success': False, 'error': 'Deadline notifications disabled'}
        except:
            pass

        if days_until is not None:
            if days_until == 0:
                title = "Deadline Today!"
                body = f"'{task.title}' is due today"
            elif days_until == 1:
                title = "Deadline Tomorrow"
                body = f"'{task.title}' is due tomorrow"
            else:
                title = f"Deadline in {days_until} days"
                body = f"'{task.title}' is due in {days_until} days"
        else:
            title = "Task Overdue"
            body = f"'{task.title}' is overdue"

        data = {
            'type': 'deadline',
            'task_id': task.id,
            'task_title': task.title,
            'days_until': days_until
        }

        return self.send_push_notification(user, title, body, data)

    def send_daily_pulse_reminder(self, user):
        """
        Send reminder to complete daily pulse

        Args:
            user: User object

        Returns:
            dict: Result of send_push_notification
        """
        # Check if daily pulse reminders are enabled
        try:
            if not user.notification_preferences.daily_pulse_reminder_enabled:
                return {'success': False, 'error': 'Daily pulse reminders disabled'}
        except:
            pass

        title = "Daily Check-in"
        body = "How did your day go? Take a moment to reflect"

        data = {
            'type': 'daily_pulse',
            'action': 'open_daily_pulse'
        }

        return self.send_push_notification(user, title, body, data)

    def send_ai_motivation(self, user, message=None):
        """
        Send motivational message from AI coach

        Args:
            user: User object
            message (str): Custom message (if None, will use default)

        Returns:
            dict: Result of send_push_notification
        """
        # Check if AI motivation is enabled
        try:
            if not user.notification_preferences.ai_motivation_enabled:
                return {'success': False, 'error': 'AI motivation disabled'}
        except:
            pass

        title = "Your AI Coach"
        body = message or "You've got this! Keep pushing towards your goals 💪"

        data = {
            'type': 'ai_motivation',
            'action': 'open_app'
        }

        return self.send_push_notification(user, title, body, data)
