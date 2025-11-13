"""
Vision API - Generate vision and daily headlines from GoalSpecs

Uses the primary GoalSpec to generate personalized vision statements
and daily motivational headlines.
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from datetime import datetime, timedelta

from .models import GoalSpec
from ai.openai_client import openai_client


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_vision(request):
    """
    Get user's vision statement generated from primary GoalSpec

    Returns:
    {
        "vision": "Complete MSc at University of Edinburgh...",
        "primary_goalspec": {
            "id": 1,
            "category": "study",
            "title": "...",
            ...
        }
    }
    """
    try:
        # Get primary GoalSpec (highest priority_weight)
        primary_goalspec = GoalSpec.objects.filter(
            user=request.user,
            status='active'
        ).order_by('-priority_weight', '-created_at').first()

        if not primary_goalspec:
            return Response({
                'vision': 'Set your goals to see your vision',
                'primary_goalspec': None,
            })

        # Generate vision from primary goalspec
        vision_text = _generate_vision_from_goalspec(primary_goalspec)

        return Response({
            'vision': vision_text,
            'primary_goalspec': {
                'id': primary_goalspec.id,
                'category': primary_goalspec.category,
                'title': primary_goalspec.title,
                'description': primary_goalspec.description,
            }
        })

    except Exception as e:
        print(f"Vision generation error: {e}")
        return Response(
            {'error': f'Failed to generate vision: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_daily_headline(request):
    """
    Get daily motivational headline based on user's progress and goals

    Returns:
    {
        "headline": "3 applications away from your dream MSc",
        "goalspec_id": 1,
        "generated_at": "2025-10-15T10:00:00Z"
    }
    """
    try:
        # Get primary GoalSpec
        primary_goalspec = GoalSpec.objects.filter(
            user=request.user,
            status='active'
        ).order_by('-priority_weight', '-created_at').first()

        if not primary_goalspec:
            return Response({
                'headline': 'Ready to achieve your goals?',
                'goalspec_id': None,
            })

        # Get today's todos for this goalspec
        from todos.models import AtomicTask
        today = timezone.now().date()

        tasks_today = AtomicTask.objects.filter(
            user=request.user,
            goalspec=primary_goalspec,
            scheduled_date=today
        )

        completed_today = tasks_today.filter(status='done').count()
        pending_today = tasks_today.filter(status='pending').count()

        # Generate headline
        headline = _generate_daily_headline(
            primary_goalspec,
            completed_today,
            pending_today
        )

        return Response({
            'headline': headline,
            'goalspec_id': primary_goalspec.id,
            'generated_at': timezone.now().isoformat(),
        })

    except Exception as e:
        print(f"Headline generation error: {e}")
        return Response({
            'headline': 'Keep pushing forward!',
            'error': str(e),
        })


def _generate_vision_from_goalspec(goalspec: GoalSpec) -> str:
    """Generate a compelling vision statement from a GoalSpec"""

    category_map = {
        'study': 'academic excellence',
        'career': 'professional success',
        'sport': 'fitness achievement',
        'finance': 'financial freedom',
        'language': 'language mastery',
        'health': 'optimal health',
        'creative': 'creative expression',
        'admin': 'organized life',
        'research': 'research breakthrough',
        'networking': 'meaningful connections',
        'travel': 'world exploration',
        'other': 'personal growth',
    }

    category_vision = category_map.get(goalspec.category, 'your goal')

    # Create vision statement
    if goalspec.target_date:
        days_remaining = (goalspec.target_date - timezone.now().date()).days
        if days_remaining > 0:
            vision = f"{goalspec.title} - {days_remaining} days to {category_vision}"
        else:
            vision = f"{goalspec.title} - Achieving {category_vision} now"
    else:
        vision = f"{goalspec.title} - Your path to {category_vision}"

    return vision


def _generate_daily_headline(goalspec: GoalSpec, completed: int, pending: int) -> str:
    """Generate motivational daily headline"""

    headlines_by_category = {
        'study': [
            f"{pending} tasks closer to your dream university",
            f"Building your academic future today",
            f"{completed} wins for your MSc journey",
        ],
        'career': [
            f"{pending} steps toward your dream job",
            f"Your career breakthrough starts today",
            f"{completed} actions toward professional success",
        ],
        'sport': [
            f"{pending} workouts until peak performance",
            f"Today's training = tomorrow's victory",
            f"{completed} sessions toward your fitness goal",
        ],
        'finance': [
            f"{pending} moves toward financial freedom",
            f"Building wealth one action at a time",
            f"{completed} steps closer to your financial goal",
        ],
        'language': [
            f"{pending} lessons until fluency",
            f"Every word learned is progress made",
            f"{completed} practice sessions completed",
        ],
        'health': [
            f"{pending} healthy choices today",
            f"Your best health starts now",
            f"{completed} wellness actions completed",
        ],
        'creative': [
            f"{pending} creative tasks await",
            f"Your masterpiece takes shape today",
            f"{completed} creative wins today",
        ],
        'networking': [
            f"{pending} connections to make",
            f"Your network is your net worth",
            f"{completed} meaningful connections today",
        ],
    }

    category_headlines = headlines_by_category.get(
        goalspec.category,
        [f"{pending} tasks toward your goal", f"Making progress today", f"{completed} wins today"]
    )

    # Choose headline based on progress
    if pending > 0:
        return category_headlines[0]
    elif completed > 0:
        return category_headlines[2]
    else:
        return category_headlines[1]


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_vision_analytics(request):
    """
    Get analytics for user's vision and goals

    Returns progress metrics, milestones, etc.
    """
    try:
        goalspecs = GoalSpec.objects.filter(
            user=request.user,
            status='active'
        ).order_by('-priority_weight')

        analytics = []
        for goalspec in goalspecs:
            from todos.models import AtomicTask

            total_tasks = AtomicTask.objects.filter(
                user=request.user,
                goalspec=goalspec
            ).count()

            completed_tasks = AtomicTask.objects.filter(
                user=request.user,
                goalspec=goalspec,
                status='done'
            ).count()

            progress_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

            analytics.append({
                'goalspec': {
                    'id': goalspec.id,
                    'category': goalspec.category,
                    'title': goalspec.title,
                    'priority_weight': goalspec.priority_weight,
                },
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks,
                'progress_percentage': round(progress_percentage, 1),
            })

        return Response({
            'goalspecs': analytics,
            'total_goalspecs': len(analytics),
        })

    except Exception as e:
        print(f"Vision analytics error: {e}")
        return Response(
            {'error': f'Failed to get analytics: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
