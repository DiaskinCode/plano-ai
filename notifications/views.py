from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from users.models import NotificationPreferences
from .serializers import (
    PushTokenSerializer,
    NotificationPreferencesSerializer,
    TestNotificationSerializer
)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def register_push_token(request):
    """
    Register or update user's Expo push token
    POST /api/notifications/register-token/
    Body: {"push_token": "ExponentPushToken[xxx]"}
    """
    serializer = PushTokenSerializer(data=request.data)
    if serializer.is_valid():
        serializer.update(request.user, serializer.validated_data)
        return Response({
            'message': 'Push token registered successfully',
            'push_enabled': request.user.push_enabled
        }, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def notification_preferences(request):
    """
    Get or update notification preferences
    GET /api/notifications/preferences/
    PUT/PATCH /api/notifications/preferences/
    """
    try:
        preferences = request.user.notification_preferences
    except NotificationPreferences.DoesNotExist:
        # Create default preferences if they don't exist
        preferences = NotificationPreferences.objects.create(user=request.user)

    if request.method == 'GET':
        serializer = NotificationPreferencesSerializer(preferences)
        return Response(serializer.data)

    elif request.method in ['PUT', 'PATCH']:
        partial = request.method == 'PATCH'
        serializer = NotificationPreferencesSerializer(
            preferences,
            data=request.data,
            partial=partial,
            context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_test_notification(request):
    """
    Send a test push notification to the user
    POST /api/notifications/test/
    Body (optional): {"title": "Test", "body": "Test message"}
    """
    serializer = TestNotificationSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    user = request.user

    # Check if user has push token
    if not user.push_token:
        return Response({
            'error': 'No push token registered for this user'
        }, status=status.HTTP_400_BAD_REQUEST)

    if not user.push_enabled:
        return Response({
            'error': 'Push notifications are disabled for this user'
        }, status=status.HTTP_400_BAD_REQUEST)

    # Import notification service (will create later)
    try:
        from .service import NotificationService
        service = NotificationService()

        title = serializer.validated_data.get('title')
        body = serializer.validated_data.get('body')

        result = service.send_push_notification(
            user=user,
            title=title,
            body=body,
            data={'type': 'test'}
        )

        if result.get('success'):
            return Response({
                'message': 'Test notification sent successfully',
                'push_token': user.push_token
            })
        else:
            return Response({
                'error': 'Failed to send notification',
                'details': result.get('error')
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    except ImportError:
        return Response({
            'error': 'Notification service not yet implemented'
        }, status=status.HTTP_501_NOT_IMPLEMENTED)
