"""
Celery tasks for analytics app
- Weekly reflection generation (Sunday evenings)
- Daily behavior pattern updates
"""
from celery import shared_task
from datetime import datetime, timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model

from .services import BehaviorAnalyzer, ReflectionGenerator
from .models import WeeklyReflection

User = get_user_model()


@shared_task(name='analytics.generate_weekly_reflections')
def generate_weekly_reflections():
    """
    Generate weekly reflections for all active users
    Runs every Sunday at 7 PM

    Returns:
        dict: Summary of reflections generated
    """
    today = timezone.now().date()

    # Calculate week boundaries (Monday - Sunday)
    week_start = today - timedelta(days=today.weekday())  # This Monday
    week_end = week_start + timedelta(days=6)  # This Sunday

    # Get all active users
    active_users = User.objects.filter(is_active=True)

    results = {
        'total_users': active_users.count(),
        'reflections_created': 0,
        'reflections_skipped': 0,
        'errors': []
    }

    for user in active_users:
        try:
            generator = ReflectionGenerator(user)
            reflection = generator.generate_weekly_reflection(
                week_start=week_start,
                week_end=week_end,
                method='scheduled'
            )

            if reflection:
                results['reflections_created'] += 1

                # TODO: Send push notification
                # send_push_notification(user, reflection)

            else:
                results['reflections_skipped'] += 1

        except Exception as e:
            results['errors'].append({
                'user_id': user.id,
                'error': str(e)
            })

    return results


@shared_task(name='analytics.update_behavior_patterns')
def update_behavior_patterns():
    """
    Update behavior patterns for all users
    Runs daily at midnight

    Returns:
        dict: Summary of patterns updated
    """
    today = timezone.now().date()

    # Analyze last 7 days
    week_start = today - timedelta(days=7)
    week_end = today

    active_users = User.objects.filter(is_active=True)

    results = {
        'total_users': active_users.count(),
        'patterns_created': 0,
        'errors': []
    }

    for user in active_users:
        try:
            analyzer = BehaviorAnalyzer(user)
            patterns = analyzer.analyze_all_patterns(week_start, week_end)

            results['patterns_created'] += len(patterns)

        except Exception as e:
            results['errors'].append({
                'user_id': user.id,
                'error': str(e)
            })

    return results


