"""
Adaptive Coach Intervention API Views

Endpoints for triggering and applying Plan-B interventions.
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone

from ai.adaptive_coach import adaptive_coach


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_intervention(request):
    """
    Check if user needs Plan-B intervention.

    Response:
    {
        "intervention_needed": true,
        "intervention": {
            "type": "planb_switch",
            "severity": "critical",
            "title": "⚠️ Let's reset your plan",
            "message": "...",
            "actions": [...],
            "alternative_paths": [...]
        }
    }

    OR

    {
        "intervention_needed": false,
        "message": "You're on track!"
    }
    """
    user = request.user

    intervention = adaptive_coach.check_and_intervene(user)

    if intervention:
        return Response({
            "intervention_needed": True,
            "intervention": intervention,
        })
    else:
        return Response({
            "intervention_needed": False,
            "message": "You're on track! No intervention needed.",
        })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def apply_intervention(request):
    """
    Apply intervention actions to user's tasks.

    Request:
    {
        "intervention": {
            "type": "planb_switch",
            "actions": [...]
        }
    }

    Response:
    {
        "success": true,
        "tasks_updated": 5,
        "deadlines_extended": 3,
        "tasks_paused": 2,
        "message": "Successfully applied changes"
    }
    """
    user = request.user
    intervention = request.data.get('intervention')

    if not intervention:
        return Response(
            {'error': 'intervention is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        # Apply intervention actions
        result = adaptive_coach.apply_intervention_actions(user, intervention)

        # Log acceptance in user profile
        profile = user.profile
        intervention_record = {
            "date": timezone.now().isoformat(),
            "type": intervention.get("type"),
            "severity": intervention.get("severity"),
            "accepted": True,
            "actions_applied": len(intervention.get("actions", [])),
        }

        if not profile.intervention_history:
            profile.intervention_history = []

        profile.intervention_history.append(intervention_record)
        profile.save(update_fields=['intervention_history'])

        return Response({
            "success": True,
            **result
        })

    except Exception as e:
        print(f"Error applying intervention: {e}")
        import traceback
        traceback.print_exc()
        return Response(
            {'error': f'Failed to apply intervention: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def dismiss_intervention(request):
    """
    User dismisses intervention without accepting.

    Request:
    {
        "intervention_type": "planb_switch",
        "reason": "I want to continue my current plan"
    }

    Response:
    {
        "success": true,
        "message": "Intervention dismissed"
    }
    """
    user = request.user
    intervention_type = request.data.get('intervention_type')
    dismiss_reason = request.data.get('reason', '')

    profile = user.profile

    # Log dismissal
    intervention_record = {
        "date": timezone.now().isoformat(),
        "type": intervention_type,
        "accepted": False,
        "dismiss_reason": dismiss_reason,
    }

    if not profile.intervention_history:
        profile.intervention_history = []

    profile.intervention_history.append(intervention_record)

    # Update cooldown to avoid immediate re-intervention
    profile.last_intervention_at = timezone.now()
    profile.save(update_fields=['intervention_history', 'last_intervention_at'])

    return Response({
        "success": True,
        "message": "Intervention dismissed. We'll check again in a few days.",
    })
