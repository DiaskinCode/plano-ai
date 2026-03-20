"""
Notification Signals

Automatically create notifications for community and social interactions.
"""

from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from .notification_manager import (
    notify_new_follower,
    notify_community_post,
    notify_comment_reply,
    notify_new_message,
    notify_post_upvote,
    notify_mention,
)


@receiver(post_save, sender='social.Follow')
def notify_on_follow(sender, instance, created, **kwargs):
    """Notify user when someone follows them."""
    if created:
        notify_new_follower(
            follower_id=instance.follower.id,
            following_id=instance.following.id
        )


@receiver(post_save, sender='community.Post')
def notify_on_new_post(sender, instance, created, **kwargs):
    """Notify community members when a new post is created."""
    if created:
        notify_community_post(
            community_id=instance.community.id,
            post_id=instance.id,
            author_id=instance.user.id,
            community_name=instance.community.name
        )


@receiver(post_save, sender='community.Comment')
def notify_on_comment_reply(sender, instance, created, **kwargs):
    """Notify user when someone replies to their comment."""
    if created and instance.parent_comment:
        # This is a reply to a comment
        notify_comment_reply(
            comment_id=instance.parent_comment.id,
            post_id=instance.post.id,
            author_id=instance.parent_comment.user.id,
            replier_id=instance.user.id
        )


@receiver(post_save, sender='social.DirectMessage')
def notify_on_new_message(sender, instance, created, **kwargs):
    """Notify user when they receive a new direct message."""
    if created:
        notify_new_message(
            sender_id=instance.sender.id,
            recipient_id=instance.recipient.id,
            message_id=instance.id
        )


# Note: Post upvote notification is handled in the community views
# when upvotes reach milestones (10, 25, 50, 100, etc.)

# Note: Mention detection and notification needs to be implemented
# in post/comment creation logic (regex parsing for @username)
