"""
Celery configuration for PathAI backend
"""
import os
from celery import Celery
from celery.schedules import crontab

# Set default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pathaibackend.settings')

# Create Celery app
app = Celery('pathaibackend')

# Load configuration from Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()


# Celery Beat Schedule (Periodic Tasks)
app.conf.beat_schedule = {
    # TASK REMINDERS - Critical for push notifications
    'check-and-send-task-reminders': {
        'task': 'notifications.tasks.check_and_send_task_reminders',
        'schedule': 300.0,  # Every 5 minutes (300 seconds)
        'options': {
            'expires': 240,  # Expires after 4 minutes if not picked up
        }
    },
    'check-and-send-deadline-notifications': {
        'task': 'notifications.tasks.check_and_send_deadline_notifications',
        'schedule': crontab(hour=8, minute=0),  # Daily at 8 AM
        'options': {
            'expires': 3600,
        }
    },
    'generate-weekly-reflections': {
        'task': 'analytics.generate_weekly_reflections',
        'schedule': crontab(day_of_week=0, hour=19, minute=0),  # Sunday 7 PM
        'options': {
            'expires': 3600,  # Task expires after 1 hour if not picked up
        }
    },
    'update-behavior-patterns': {
        'task': 'analytics.update_behavior_patterns',
        'schedule': crontab(hour=0, minute=30),  # Daily at 12:30 AM
        'options': {
            'expires': 7200,
        }
    },
    'cleanup-old-patterns': {
        'task': 'analytics.cleanup_old_patterns',
        'schedule': crontab(day_of_week=1, hour=2, minute=0),  # Monday 2 AM
        'options': {
            'expires': 3600,
        }
    },
    'generate-daily-pulse-morning': {
        'task': 'analytics.generate_daily_pulse_morning',
        'schedule': crontab(hour=7, minute=0),  # Daily at 7:00 AM
        'options': {
            'expires': 3600,  # Task expires after 1 hour if not picked up
        }
    },
}

# Celery Beat timezone
app.conf.timezone = 'UTC'


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing Celery"""
    print(f'Request: {self.request!r}')
