"""
Email service for mentorship bookings

Handles sending emails for:
- Booking confirmations
- Meeting reminders (24h, 1h before)
- Cancellations
"""

import os
from datetime import timedelta

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.conf import settings


def send_booking_confirmation_email(booking):
    """
    Send booking confirmation email to both student and mentor

    Args:
        booking: MentorBooking instance
    """
    try:
        meeting_time = booking.start_at_utc.strftime("%I:%M %p %Z on %B %d, %Y")
        meeting_link = booking.meeting_url or booking.mentor.meeting_link

        # Email to student
        student_subject = f"✅ Mentor Session Confirmed with {booking.mentor.title}"
        student_message = f"""
Hi {booking.student.profile.name if hasattr(booking.student, 'profile') else 'Student'},

Your mentor session has been confirmed!

Mentor: {booking.mentor.title}
Date & Time: {meeting_time}
Duration: {booking.duration_minutes} minutes
{f"Topic: {booking.topic}" if booking.topic else ""}

{f"Meeting Link: {meeting_link}" if meeting_link else "Your mentor will share the meeting link shortly."}

Please join the meeting 5 minutes early. If you can't make it, please cancel in the app.

Best regards,
PathAI Team
        """.strip()

        send_mail(
            subject=student_subject,
            message=student_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[booking.student.email],
            fail_silently=True,
        )

        # Email to mentor
        mentor_subject = f"📅 New Session Booked: {booking.student.email if hasattr(booking.student, 'email') else 'Student'}"
        mentor_message = f"""
Hi {booking.mentor.title},

You have a new mentor session scheduled!

Student: {booking.student.profile.name if hasattr(booking.student, 'profile') else booking.student.email}
Date & Time: {meeting_time}
Duration: {booking.duration_minutes} minutes
{f"Topic: {booking.topic}" if booking.topic else ""}
{f"Student Notes: {booking.student_notes}" if booking.student_notes else ""}

{f"Meeting Link: {meeting_link}" if meeting_link else "Please share your meeting link with the student."}

Please be available 5 minutes before the session.

Best regards,
PathAI Team
        """.strip()

        send_mail(
            subject=mentor_subject,
            message=mentor_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[booking.mentor.user.email],
            fail_silently=True,
        )

        print(f"✓ Booking confirmation emails sent for booking {booking.id}")

    except Exception as e:
        print(f"✗ Error sending booking confirmation email: {e}")


def send_meeting_reminder_email(booking, reminder_type="24h"):
    """
    Send meeting reminder email to both student and mentor

    Args:
        booking: MentorBooking instance
        reminder_type: "24h" or "1h"
    """
    try:
        meeting_time = booking.start_at_utc.strftime("%I:%M %p %Z on %B %d, %Y")
        meeting_link = booking.meeting_url or booking.mentor.meeting_link

        time_phrase = "24 hours" if reminder_type == "24h" else "1 hour"

        # Email to student
        student_subject = f"🔔 Reminder: Mentor Session in {time_phrase}"
        student_message = f"""
Hi {booking.student.profile.name if hasattr(booking.student, 'profile') else 'Student'},

This is a friendly reminder that your mentor session is starting in {time_phrase}.

Mentor: {booking.mentor.title}
Date & Time: {meeting_time}
Duration: {booking.duration_minutes} minutes
{f"Topic: {booking.topic}" if booking.topic else ""}

{f"Meeting Link: {meeting_link}" if meeting_link else "Check the app for the meeting link."}

Please make sure you have a stable internet connection and join 5 minutes early.

Best regards,
PathAI Team
        """.strip()

        send_mail(
            subject=student_subject,
            message=student_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[booking.student.email],
            fail_silently=True,
        )

        # Email to mentor
        mentor_subject = f"🔔 Reminder: Session Starting in {time_phrase}"
        mentor_message = f"""
Hi {booking.mentor.title},

This is a friendly reminder that your mentor session is starting in {time_phrase}.

Student: {booking.student.profile.name if hasattr(booking.student, 'profile') else booking.student.email}
Date & Time: {meeting_time}
Duration: {booking.duration_minutes} minutes
{f"Topic: {booking.topic}" if booking.topic else ""}

{f"Meeting Link: {meeting_link}" if meeting_link else "Use your usual meeting link."}

Please be ready 5 minutes before the session.

Best regards,
PathAI Team
        """.strip()

        send_mail(
            subject=mentor_subject,
            message=mentor_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[booking.mentor.user.email],
            fail_silently=True,
        )

        print(f"✓ {reminder_type} reminder emails sent for booking {booking.id}")

    except Exception as e:
        print(f"✗ Error sending {reminder_type} reminder email: {e}")


def send_booking_cancellation_email(booking):
    """
    Send booking cancellation email to both student and mentor

    Args:
        booking: MentorBooking instance
    """
    try:
        meeting_time = booking.start_at_utc.strftime("%I:%M %p %Z on %B %d, %Y")

        # Email to student
        student_subject = "❌ Mentor Session Cancelled"
        student_message = f"""
Hi {booking.student.profile.name if hasattr(booking.student, 'profile') else 'Student'},

Your mentor session has been cancelled.

Mentor: {booking.mentor.title}
Originally scheduled for: {meeting_time}

If you'd like to reschedule, please book a new session through the app.

Best regards,
PathAI Team
        """.strip()

        send_mail(
            subject=student_subject,
            message=student_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[booking.student.email],
            fail_silently=True,
        )

        # Email to mentor
        mentor_subject = "❌ Session Cancelled"
        mentor_message = f"""
Hi {booking.mentor.title},

The following mentor session has been cancelled:

Student: {booking.student.profile.name if hasattr(booking.student, 'profile') else booking.student.email}
Originally scheduled for: {meeting_time}

This slot is now available for other bookings.

Best regards,
PathAI Team
        """.strip()

        send_mail(
            subject=mentor_subject,
            message=mentor_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[booking.mentor.user.email],
            fail_silently=True,
        )

        print(f"✓ Cancellation emails sent for booking {booking.id}")

    except Exception as e:
        print(f"✗ Error sending cancellation email: {e}")


def generate_ics_file(booking):
    """
    Generate ICS calendar file for a booking

    Args:
        booking: MentorBooking instance

    Returns:
        String containing ICS file content
    """
    try:
        start_time = booking.start_at_utc.strftime("%Y%m%dT%H%M%SZ")
        end_time = booking.end_at_utc.strftime("%Y%m%dT%H%M%SZ")

        ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//PathAI//Mentor Session//EN
BEGIN:VEVENT
UID:booking-{booking.id}@pathai.com
DTSTART:{start_time}
DTEND:{end_time}
SUMMARY:Mentor Session with {booking.mentor.title}
{f"DESCRIPTION:Topic: {booking.topic}\\n\\nJoin meeting: {booking.meeting_url}" if booking.topic else f"DESCRIPTION:Join meeting: {booking.meeting_url}"}
{f"LOCATION:{booking.meeting_url}" if booking.meeting_url else ""}
END:VEVENT
END:VCALENDAR
        """.strip()

        return ics_content

    except Exception as e:
        print(f"✗ Error generating ICS file: {e}")
        return None
