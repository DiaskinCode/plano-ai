"""
Task Splitting API Views

Endpoints for intelligently breaking down tasks.
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import Todo
from ai.task_splitter import task_splitter


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def split_task(request, task_id):
    """
    Split a task into sub-tasks using AI.

    Request:
    {
        "user_context": "Optional: Additional context about user's situation"
    }

    Response:
    {
        "parent_task_id": 123,
        "parent_title": "Write SOP",
        "subtasks_created": 3,
        "subtasks": [
            {
                "id": 456,
                "title": "Step 1: Research SOP requirements",
                "scheduled_date": "2025-11-08",
                "timebox_minutes": 30,
                "sequence_order": 1
            },
            ...
        ],
        "message": "Task split into 3 actionable sub-tasks"
    }
    """
    task = get_object_or_404(Todo, id=task_id, user=request.user)
    user_context = request.data.get('user_context', '')

    # Check if task already has subtasks
    if task.subtasks.exists():
        return Response(
            {'error': 'Task already has sub-tasks. Delete them first if you want to re-split.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        # Build user context from profile if not provided
        if not user_context:
            profile = request.user.profile
            context_parts = []

            if task.goalspec and task.goalspec.category == 'study':
                if profile.gpa:
                    context_parts.append(f"GPA: {profile.gpa}")
                if profile.test_scores:
                    context_parts.append(f"Test scores: {profile.test_scores}")
            elif task.goalspec and task.goalspec.category == 'career':
                if profile.years_of_experience:
                    context_parts.append(f"Experience: {profile.years_of_experience} years")
                if profile.current_role:
                    context_parts.append(f"Current role: {profile.current_role}")

            user_context = "\n".join(context_parts)

        # Split and create subtasks
        result = task_splitter.split_and_create(task, user_context)

        return Response(result)

    except Exception as e:
        print(f"Error splitting task: {e}")
        import traceback
        traceback.print_exc()
        return Response(
            {'error': f'Failed to split task: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_split_candidates(request):
    """
    Find tasks that should be split.

    Response:
    {
        "candidates": [
            {
                "task_id": 123,
                "title": "Write SOP",
                "reason": "Overdue by 21 days - needs re-scoping",
                "days_overdue": 21,
                "timebox_minutes": 180,
                "cognitive_load": 4
            },
            ...
        ],
        "count": 3
    }
    """
    user = request.user

    # Get all active tasks
    active_tasks = Todo.objects.filter(
        user=user,
        status__in=['ready', 'in_progress', 'blocked']
    ).exclude(
        parent_task__isnull=False  # Exclude subtasks
    )

    candidates = []

    for task in active_tasks:
        should_split, reason = task_splitter.should_split_task(task)

        if should_split:
            candidates.append({
                "task_id": task.id,
                "title": task.title,
                "reason": reason,
                "days_overdue": task.days_overdue if task.is_overdue else 0,
                "timebox_minutes": task.timebox_minutes,
                "cognitive_load": task.cognitive_load,
                "scheduled_date": str(task.scheduled_date),
            })

    # Sort by most overdue first
    candidates.sort(key=lambda x: x['days_overdue'], reverse=True)

    return Response({
        "candidates": candidates,
        "count": len(candidates),
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_split_tasks(request):
    """
    Split multiple tasks at once (used by AdaptiveCoach).

    Request:
    {
        "task_ids": [123, 456, 789]
    }

    Response:
    {
        "tasks_split": 3,
        "subtasks_created": 9,
        "results": [...]
    }
    """
    task_ids = request.data.get('task_ids', [])

    if not task_ids:
        return Response(
            {'error': 'task_ids is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    user = request.user
    results = []
    total_subtasks = 0

    for task_id in task_ids:
        try:
            task = Todo.objects.get(id=task_id, user=user)

            # Skip if already has subtasks
            if task.subtasks.exists():
                continue

            result = task_splitter.split_and_create(task)
            results.append(result)
            total_subtasks += result['subtasks_created']

        except Todo.DoesNotExist:
            pass
        except Exception as e:
            print(f"Error splitting task {task_id}: {e}")

    return Response({
        "tasks_split": len(results),
        "subtasks_created": total_subtasks,
        "results": results,
    })
