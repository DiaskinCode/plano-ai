"""
Community Signals - Mentions and Notifications
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from search.utils import MentionDetector


@receiver(post_save, sender='community.Post')
def detect_mentions_in_post(sender, instance, created, **kwargs):
    """
    Detect @mentions in post content and create notifications.
    """
    if created or (instance.content and hasattr(instance, '_content_changed')):
        # Extract mentions from post content
        mentions = MentionDetector.extract_mentions(instance.content)

        # Also check title for mentions
        title_mentions = MentionDetector.extract_mentions(instance.title)
        mentions = list(set(mentions + title_mentions))

        if mentions:
            # Notify all mentioned users
            from search.utils import MentionDetector
            MentionDetector.notify_mentions(
                text=f"{instance.title} {instance.content}",
                post_id=instance.id,
                actor_id=instance.user.id,
            )


@receiver(post_save, sender='community.Comment')
def detect_mentions_in_comment(sender, instance, created, **kwargs):
    """
    Detect @mentions in comment content and create notifications.
    """
    if created:
        # Notify mentioned users
        from search.utils import MentionDetector
        MentionDetector.notify_mentions(
            text=instance.content,
            post_id=instance.post.id,
            comment_id=instance.id,
            actor_id=instance.user.id,
        )
