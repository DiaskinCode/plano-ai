"""
In-App Notification Manager

Centralized service for creating and managing in-app notifications.
Handles notification preferences, quiet hours, and batching.
"""

from django.utils import timezone
from django.db.models import Q
from typing import Optional, Dict, Any, List
from .models import Notification, NotificationPreference


class InAppNotificationService:
    """Service for creating and managing in-app notifications"""

    @staticmethod
    def create_notification(
        recipient_id: int,
        notification_type: str,
        title: str,
        message: str,
        actor_id: Optional[int] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Optional[Notification]:
        """
        Create a notification for a user, respecting their preferences.

        Args:
            recipient_id: User ID to receive notification
            notification_type: Type of notification (e.g., 'community_new_post')
            title: Notification title
            message: Notification message
            actor_id: User ID who triggered the notification (optional)
            data: Additional data (e.g., {'post_id': 123})

        Returns:
            Notification object if created, None if suppressed
        """
        from django.contrib.auth import get_user_model

        User = get_user_model()

        try:
            recipient = User.objects.get(id=recipient_id)
        except User.DoesNotExist:
            return None

        # Get or create notification preferences
        prefs, _ = NotificationPreference.objects.get_or_create(user=recipient)

        # Check if notification type is enabled
        if not prefs.is_notification_enabled(notification_type):
            return None

        # Get actor if provided
        actor = None
        if actor_id:
            try:
                actor = User.objects.get(id=actor_id)
            except User.DoesNotExist:
                pass

        # Create notification
        notification = Notification.objects.create(
            recipient=recipient,
            notification_type=notification_type,
            title=title,
            message=message,
            actor=actor,
            data=data or {},
        )

        return notification

    @staticmethod
    def mark_as_read(notification_id: int, user_id: int) -> bool:
        """Mark a notification as read."""
        try:
            notification = Notification.objects.get(
                id=notification_id,
                recipient_id=user_id
            )
            if not notification.is_read:
                notification.is_read = True
                notification.read_at = timezone.now()
                notification.save(update_fields=['is_read', 'read_at'])
            return True
        except Notification.DoesNotExist:
            return False

    @staticmethod
    def mark_all_as_read(user_id: int) -> int:
        """Mark all notifications as read for a user. Returns count updated."""
        count = Notification.objects.filter(
            recipient_id=user_id,
            is_read=False
        ).update(
            is_read=True,
            read_at=timezone.now()
        )
        return count

    @staticmethod
    def get_unread_count(user_id: int) -> int:
        """Get count of unread notifications for a user."""
        return Notification.objects.filter(
            recipient_id=user_id,
            is_read=False
        ).count()

    @staticmethod
    def get_notifications(
        user_id: int,
        unread_only: bool = False,
        limit: int = 50
    ) -> List[Notification]:
        """Get notifications for a user."""
        queryset = Notification.objects.filter(recipient_id=user_id)

        if unread_only:
            queryset = queryset.filter(is_read=False)

        return list(queryset[:limit])


# Convenience functions for common notification types

def notify_new_follower(follower_id: int, following_id: int):
    """Notify user when someone follows them."""
    from django.contrib.auth import get_user_model

    User = get_user_model()

    try:
        follower = User.objects.get(id=follower_id)

        return InAppNotificationService.create_notification(
            recipient_id=following_id,
            notification_type='social_new_follower',
            title=f'{follower.username} started following you',
            message=f'{follower.username} is now following you.',
            actor_id=follower_id,
            data={'follower_id': follower_id},
        )
    except User.DoesNotExist:
        return None


def notify_community_post(community_id: int, post_id: int, author_id: int, community_name: str):
    """Notify community members when a new post is created."""
    from community.models import CommunityMember

    # Get all members except the author
    members = CommunityMember.objects.filter(
        community_id=community_id
    ).exclude(user_id=author_id)

    notifications = []
    for member in members:
        notif = InAppNotificationService.create_notification(
            recipient_id=member.user_id,
            notification_type='community_new_post',
            title=f'New post in {community_name}',
            message=f'A new post was shared in {community_name}',
            actor_id=author_id,
            data={'post_id': post_id, 'community_id': community_id},
        )
        if notif:
            notifications.append(notif)

    return notifications


def notify_comment_reply(comment_id: int, post_id: int, author_id: int, replier_id: int):
    """Notify user when someone replies to their comment."""
    from django.contrib.auth import get_user_model

    User = get_user_model()

    try:
        replier = User.objects.get(id=replier_id)

        return InAppNotificationService.create_notification(
            recipient_id=author_id,
            notification_type='community_reply',
            title=f'{replier.username} replied to your comment',
            message='Someone replied to your comment.',
            actor_id=replier_id,
            data={'comment_id': comment_id, 'post_id': post_id},
        )
    except User.DoesNotExist:
        return None


def notify_new_message(sender_id: int, recipient_id: int, message_id: int):
    """Notify user when they receive a new direct message."""
    from django.contrib.auth import get_user_model

    User = get_user_model()

    try:
        sender = User.objects.get(id=sender_id)

        return InAppNotificationService.create_notification(
            recipient_id=recipient_id,
            notification_type='message_new',
            title=f'New message from {sender.username}',
            message='You have a new direct message.',
            actor_id=sender_id,
            data={'message_id': message_id, 'sender_id': sender_id},
        )
    except User.DoesNotExist:
        return None


def notify_post_upvote(post_id: int, user_id: int, voter_id: int):
    """Notify user when their post receives an upvote milestone."""
    from community.models import Post
    from django.contrib.auth import get_user_model

    User = get_user_model()

    try:
        post = Post.objects.get(id=post_id)
        voter = User.objects.get(id=voter_id)

        # Only notify at milestones (10, 25, 50, 100, etc.)
        upvotes = post.upvotes
        if upvotes in [10, 25, 50, 100, 200, 500, 1000]:
            return InAppNotificationService.create_notification(
                recipient_id=user_id,
                notification_type='community_upvote',
                title=f'🎉 Your post has {upvotes} upvotes!',
                message=f'Congratulations! Your post reached {upvotes} upvotes.',
                actor_id=voter_id,
                data={'post_id': post_id, 'upvotes': upvotes},
            )
    except (Post.DoesNotExist, User.DoesNotExist):
        return None

    return None


def notify_mention(user_id: int, mentioner_id: int, post_id: int, comment_id: Optional[int] = None):
    """Notify user when they are mentioned in a post or comment."""
    from django.contrib.auth import get_user_model

    User = get_user_model()

    try:
        mentioner = User.objects.get(id=mentioner_id)

        title = f'{mentioner.username} mentioned you'
        message = f'{mentioner.username} mentioned you in a ' + ('comment' if comment_id else 'post')

        data = {'post_id': post_id}
        if comment_id:
            data['comment_id'] = comment_id

        return InAppNotificationService.create_notification(
            recipient_id=user_id,
            notification_type='community_mention',
            title=title,
            message=message,
            actor_id=mentioner_id,
            data=data,
        )
    except User.DoesNotExist:
        return None
