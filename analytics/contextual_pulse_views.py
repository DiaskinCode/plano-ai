"""
Context-Aware Daily Pulse API Views

Enhanced Daily Pulse that uses performance insights.
"""

from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django.utils import timezone

from ai.contextual_pulse_generator import contextual_pulse_generator
from todos.models import Todo


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def generate_contextual_pulse(request):
    """
    Generate context-aware Daily Pulse using performance insights.

    Response:
    {
        "greeting_message": "☀️ Good morning! ...",
        "top_priorities": [
            {
                "task_id": 123,
                "title": "Write SOP draft",
                "reason": "High impact for your Cambridge application",
                "timebox_minutes": 60,
                "priority": 3
            },
            ...
        ],
        "workload_assessment": {
            "percentage": 85,
            "status": "manageable",
            "message": "You have 4 hours of work scheduled",
            "total_minutes": 240
        },
        "warnings": [
            "⚠️ Task overdue 7 days: Write SOP. Let's re-scope?"
        ],
        "smart_suggestions": [
            "💡 Your peak productivity is 9-11am. Schedule SOP draft then."
        ],
        "coaching_note": "Based on last week's patterns...",
        "full_message": "Comprehensive daily briefing...",
        "generated_at": "2025-11-06T08:00:00Z"
    }
    """
    user = request.user
    today = timezone.now().date()

    # Get today's tasks
    daily_tasks = Todo.objects.filter(
        user=user,
        scheduled_date=today,
        status__in=['ready', 'in_progress']
    ).order_by('-priority', 'scheduled_time')

    if not daily_tasks.exists():
        return Response({
            "message": "No tasks scheduled for today",
            "greeting_message": "☀️ You have a free day! Consider planning ahead.",
            "top_priorities": [],
            "workload_assessment": {
                "percentage": 0,
                "status": "light",
                "message": "No tasks scheduled",
                "total_minutes": 0,
            },
            "warnings": [],
            "smart_suggestions": ["💡 Use today to plan tasks for the rest of the week"],
            "coaching_note": "A light day can be great for planning and reflection.",
            "full_message": "You have a free day ahead. Consider using this time for planning.",
            "generated_at": timezone.now().isoformat(),
        })

    try:
        # Generate context-aware pulse
        pulse = contextual_pulse_generator.generate_contextual_pulse(
            user=user,
            daily_tasks=list(daily_tasks)
        )

        return Response(pulse)

    except Exception as e:
        print(f"Error generating contextual pulse: {e}")
        import traceback
        traceback.print_exc()

        return Response(
            {'error': f'Failed to generate pulse: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
