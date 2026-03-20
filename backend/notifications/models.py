from django.conf import settings
from django.db import models

USER_MODEL = settings.AUTH_USER_MODEL


class Notification(models.Model):
    """
    User Notification Model

    Stores all notifications for users including:
    - Task reminders
    - Community interactions
    - Social interactions
    - Messages
    """

    # Notification types
    NOTIFICATION_TYPES = [
        # Task notifications
        ("task_reminder", "Task Reminder"),
        ("task_due_soon", "Task Due Soon"),
        ("task_overdue", "Task Overdue"),
        ("task_completed", "Task Completed"),
        # Community notifications
        ("community_new_post", "New Post in Community"),
        ("community_reply", "Reply to Comment"),
        ("community_mention", "Mention in Post/Comment"),
        ("community_upvote", "Upvote Milestone"),
        # Social notifications
        ("social_new_follower", "New Follower"),
        ("social_like", "Like on Post"),
        # Message notifications
        ("message_new", "New Direct Message"),
        ("message_unread", "Unread Messages"),
        # System notifications
        ("system_update", "System Update"),
        ("achievement", "Achievement Unlocked"),
        # Mentorship notifications
        ("booking_requested", "New Booking Request"),
        ("booking_confirmed", "Booking Confirmed"),
        ("session_reminder", "Upcoming Session Reminder"),
        ("review_ready", "Review Response Ready"),
    ]

    # Recipient
    recipient = models.ForeignKey(
        USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )

    # Notification type
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)

    # Content
    title = models.CharField(max_length=255)
    message = models.TextField()

    # Optional: Link to related object
    # Format: {"type": "post", "id": 123} or {"type": "task", "id": 456}
    data = models.JSONField(default=dict, blank=True)

    # Read status
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    # Optional: Actor (user who triggered the notification)
    actor = models.ForeignKey(
        USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="triggered_notifications",
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["recipient", "-created_at"]),
            models.Index(fields=["recipient", "is_read"]),
            models.Index(fields=["notification_type"]),
        ]

    def __str__(self):
        return f"{self.recipient.email}: {self.title}"


class NotificationPreference(models.Model):
    """
    Enhanced notification preferences for each notification type.
    """

    user = models.OneToOneField(
        USER_MODEL, on_delete=models.CASCADE, related_name="notification_settings"
    )

    # Task notifications
    task_reminders_enabled = models.BooleanField(default=True)
    task_due_soon_enabled = models.BooleanField(default=True)
    task_overdue_enabled = models.BooleanField(default=True)
    task_completed_enabled = models.BooleanField(default=False)

    # Community notifications
    community_new_post_enabled = models.BooleanField(default=True)
    community_reply_enabled = models.BooleanField(default=True)
    community_mention_enabled = models.BooleanField(default=True)
    community_upvote_enabled = models.BooleanField(default=True)

    # Social notifications
    social_new_follower_enabled = models.BooleanField(default=True)
    social_like_enabled = models.BooleanField(default=True)

    # Message notifications
    message_new_enabled = models.BooleanField(default=True)
    message_unread_enabled = models.BooleanField(default=True)

    # System notifications
    system_update_enabled = models.BooleanField(default=True)
    achievement_enabled = models.BooleanField(default=True)

    # Mentorship notifications
    booking_requested_enabled = models.BooleanField(default=True)
    booking_confirmed_enabled = models.BooleanField(default=True)
    session_reminder_enabled = models.BooleanField(default=True)
    review_ready_enabled = models.BooleanField(default=True)

    # Quiet hours
    quiet_hours_enabled = models.BooleanField(default=False)
    quiet_hours_start = models.TimeField(
        null=True, blank=True, help_text="Start time e.g., 22:00"
    )
    quiet_hours_end = models.TimeField(
        null=True, blank=True, help_text="End time e.g., 08:00"
    )

    # Push notification preferences
    push_enabled = models.BooleanField(default=True)
    push_sound_enabled = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Notification Preference"
        verbose_name_plural = "Notification Preferences"

    def __str__(self):
        return f"Notification settings for {self.user.email}"

    def is_notification_enabled(self, notification_type: str) -> bool:
        """Check if a specific notification type is enabled."""
        field_name = f"{notification_type}_enabled"
        return getattr(self, field_name, False)