@shared_task(name='analytics.generate_reflection_for_user')
def generate_reflection_for_user(user_id: int, week_start_str: str = None):
    """
    Generate reflection for a specific user (on-demand)

    Args:
        user_id: User ID
        week_start_str: Week start date in YYYY-MM-DD format (optional)

    Returns:
        dict: Reflection data or error
    """
    try:
        user = User.objects.get(id=user_id)

        if week_start_str:
            week_start = datetime.strptime(week_start_str, '%Y-%m-%d').date()
        else:
            today = timezone.now().date()
            week_start = today - timedelta(days=today.weekday())

        week_end = week_start + timedelta(days=6)

        generator = ReflectionGenerator(user)
        reflection = generator.generate_weekly_reflection(
            week_start=week_start,
            week_end=week_end,
            method='on_demand'
        )

        if reflection:
            return {
                'success': True,
                'reflection_id': reflection.id,
                'week': reflection.get_week_label(),
                'insights_count': len(reflection.insights)
            }
        else:
            return {
                'success': False,
                'error': 'Not enough data to generate reflection'
            }

    except User.DoesNotExist:
        return {
            'success': False,
            'error': f'User {user_id} not found'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


@shared_task(name='analytics.cleanup_old_patterns')
def cleanup_old_patterns():
    """
    Mark old behavior patterns as inactive
    Runs weekly

    Patterns older than 30 days are marked inactive
    """
    from .models import UserBehaviorPattern

    cutoff_date = timezone.now().date() - timedelta(days=30)

    updated = UserBehaviorPattern.objects.filter(
        time_window_end__lt=cutoff_date,
        is_active=True
    ).update(is_active=False)

    return {
        'patterns_deactivated': updated
    }


# ==============================================
# Daily Pulse / Morning Brief Tasks
# ==============================================

@shared_task(name='analytics.generate_daily_pulse_morning')
def generate_daily_pulse_morning():
    """
    Generate Daily Pulse for all active users
    Runs every morning at 7:00 AM

    Returns:
        dict: Summary of briefs generated
    """
    from .daily_pulse_service import DailyPulseGenerator
    from .models import DailyBrief

    today = timezone.now().date()

    # Get all active users
    active_users = User.objects.filter(is_active=True)

    results = {
        'total_users': active_users.count(),
        'briefs_created': 0,
        'briefs_skipped': 0,
        'errors': []
    }

    for user in active_users:
        try:
            # Check if brief already exists
            existing = DailyBrief.objects.filter(
                user=user,
                date=today
            ).first()

            if existing:
                results['briefs_skipped'] += 1
                continue

            # Generate brief
            generator = DailyPulseGenerator(user)
            brief = generator.generate_daily_brief(trigger='scheduled')

            if brief:
                results['briefs_created'] += 1

                # TODO: Send push notification
                # send_push_notification(user, brief)

            else:
                results['briefs_skipped'] += 1

        except Exception as e:
            results['errors'].append({
                'user_id': user.id,
                'error': str(e)
            })

    return results


@shared_task(name='analytics.regenerate_daily_pulse_on_login')
def regenerate_daily_pulse_on_login(user_id: int):
    """
    Regenerate Daily Pulse when user logs in
    Only regenerates if existing brief is older than 1 hour

    Args:
        user_id: User ID

    Returns:
        dict: Brief data or error
    """
    from .daily_pulse_service import DailyPulseGenerator
    from .models import DailyBrief

    try:
        user = User.objects.get(id=user_id)
        today = timezone.now().date()

        # Check existing brief
        existing = DailyBrief.objects.filter(
            user=user,
            date=today
        ).first()

        if existing and not existing.should_regenerate():
            # Brief is fresh, no need to regenerate
            return {
                'success': True,
                'regenerated': False,
                'brief_id': existing.id,
                'message': 'Brief is fresh, no regeneration needed'
            }

        # Generate or regenerate
        generator = DailyPulseGenerator(user)
        brief = generator.generate_daily_brief(trigger='on_login')

        if brief:
            # Mark as shown in app
            brief.mark_shown('app')

            return {
                'success': True,
                'regenerated': True,
                'brief_id': brief.id,
                'workload_percentage': brief.workload_percentage,
                'top_priorities_count': len(brief.top_priorities)
            }
        else:
            return {
                'success': False,
                'error': 'Failed to generate brief'
            }

    except User.DoesNotExist:
        return {
            'success': False,
            'error': f'User {user_id} not found'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


@shared_task(name='analytics.send_daily_pulse_to_chat')
def send_daily_pulse_to_chat(user_id: int):
    """
    Send Daily Pulse as a chat message
    Called after brief generation

    Args:
        user_id: User ID

    Returns:
        dict: Success status
    """
    from .models import DailyBrief
    from chat.models import ChatMessage, ChatConversation

    try:
        user = User.objects.get(id=user_id)
        today = timezone.now().date()

        # Get today's brief
        brief = DailyBrief.objects.filter(
            user=user,
            date=today
        ).first()

        if not brief:
            return {
                'success': False,
                'error': 'No brief found for today'
            }

        if brief.shown_in_chat:
            return {
                'success': True,
                'message': 'Brief already sent to chat'
            }

        # Get or create main conversation
        conversation, _ = ChatConversation.objects.get_or_create(
            user=user,
            task__isnull=True,
            defaults={'title': 'Daily Brief'}
        )

        # Create chat message
        ChatMessage.objects.create(
            user=user,
            conversation=conversation,
            role='assistant',
            content=brief.full_message
        )

        # Mark as shown
        brief.mark_shown('chat')

        return {
            'success': True,
            'conversation_id': conversation.id,
            'message': 'Brief sent to chat successfully'
        }

    except User.DoesNotExist:
        return {
            'success': False,
            'error': f'User {user_id} not found'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
