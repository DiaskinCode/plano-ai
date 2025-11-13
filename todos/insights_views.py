"""
AI Insights API Views
Endpoints for category progress, skip patterns, and smart task suggestions
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.db import models
from datetime import datetime, timedelta

from .models import Todo
from .advanced_models import AIInsight, TaskCompletion
from ai.task_intelligence import calculate_category_progress, analyze_skip_patterns


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_category_progress(request):
    """
    Get completion progress by goal category

    Response:
    {
        "study": {
            "completed": 15,
            "total": 20,
            "percentage": 75,
            "on_track": true
        },
        "language": { ... },
        "sport": { ... }
    }
    """
    try:
        progress = calculate_category_progress(request.user)
        return Response(progress)
    except Exception as e:
        print(f"Category progress error: {e}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_skip_patterns(request):
    """
    Analyze why user skips tasks

    Query params:
    - days_back: int (default 14)

    Response:
    {
        "total_skipped": 12,
        "reasons": {
            "no_time": 7,
            "no_motivation": 3,
            "distracted": 2
        },
        "top_reason": "no_time",
        "skip_rate": 0.32,
        "period_days": 14
    }
    """
    days_back = int(request.query_params.get('days_back', 14))

    try:
        patterns = analyze_skip_patterns(request.user, days_back)
        return Response(patterns)
    except Exception as e:
        print(f"Skip patterns error: {e}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_ai_insights(request):
    """
    Get all AI-generated insights for user

    Query params:
    - unread_only: bool (default false)
    - category: str (optional filter)

    Response:
    [
        {
            "id": 1,
            "insight_type": "skip_pattern",
            "category": "language",
            "title": "Evening tasks often skipped",
            "message": "You skip 70% of evening tasks. Reschedule to morning?",
            "data": {...},
            "action_suggestions": [...],
            "priority": 3,
            "is_read": false,
            "created_at": "..."
        },
        ...
    ]
    """
    unread_only = request.query_params.get('unread_only', 'false').lower() == 'true'
    category = request.query_params.get('category')

    insights = AIInsight.objects.filter(
        user=request.user,
        is_dismissed=False
    )

    if unread_only:
        insights = insights.filter(is_read=False)

    if category:
        insights = insights.filter(category=category)

    # Remove expired insights
    insights = insights.filter(
        models.Q(expires_at__isnull=True) | models.Q(expires_at__gte=timezone.now())
    )

    data = []
    for insight in insights:
        data.append({
            'id': insight.id,
            'insight_type': insight.insight_type,
            'category': insight.category,
            'title': insight.title,
            'message': insight.message,
            'data': insight.data,
            'action_suggestions': insight.action_suggestions,
            'priority': insight.priority,
            'is_read': insight.is_read,
            'created_at': insight.created_at.isoformat(),
        })

    return Response(data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_insight_read(request, insight_id):
    """Mark an insight as read"""
    try:
        insight = AIInsight.objects.get(id=insight_id, user=request.user)
        insight.is_read = True
        insight.save()
        return Response({'success': True})
    except AIInsight.DoesNotExist:
        return Response(
            {'error': 'Insight not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def dismiss_insight(request, insight_id):
    """Dismiss an insight"""
    try:
        insight = AIInsight.objects.get(id=insight_id, user=request.user)
        insight.is_dismissed = True
        insight.save()
        return Response({'success': True})
    except AIInsight.DoesNotExist:
        return Response(
            {'error': 'Insight not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def complete_task_with_feedback(request, task_id):
    """
    Complete a task with user feedback

    Request:
    {
        "completion_reason": "completed" | "skipped_no_time" | "skipped_no_motivation" | ...,
        "difficulty_rating": 1-5 (optional),
        "actual_duration_minutes": int (optional),
        "notes": "..." (optional),
        "energy_level_at_completion": "high" | "medium" | "low" (optional)
    }

    Response:
    {
        "success": true,
        "task_id": 123,
        "completion_id": 456
    }
    """
    try:
        task = Todo.objects.get(id=task_id, user=request.user)

        # Update task status
        completion_reason = request.data.get('completion_reason', 'completed')
        if completion_reason == 'completed':
            task.status = 'done'
            task.completed_at = timezone.now()
        else:
            task.status = 'skipped'
            task.skipped_at = timezone.now()
            task.skip_reason = completion_reason

        task.save()

        # Create TaskCompletion record
        completion = TaskCompletion.objects.create(
            task=task,
            user=request.user,
            completion_reason=completion_reason,
            difficulty_rating=request.data.get('difficulty_rating'),
            actual_duration_minutes=request.data.get('actual_duration_minutes'),
            notes=request.data.get('notes', ''),
            energy_level_at_completion=request.data.get('energy_level_at_completion'),
            time_of_day=_get_time_of_day()
        )

        return Response({
            'success': True,
            'task_id': task.id,
            'completion_id': completion.id
        })

    except Todo.DoesNotExist:
        return Response(
            {'error': 'Task not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        print(f"Task completion error: {e}")
        import traceback
        traceback.print_exc()
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def suggest_smart_task(request):
    """
    🎲 Suggest a smart task based on user's current context

    Request:
    {
        "current_energy": "high" | "medium" | "low" (optional),
        "available_minutes": int (optional, default 30),
        "current_mood": "motivated" | "tired" | "stressed" (optional)
    }

    Response:
    {
        "suggested_task": {
            "id": 123,
            "title": "Complete 3 Spanish lessons",
            "energy_level": "medium",
            "cognitive_load": 3,
            "timebox_minutes": 30,
            "category": "language",
            "reason": "Matches your current energy and time. Language progress is at 67%."
        },
        "alternatives": [
            { ... },
            { ... }
        ]
    }
    """
    try:
        current_energy = request.data.get('current_energy', 'medium')
        available_minutes = request.data.get('available_minutes', 30)
        current_mood = request.data.get('current_mood')

        # Get ready tasks
        tasks = Todo.objects.filter(
            user=request.user,
            status='ready',
            scheduled_date__lte=timezone.now().date() + timedelta(days=2),  # Today or next 2 days
        )

        # Filter by energy level
        if current_energy == 'low':
            tasks = tasks.filter(energy_level='low')
        elif current_energy == 'high':
            tasks = tasks.filter(energy_level__in=['high', 'medium'])
        else:  # medium
            tasks = tasks.exclude(energy_level='high')

        # Filter by available time
        tasks = tasks.filter(timebox_minutes__lte=available_minutes)

        # Get category progress to prioritize low-progress categories
        progress = calculate_category_progress(request.user)

        # Score each task
        scored_tasks = []
        for task in tasks:
            score = _calculate_task_score(task, progress, current_mood)
            scored_tasks.append((score, task))

        # Sort by score (highest first)
        scored_tasks.sort(key=lambda x: x[0], reverse=True)

        if not scored_tasks:
            return Response({
                'suggested_task': None,
                'alternatives': [],
                'message': 'No suitable tasks found for your current energy and time.'
            })

        # Get top suggestion
        top_task = scored_tasks[0][1]
        category = top_task.goalspec.category if top_task.goalspec else 'general'
        category_prog = progress.get(category, {})

        suggestion = {
            'id': top_task.id,
            'title': top_task.title,
            'description': top_task.description,
            'energy_level': top_task.energy_level,
            'cognitive_load': top_task.cognitive_load,
            'timebox_minutes': top_task.timebox_minutes,
            'category': category,
            'priority': top_task.priority,
            'scheduled_date': top_task.scheduled_date.isoformat(),
            'reason': _generate_suggestion_reason(top_task, category_prog, current_energy)
        }

        # Get alternatives (next 2-3 tasks)
        alternatives = []
        for score, task in scored_tasks[1:4]:
            cat = task.goalspec.category if task.goalspec else 'general'
            alternatives.append({
                'id': task.id,
                'title': task.title,
                'energy_level': task.energy_level,
                'timebox_minutes': task.timebox_minutes,
                'category': cat,
            })

        return Response({
            'suggested_task': suggestion,
            'alternatives': alternatives
        })

    except Exception as e:
        print(f"Smart suggestion error: {e}")
        import traceback
        traceback.print_exc()
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Helper functions

def _get_time_of_day():
    """Get current time of day bucket"""
    hour = datetime.now().hour
    if 5 <= hour < 12:
        return 'morning'
    elif 12 <= hour < 17:
        return 'afternoon'
    elif 17 <= hour < 22:
        return 'evening'
    else:
        return 'night'


def _calculate_task_score(task, progress, mood):
    """
    Calculate score for task suggestion

    Factors:
    - Priority (3 = high, 2 = medium, 1 = low)
    - Overdue status (bonus)
    - Category progress (lower progress = higher score)
    - Deadline proximity
    """
    score = 0

    # Priority weight
    score += task.priority * 10

    # Overdue bonus
    if task.is_overdue:
        score += 20

    # Category progress (prioritize low-progress categories)
    category = task.goalspec.category if task.goalspec else None
    if category and category in progress:
        cat_prog = progress[category]
        # Lower percentage = higher score
        score += (100 - cat_prog['percentage']) / 5

    # Deadline proximity (closer deadline = higher score)
    days_until = (task.scheduled_date - timezone.now().date()).days
    if days_until <= 1:
        score += 15
    elif days_until <= 3:
        score += 10
    elif days_until <= 7:
        score += 5

    # Mood adjustment
    if mood == 'motivated' and task.cognitive_load >= 4:
        score += 10  # Boost hard tasks when motivated
    elif mood == 'tired' and task.cognitive_load <= 2:
        score += 10  # Boost easy tasks when tired

    return score


def _generate_suggestion_reason(task, category_progress, current_energy):
    """Generate human-readable reason for suggestion"""
    reasons = []

    # Energy match
    reasons.append(f"Matches your {current_energy} energy level")

    # Category progress
    if category_progress and category_progress.get('percentage', 0) < 70:
        reasons.append(f"{task.goalspec.category.title()} progress is at {category_progress['percentage']}%")

    # Deadline
    days_until = (task.scheduled_date - timezone.now().date()).days
    if days_until == 0:
        reasons.append("Due today")
    elif days_until == 1:
        reasons.append("Due tomorrow")
    elif days_until <= 3:
        reasons.append(f"Due in {days_until} days")

    # Priority
    if task.priority == 3:
        reasons.append("High priority")

    return ". ".join(reasons) + "."
