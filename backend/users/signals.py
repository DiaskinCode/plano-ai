"""
User signals for automatic setup
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import User, NotificationPreferences


@receiver(post_save, sender=User)
def create_notification_preferences(sender, instance, created, **kwargs):
    """
    Automatically create NotificationPreferences when a new User is created
    """
    if created:
        NotificationPreferences.objects.create(
            user=instance,
            task_reminders_enabled=True,
            task_reminder_minutes_before=15,  # 15 minutes before for useful reminders
            deadline_notifications_enabled=True,
            ai_motivation_enabled=True,
            daily_pulse_reminder_enabled=True
        )
        print(f'✅ Created NotificationPreferences for user: {instance.email}')


# Progress Tracking Signals

@receiver(post_save, sender='todos.Todo')
def update_progress_on_task_completion(sender, instance, created, **kwargs):
    """
    Automatically update user progress when a task is completed.

    This is triggered when:
    - A task's status changes to 'completed'
    - A task is updated with new completion data
    """
    # Only update if task is completed and has a user
    if instance.status == 'completed' and instance.user:
        try:
            from .services import update_user_progress
            update_user_progress(instance.user.id)
        except Exception as e:
            # Log error but don't fail the task save
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Failed to update progress for user {instance.user.id}: {str(e)}')


@receiver(post_save, sender='social.Follow')
def update_follow_count_on_follow(sender, instance, created, **kwargs):
    """
    Update follower/following counts when users follow each other.
    This is handled in the social views via F() expressions, but we also
    update here for consistency.
    """
    if created:
        from django.db.models import F

        # Update following count for follower
        instance.follower.profile.following_count = F('following_count') + 1
        instance.follower.profile.save(update_fields=['following_count'])

        # Update follower count for following
        instance.following.profile.follower_count = F('follower_count') + 1
        instance.following.profile.save(update_fields=['follower_count'])


@receiver(post_delete, sender='social.Follow')
def update_follow_count_on_unfollow(sender, instance, **kwargs):
    """
    Update follower/following counts when users unfollow each other.
    """
    from django.db.models import F

    # Update following count for follower (ensure it doesn't go negative)
    if instance.follower.profile.following_count > 0:
        instance.follower.profile.following_count = F('following_count') - 1
        instance.follower.profile.save(update_fields=['following_count'])

    # Update follower count for following (ensure it doesn't go negative)
    if instance.following.profile.follower_count > 0:
        instance.following.profile.follower_count = F('follower_count') - 1
        instance.following.profile.save(update_fields=['follower_count'])


@receiver(post_save, sender='community.Post')
def update_post_count_on_post_create(sender, instance, created, **kwargs):
    """
    Update post count when a user creates a post.
    """
    if created:
        from django.db.models import F

        instance.user.profile.post_count = F('post_count') + 1
        instance.user.profile.save(update_fields=['post_count'])


@receiver(post_delete, sender='community.Post')
def update_post_count_on_post_delete(sender, instance, **kwargs):
    """
    Update post count when a user deletes a post.
    """
    from django.db.models import F

    if instance.user.profile.post_count > 0:
        instance.user.profile.post_count = F('post_count') - 1
        instance.user.profile.save(update_fields=['post_count'])

