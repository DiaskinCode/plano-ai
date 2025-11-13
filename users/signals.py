"""
User signals for automatic setup
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, NotificationPreferences


@receiver(post_save, sender=User)
def create_notification_preferences(sender, instance, created, **kwargs):
    """
    Automatically create NotificationPreferences when a new User is created
    """
    if created:
        NotificationPreferences.objects.create(
            user=instance,
            task_reminders_enabled=True,
            task_reminder_minutes_before=5,
            deadline_notifications_enabled=True,
            ai_motivation_enabled=True,
            daily_pulse_reminder_enabled=True
        )
        print(f'✅ Created NotificationPreferences for user: {instance.email}')
