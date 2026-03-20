"""
Celery tasks for mentorship session reminders

Tasks:
- check_and_send_session_reminders: Sends reminders 24h and 1h before sessions
- send_15min_meeting_reminders: Sends push notifications 15 minutes before meetings
"""

from datetime import timedelta

from celery import shared_task
from django.db.models import Q
from django.utils import timezone

from .models import MentorBooking
from .notification_service import NotificationService


@shared_task
def check_and_send_session_reminders():
    """
    Check for upcoming sessions and send reminders

    Runs every hour to check for sessions that need reminders:
    - 24 hours before session
    - 1 hour before session
    """
    now = timezone.now()
    one_hour_from_now = now + timedelta(hours=1)
    twenty_four_hours_from_now = now + timedelta(hours=24)

    # Find sessions that need 24h reminder
    # Sessions in the next hour that haven't had a 24h reminder yet
    sessions_24h = (
        MentorBooking.objects.filter(
            status="confirmed",
            start_at_utc__gt=now,
            start_at_utc__lte=one_hour_from_now,
        )
        .exclude(
            # Exclude if we already sent a 24h reminder (we track this via notification)
            notifications__notification_type="session_reminder",
            notifications__data__reminder_type="24h",
        )
        .select_related("mentor", "mentor__user", "student")
    )

    for booking in sessions_24h:
        try:
            NotificationService.create_notification(
                recipient=booking.mentor.user,
                notification_type="session_reminder",
                title="Session Reminder: 24 Hours",
                message=f"Session with {booking.student.profile.name if hasattr(booking.student, 'profile') else booking.student.email} in 24 hours.",
                data={
                    "type": "booking",
                    "booking_id": booking.id,
                    "reminder_type": "24h",
                    "meeting_url": booking.meeting_url,
                },
            )

            NotificationService.create_notification(
                recipient=booking.student,
                notification_type="session_reminder",
                title="Session Reminder: 24 Hours",
                message=f"Your session with {booking.mentor.title} is in 24 hours.",
                data={
                    "type": "booking",
                    "booking_id": booking.id,
                    "reminder_type": "24h",
                    "meeting_url": booking.meeting_url,
                },
            )
        except Exception as e:
            print(f"Error sending 24h reminder for booking {booking.id}: {e}")

    # Find sessions that need 1h reminder
    # Sessions starting in the next 5 minutes that haven't had a 1h reminder
    sessions_1h = (
        MentorBooking.objects.filter(
            status="confirmed",
            start_at_utc__gt=now,
            start_at_utc__lte=one_hour_from_now,
        )
        .exclude(
            notifications__notification_type="session_reminder",
            notifications__data__reminder_type="1h",
        )
        .select_related("mentor", "mentor__user", "student")
    )

    for booking in sessions_1h:
        try:
            NotificationService.create_notification(
                recipient=booking.mentor.user,
                notification_type="session_reminder",
                title="Session Starting Soon!",
                message=f"Session with {booking.student.profile.name if hasattr(booking.student, 'profile') else booking.student.email} starts in 1 hour.",
                data={
                    "type": "booking",
                    "booking_id": booking.id,
                    "reminder_type": "1h",
                    "meeting_url": booking.meeting_url,
                },
            )

            NotificationService.create_notification(
                recipient=booking.student,
                notification_type="session_reminder",
                title="Session Starting Soon!",
                message=f"Your session with {booking.mentor.title} starts in 1 hour.",
                data={
                    "type": "booking",
                    "booking_id": booking.id,
                    "reminder_type": "1h",
                    "meeting_url": booking.meeting_url,
                },
            )
        except Exception as e:
            print(f"Error sending 1h reminder for booking {booking.id}: {e}")

    return {
        "24h_reminders_sent": sessions_24h.count(),
        "1h_reminders_sent": sessions_1h.count(),
    }


