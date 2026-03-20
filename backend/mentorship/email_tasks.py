"""
Celery tasks for email reminders

Tasks:
- send_24h_reminders: Send email reminders 24 hours before meetings
- send_1h_reminders: Send email reminders 1 hour before meetings
"""

from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from .models import MentorBooking
from .email_service import send_meeting_reminder_email


@shared_task
def send_24h_reminders():
    """
    Send email reminders 24 hours before meetings

    Runs every hour to check for meetings starting in 23-25 hours
    """
    now = timezone.now()
    twenty_three_hours_from_now = now + timedelta(hours=23)
    twenty_five_hours_from_now = now + timedelta(hours=25)

    # Find confirmed meetings starting in 23-25 hours
    upcoming_bookings = MentorBooking.objects.filter(
        status="confirmed",
        start_at_utc__gt=twenty_three_hours_from_now,
        start_at_utc__lte=twenty_five_hours_from_now,
    ).select_related("mentor", "mentor__user", "student")

    reminders_sent = 0

    for booking in upcoming_bookings:
        try:
            # Check if we haven't sent a 24h reminder yet
            # (We'll track this via notification logs)
            send_meeting_reminder_email(booking, reminder_type="24h")
            reminders_sent += 1
        except Exception as e:
            print(f"Error sending 24h reminder for booking {booking.id}: {e}")

    return {
        "reminders_sent": reminders_sent,
    }


@shared_task
def send_1h_reminders():
    """
    Send email reminders 1 hour before meetings

    Runs every 5 minutes to check for meetings starting in 58-62 minutes
    """
    now = timezone.now()
    fifty_eight_minutes_from_now = now + timedelta(minutes=58)
    sixty_two_minutes_from_now = now + timedelta(minutes=62)

    # Find confirmed meetings starting in 58-62 minutes
    upcoming_bookings = MentorBooking.objects.filter(
        status="confirmed",
        start_at_utc__gt=fifty_eight_minutes_from_now,
        start_at_utc__lte=sixty_two_minutes_from_now,
    ).select_related("mentor", "mentor__user", "student")

    reminders_sent = 0

    for booking in upcoming_bookings:
        try:
            send_meeting_reminder_email(booking, reminder_type="1h")
            reminders_sent += 1
        except Exception as e:
            print(f"Error sending 1h reminder for booking {booking.id}: {e}")

    return {
        "reminders_sent": reminders_sent,
    }
