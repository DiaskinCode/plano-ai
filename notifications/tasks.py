"""
Celery tasks for sending notifications
"""
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from todos.models import Todo
from users.models import User
from .service import NotificationService
import logging

logger = logging.getLogger(__name__)


@shared_task
def check_and_send_task_reminders():
    """
    Periodic task to check for upcoming tasks and send reminders
    Runs every 10 minutes

    OPTIMIZED: Uses pre-computed reminder_time field instead of calculating on the fly.
    This is more efficient and accurate since reminder_time is set automatically
    by Django signals when tasks are created or updated.
    """
    service = NotificationService()
    now = timezone.now()

    # Define a time window to catch reminders (±2 minutes)
    # This accounts for Celery task scheduling delays
    reminder_time_start = now - timedelta(minutes=2)
    reminder_time_end = now + timedelta(minutes=2)

    # OPTIMIZED QUERY: Use pre-computed reminder_time field
    # Much more efficient than calculating time windows per-user
    upcoming_tasks = Todo.objects.filter(
        reminder_time__gte=reminder_time_start,
        reminder_time__lte=reminder_time_end,
        reminder_sent=False,
        status__in=['pending', 'ready'],
        # Only for users with push enabled and task reminders enabled
        user__push_token__isnull=False,
        user__push_enabled=True,
        user__notification_preferences__task_reminders_enabled=True
    ).select_related('user', 'user__notification_preferences')

    logger.info(f"Found {upcoming_tasks.count()} tasks needing reminders")

    for task in upcoming_tasks:
        try:
            result = service.send_task_reminder(task)
            if result.get('success'):
                task.reminder_sent = True
                task.save(update_fields=['reminder_sent'])
                logger.info(f"Sent reminder for task {task.id} ({task.title}) to {task.user.email}")
            else:
                logger.warning(f"Failed to send reminder for task {task.id}: {result.get('error')}")

        except Exception as e:
            logger.error(f"Error sending reminder for task {task.id}: {str(e)}")


@shared_task
def check_and_send_deadline_notifications():
    """
    Check for approaching deadlines and send notifications
    Runs daily
    """
    service = NotificationService()
    today = timezone.now().date()

    # Check for tasks due tomorrow
    tomorrow = today + timedelta(days=1)
    tasks_tomorrow = Todo.objects.filter(
        scheduled_date=tomorrow,
        status__in=['pending', 'ready', 'in_progress'],
        user__push_enabled=True,
        user__notification_preferences__deadline_notifications_enabled=True
    ).select_related('user')

    for task in tasks_tomorrow:
        service.send_deadline_notification(task, days_until=1)

    # Check for overdue tasks
    overdue_tasks = Todo.objects.filter(
        scheduled_date__lt=today,
        status__in=['pending', 'ready', 'in_progress'],
        user__push_enabled=True,
        user__notification_preferences__deadline_notifications_enabled=True
    ).select_related('user')

    for task in overdue_tasks[:10]:  # Limit to avoid spam
        service.send_deadline_notification(task, days_until=None)


@shared_task
def send_daily_pulse_reminders():
    """
    Send daily pulse reminders to users
    Scheduled at user's preferred time
    """
    service = NotificationService()

    users = User.objects.filter(
        push_enabled=True,
        notification_preferences__daily_pulse_reminder_enabled=True
    ).select_related('notification_preferences')

    for user in users:
        try:
            service.send_daily_pulse_reminder(user)
            logger.info(f"Sent daily pulse reminder to {user.email}")
        except Exception as e:
            logger.error(f"Error sending daily pulse to {user.id}: {str(e)}")


@shared_task
def send_ai_motivation_messages():
    """
    Send motivational messages to users
    Can be scheduled for morning or evening
    """
    service = NotificationService()

    users = User.objects.filter(
        push_enabled=True,
        notification_preferences__ai_motivation_enabled=True
    )

    # You can add logic to generate personalized messages using AI
    for user in users:
        try:
            service.send_ai_motivation(user)
            logger.info(f"Sent AI motivation to {user.email}")
        except Exception as e:
            logger.error(f"Error sending motivation to {user.id}: {str(e)}")