@shared_task
def expire_requested_bookings():
    """
    Expire booking requests that haven't been confirmed

    Runs every 15 minutes to cancel requested bookings that are older than 15 minutes
    This prevents "ghost blocking" of time slots
    """
    expire_time = timezone.now() - timedelta(minutes=15)

    expired_bookings = MentorBooking.objects.filter(
        status="requested", created_at__lt=expire_time
    )

    count = expired_bookings.count()
    expired_bookings.update(status="cancelled")

    return {"expired_bookings": count}


@shared_task
def send_15min_meeting_reminders():
    """
    Send push notifications 15 minutes before meetings

    Runs every 5 minutes to check for meetings starting in 13-17 minutes
    Sends notifications to both student and mentor
    """
    now = timezone.now()
    thirteen_minutes_from_now = now + timedelta(minutes=13)
    seventeen_minutes_from_now = now + timedelta(minutes=17)

    # Find confirmed meetings starting in 13-17 minutes that haven't had reminders sent
    upcoming_bookings = MentorBooking.objects.filter(
        status="confirmed",
        start_at_utc__gt=thirteen_minutes_from_now,
        start_at_utc__lte=seventeen_minutes_from_now,
        reminder_sent=False,
    ).select_related("mentor", "mentor__user", "student")

    reminders_sent = 0

    for booking in upcoming_bookings:
        try:
            # Get meeting time in user's timezone
            meeting_time = booking.start_at_utc.strftime("%I:%M %p")

            # Send notification to student
            NotificationService.create_notification(
                recipient=booking.student,
                notification_type="meeting_reminder_15min",
                title="🔔 Meeting Starting Soon!",
                message=f"Your session with {booking.mentor.title} starts at {meeting_time}. Get ready!",
                data={
                    "type": "meeting_reminder",
                    "booking_id": booking.id,
                    "reminder_type": "15min",
                    "meeting_url": booking.meeting_url,
                    "mentor_name": booking.mentor.title,
                    "meeting_time": meeting_time,
                },
            )

            # Send notification to mentor
            NotificationService.create_notification(
                recipient=booking.mentor.user,
                notification_type="meeting_reminder_15min",
                title="🔔 Meeting Starting Soon!",
                message=f"Session with {booking.student.email if hasattr(booking.student, 'email') else 'your student'} starts at {meeting_time}. Get ready!",
                data={
                    "type": "meeting_reminder",
                    "booking_id": booking.id,
                    "reminder_type": "15min",
                    "meeting_url": booking.meeting_url,
                    "student_email": booking.student.email if hasattr(booking.student, 'email') else 'student',
                    "meeting_time": meeting_time,
                },
            )

            # Mark reminder as sent
            booking.reminder_sent = True
            booking.save(update_fields=["reminder_sent"])

            reminders_sent += 1

        except Exception as e:
            print(f"Error sending 15min reminder for booking {booking.id}: {e}")

    return {
        "reminders_sent": reminders_sent,
    }


@shared_task
def update_mentor_stats(mentor_id):
    """
    Update mentor statistics (rating, total sessions)

    Should be called after each completed booking
    """
    from django.db.models import Avg, Count

    try:
        from .models import MentorProfile

        mentor = MentorProfile.objects.get(id=mentor_id)

        # Calculate rating from reviews
        completed_bookings = MentorBooking.objects.filter(
            mentor=mentor, status="completed", rating__isnull=False
        )

        if completed_bookings.exists():
            avg_rating = completed_bookings.aggregate(avg_rating=Avg("rating"))[
                "avg_rating"
            ]
            mentor.rating = round(avg_rating, 2) if avg_rating else 0.0
        else:
            mentor.rating = 0.0

        # Count total sessions
        mentor.total_sessions = MentorBooking.objects.filter(
            mentor=mentor, status="completed"
        ).count()

        mentor.save()

        return {
            "mentor_id": mentor_id,
            "rating": mentor.rating,
            "total_sessions": mentor.total_sessions,
        }

    except MentorProfile.DoesNotExist:
        return {"error": f"Mentor {mentor_id} not found"}
