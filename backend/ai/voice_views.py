"""
Voice Interface API Views

Endpoints for voice command processing.
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .voice_processor import voice_processor


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def process_voice_command(request):
    """
    Process voice command and return structured response.

    Request:
    {
        "transcript": "Add task review Cambridge application by Friday",
        "timestamp": "2025-11-06T10:30:00Z"
    }

    Response:
    {
        "intent": "create_task",
        "action_taken": {
            "task_id": 123,
            "title": "Review Cambridge application",
            "scheduled_date": "2025-11-08"
        },
        "response_text": "Got it! I've added 'Review Cambridge application' for Friday.",
        "success": true
    }
    """
    transcript = request.data.get('transcript', '').strip()

    if not transcript:
        return Response(
            {'error': 'transcript is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        # Process voice command
        result = voice_processor.process_command(
            user=request.user,
            transcript=transcript
        )

        return Response(result)

    except Exception as e:
        print(f"Error processing voice command: {e}")
        import traceback
        traceback.print_exc()

        return Response(
            {
                'error': f'Failed to process command: {str(e)}',
                'response_text': "Sorry, I encountered an error. Could you try again?"
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def voice_query(request):
    """
    Answer voice query using contextual data.

    Request:
    {
        "query": "Coach, am I on track?",
        "context": "performance" // Optional: daily_pulse, performance, tasks
    }

    Response:
    {
        "answer": "You're on a 5-day streak with 65% completion rate...",
        "data": {
            "streak": 5,
            "completion_rate": 0.65
        }
    }
    """
    query = request.data.get('query', '').strip()
    context_type = request.data.get('context', 'general')

    if not query:
        return Response(
            {'error': 'query is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        # Process as coach query
        result = voice_processor.process_command(
            user=request.user,
            transcript=query
        )

        return Response({
            "answer": result.get('response_text', ''),
            "data": result.get('action_taken', {}),
            "intent": result.get('intent', 'unknown')
        })

    except Exception as e:
        print(f"Error processing voice query: {e}")
        return Response(
            {'error': f'Failed to process query: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def voice_capabilities(request):
    """
    Return list of supported voice commands.

    Response:
    {
        "capabilities": [
            {
                "intent": "create_task",
                "examples": [
                    "Add task review Cambridge application by Friday",
                    "Create task call mentor tomorrow"
                ],
                "description": "Create a new task with optional deadline"
            },
            ...
        ]
    }
    """
    capabilities = [
        {
            "intent": "create_task",
            "examples": [
                "Add task review Cambridge application by Friday",
                "Create task call mentor tomorrow",
                "Remind me to submit IELTS scores next week"
            ],
            "description": "Create a new task with optional deadline and priority"
        },
        {
            "intent": "complete_task",
            "examples": [
                "Mark task done: Write SOP",
                "I completed the research task",
                "Finished writing my essay"
            ],
            "description": "Mark a task as completed"
        },
        {
            "intent": "list_tasks",
            "examples": [
                "What's on my agenda today?",
                "Show my tasks for this week",
                "What tasks are overdue?"
            ],
            "description": "List tasks with optional filters (today, week, overdue)"
        },
        {
            "intent": "coach_query",
            "examples": [
                "Coach, am I on track?",
                "How am I doing?",
                "What should I focus on?"
            ],
            "description": "Ask the adaptive coach for advice"
        },
        {
            "intent": "performance_query",
            "examples": [
                "What's my completion rate this week?",
                "How many tasks did I complete today?",
                "What's my current streak?"
            ],
            "description": "Get performance statistics"
        },
        {
            "intent": "daily_checkin",
            "examples": [
                "Start daily check-in",
                "I completed 3 out of 5 tasks today",
                "Today was overwhelming"
            ],
            "description": "Do daily check-in and get coaching feedback"
        },
    ]

    return Response({"capabilities": capabilities})
