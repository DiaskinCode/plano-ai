"""
Social Models - College Application Platform

LinkedIn-style social features with:
- User profiles with followers/following
- Direct messaging between users
- Privacy controls
"""

from django.db import models
from django.conf import settings

USER_MODEL = settings.AUTH_USER_MODEL


class Follow(models.Model):
    """
    Tracks follower/following relationships between users
    """
    follower = models.ForeignKey(
        USER_MODEL,
        on_delete=models.CASCADE,
        related_name='following',
        help_text="User who is following"
    )
    following = models.ForeignKey(
        USER_MODEL,
        on_delete=models.CASCADE,
        related_name='followers',
        help_text="User being followed"
    )

    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True, help_text="When follow relationship was created")

    class Meta:
        unique_together = ['follower', 'following']
        indexes = [
            models.Index(fields=['follower', '-created_at']),
            models.Index(fields=['following', '-created_at']),
        ]
        verbose_name = "Follow"
        verbose_name_plural = "Follows"

    def __str__(self):
        return f"{self.follower.email} → {self.following.email}"


class DirectMessage(models.Model):
    """
    Direct messages between users
    Supports text, images, and file attachments

    Note: Using polling approach (not WebSockets)
    Frontend polls every 15-30 seconds for new messages
    Can upgrade to Django Channels + WebSockets later if needed
    """
    sender = models.ForeignKey(
        USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages',
        help_text="User who sent the message"
    )
    recipient = models.ForeignKey(
        USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_messages',
        help_text="User who received the message"
    )

    # Message content
    content = models.TextField(
        help_text="Message text content"
    )

    # Attachments (images, files, etc.)
    attachments = models.JSONField(
        default=list,
        blank=True,
        help_text='List of attachments: [{"type": "image", "url": "..."}, {"type": "file", "url": "...", "name": "..."}]'
    )

    # Message status
    is_read = models.BooleanField(
        default=False,
        help_text="Whether message has been read by recipient"
    )
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When message was read"
    )

    # Reply threading (optional - for organizing conversations)
    reply_to = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies',
        help_text="If this is a reply to another message"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, help_text="When message was sent")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['sender', 'recipient', '-created_at']),
            models.Index(fields=['recipient', 'is_read', '-created_at']),
            models.Index(fields=['-created_at']),
        ]
        verbose_name = "Direct Message"
        verbose_name_plural = "Direct Messages"

    def __str__(self):
        preview = self.content[:50] + ('...' if len(self.content) > 50 else '')
        return f"{self.sender.email} → {self.recipient.email}: {preview}"


class BlockedUser(models.Model):
    """
    Tracks blocked users
    Blocked users cannot:
    - Send messages
    - Follow
    - See profile/posts (if private)
    """
    blocker = models.ForeignKey(
        USER_MODEL,
        on_delete=models.CASCADE,
        related_name='blocking',
        help_text="User who blocked"
    )
    blocked = models.ForeignKey(
        USER_MODEL,
        on_delete=models.CASCADE,
        related_name='blocked_by',
        help_text="User who was blocked"
    )

    # Optional reason for blocking
    reason = models.CharField(
        max_length=255,
        blank=True,
        help_text="Reason for blocking (optional)"
    )

    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True, help_text="When user was blocked")

    class Meta:
        unique_together = ['blocker', 'blocked']
        indexes = [
            models.Index(fields=['blocker', '-created_at']),
        ]
        verbose_name = "Blocked User"
        verbose_name_plural = "Blocked Users"

    def __str__(self):
        return f"{self.blocker.email} blocked {self.blocked.email}"
