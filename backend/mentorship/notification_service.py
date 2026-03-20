from django.utils import timezone
from notifications.models import Notification


class NotificationService:
    """Service for creating mentorship notifications"""

    @staticmethod
    def create_notification(
        recipient, notification_type, title, message, actor=None, data=None
    ):
        """Create a notification for a user"""
        return Notification.objects.create(
            recipient=recipient,
            notification_type=notification_type,
            title=title,
            message=message,
            actor=actor,
            data=data or {},
        )

    @staticmethod
    def notify_booking_requested(booking):
        """Notify mentor of new booking request"""
        return NotificationService.create_notification(
            recipient=booking.mentor.user,
            notification_type="booking_requested",
            title="New Booking Request",
            message=f"{booking.student.profile.name if hasattr(booking.student, 'profile') else booking.student.email} wants to book a session with you.",
            actor=booking.student,
            data={
                "type": "booking",
                "booking_id": booking.id,
                "start_at": booking.start_at_utc.isoformat(),
            },
        )

    @staticmethod
    def notify_booking_confirmed(booking):
        """Notify student that booking is confirmed"""
        return NotificationService.create_notification(
            recipient=booking.student,
            notification_type="booking_confirmed",
            title="Booking Confirmed",
            message=f"Your session with {booking.mentor.title} has been confirmed.",
            actor=booking.mentor.user,
            data={
                "type": "booking",
                "booking_id": booking.id,
                "start_at": booking.start_at_utc.isoformat(),
                "meeting_url": booking.meeting_url,
            },
        )

    @staticmethod
    def notify_booking_cancelled(booking, cancelled_by_user):
        """Notify the other party that booking was cancelled"""
        if cancelled_by_user == booking.mentor.user:
            # Notify student
            recipient = booking.student
            message = f"{booking.mentor.title} has cancelled your session."
        else:
            # Notify mentor
            recipient = booking.mentor.user
            student_name = (
                booking.student.profile.name
                if hasattr(booking.student, "profile")
                else booking.student.email
            )
            message = f"{student_name} has cancelled their session with you."

        return NotificationService.create_notification(
            recipient=recipient,
            notification_type="booking_confirmed",  # Reusing type for cancellation
            title="Booking Cancelled",
            message=message,
            actor=cancelled_by_user,
            data={"type": "booking", "booking_id": booking.id},
        )

    @staticmethod
    def notify_session_reminder(booking, hours_before):
        """Send reminder before session"""
        recipient_mentor = booking.mentor.user
        recipient_student = booking.student
        student_name = (
            booking.student.profile.name
            if hasattr(booking.student, "profile")
            else booking.student.email
        )

        # Notify mentor
        NotificationService.create_notification(
            recipient=recipient_mentor,
            notification_type="session_reminder",
            title=f"Upcoming Session in {hours_before}h",
            message=f"Session with {student_name} starts at {booking.start_at_utc.strftime('%H:%M')}.",
            data={
                "type": "booking",
                "booking_id": booking.id,
                "meeting_url": booking.meeting_url,
            },
        )

        # Notify student
        NotificationService.create_notification(
            recipient=recipient_student,
            notification_type="session_reminder",
            title=f"Upcoming Session in {hours_before}h",
            message=f"Your session with {booking.mentor.title} starts at {booking.start_at_utc.strftime('%H:%M')}.",
            data={
                "type": "booking",
                "booking_id": booking.id,
                "meeting_url": booking.meeting_url,
            },
        )

    @staticmethod
    def notify_review_ready(review_request):
        """Notify student that mentor has responded"""
        return NotificationService.create_notification(
            recipient=review_request.student,
            notification_type="review_ready",
            title="Mentor Feedback Ready",
            message=f"{review_request.mentor.title} has provided feedback on your {review_request.request_type}.",
            actor=review_request.mentor.user,
            data={
                "type": "review",
                "request_id": review_request.id,
                "request_type": review_request.request_type,
            },
        )
