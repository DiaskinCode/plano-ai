"""
Django signals for Todo model
Automatically calculate and set reminder_time when tasks are created or updated
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import datetime, timedelta
import logging
import pytz

from .models import Todo

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Todo)
def set_reminder_time(sender, instance, created, **kwargs):
    """
    Automatically calculate and set reminder_time when a task is created or updated

    This runs after a Todo is saved and:
    1. Checks if the task has a scheduled_date and scheduled_time
    2. Gets user's reminder preference (minutes before)
    3. Calculates reminder_time = scheduled_datetime - reminder_minutes
    4. Updates the task's reminder_time field

    Args:
        sender: The model class (Todo)
        instance: The actual Todo instance being saved
        created: Boolean indicating if this is a new instance
        **kwargs: Additional keyword arguments
    """
    # Skip if task is already done or skipped
    if instance.status in ['done', 'skipped']:
        return

    # Skip if no scheduled time (can't calculate exact reminder)
    if not instance.scheduled_time:
        return

    # Get user's notification preferences (create if doesn't exist)
    from users.models import NotificationPreferences

    try:
        prefs, created = NotificationPreferences.objects.get_or_create(
            user=instance.user,
            defaults={
                'task_reminders_enabled': True,
                'task_reminder_minutes_before': 15,
                'deadline_notifications_enabled': True,
                'ai_motivation_enabled': True,
                'daily_pulse_reminder_enabled': True
            }
        )

        if created:
            logger.info(f"Created notification preferences for user {instance.user.id}")

        # Skip if user doesn't have task reminders enabled
        if not prefs.task_reminders_enabled:
            return

        reminder_minutes = prefs.task_reminder_minutes_before
    except Exception as e:
        # Fallback to default 15 minutes if there's any error
        logger.warning(f"Error getting notification preferences for user {instance.user.id}: {e}, using default 15 minutes")
        reminder_minutes = 15

    # Calculate scheduled datetime
    try:
        # Get user's timezone
        user_tz_str = instance.user.timezone if instance.user.timezone else 'UTC'
        user_tz = pytz.timezone(user_tz_str)

        # Create timezone-aware datetime in user's timezone
        scheduled_datetime = datetime.combine(
            instance.scheduled_date,
            instance.scheduled_time
        )
        scheduled_datetime = user_tz.localize(scheduled_datetime)

        # Calculate reminder time
        reminder_datetime = scheduled_datetime - timedelta(minutes=reminder_minutes)

        # Convert to UTC for storage
        reminder_datetime_utc = reminder_datetime.astimezone(pytz.UTC)

        # Only update if reminder_time has changed or is not set
        # This prevents infinite loop since we're in post_save
        if instance.reminder_time != reminder_datetime_utc:
            # Use update() to avoid triggering post_save again
            Todo.objects.filter(pk=instance.pk).update(
                reminder_time=reminder_datetime_utc
            )

            logger.info(
                f"Set reminder_time for task {instance.id} ({instance.title}): "
                f"{reminder_datetime_utc} (UTC) / {reminder_datetime} ({user_tz_str}) "
                f"({reminder_minutes} min before {scheduled_datetime})"
            )

    except Exception as e:
        logger.error(f"Error calculating reminder_time for task {instance.id}: {e}")
        import traceback
        traceback.print_exc()


@receiver(post_save, sender=Todo)
def reset_reminder_sent_on_reschedule(sender, instance, created, **kwargs):
    """
    Reset reminder_sent flag when a task is rescheduled

    This ensures that if a user reschedules a task to a different time,
    they will get a new reminder for the new time.

    Args:
        sender: The model class (Todo)
        instance: The actual Todo instance being saved
        created: Boolean indicating if this is a new instance
        **kwargs: Additional keyword arguments
    """
    # Only process updates (not new tasks)
    if created:
        return

    # Skip if task is done or skipped
    if instance.status in ['done', 'skipped']:
        return

    # If the task was previously marked as reminder_sent
    # but the scheduled time changed, reset the flag
    if instance.reminder_sent and instance.reminder_time:
        # Check if reminder_time is in the future
        now = timezone.now()
        if instance.reminder_time > now:
            # Check if the task's update_at timestamp is very recent
            # (indicating it was just rescheduled)
            time_since_update = now - instance.updated_at
            if time_since_update.total_seconds() < 5:  # Within last 5 seconds
                # Reset reminder_sent flag
                Todo.objects.filter(pk=instance.pk).update(reminder_sent=False)
                logger.info(f"Reset reminder_sent for rescheduled task {instance.id}")
