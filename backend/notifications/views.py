from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import viewsets
from users.models import NotificationPreferences
from .serializers import (
    PushTokenSerializer,
    NotificationPreferencesSerializer,
    TestNotificationSerializer,
    NotificationSerializer,
    NewNotificationPreferenceSerializer,
    UnreadCountSerializer,
    MarkReadSerializer,
)
from .models import Notification, NotificationPreference as NewNotificationPreference
from .notification_manager import InAppNotificationService


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


# In-App Notification Views

class NotificationViewSet(viewsets.ViewSet):
    """
    ViewSet for managing in-app notifications

    Endpoints:
    - GET /api/notifications/ - List notifications
    - POST /api/notifications/mark-read/ - Mark notifications as read
    - POST /api/notifications/mark-all-read/ - Mark all as read
    - GET /api/notifications/unread-count/ - Get unread count
    """

    permission_classes = [IsAuthenticated]

    def list(self, request):
        """Get all notifications for the authenticated user"""
        unread_only = request.query_params.get('unread_only', 'false').lower() == 'true'
        limit = int(request.query_params.get('limit', 50))

        notifications = InAppNotificationService.get_notifications(
            user_id=request.user.id,
            unread_only=unread_only,
            limit=limit
        )

        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='mark-read')
    def mark_read(self, request):
        """Mark specific notifications as read"""
        serializer = MarkReadSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        mark_all = serializer.validated_data.get('mark_all', False)
        notification_ids = serializer.validated_data.get('notification_ids', [])

        if mark_all:
            count = InAppNotificationService.mark_all_as_read(request.user.id)
            return Response({
                'message': f'Marked {count} notifications as read',
                'count': count
            })
        elif notification_ids:
            # Mark specific notifications
            marked_count = 0
            for notif_id in notification_ids:
                if InAppNotificationService.mark_as_read(notif_id, request.user.id):
                    marked_count += 1

            return Response({
                'message': f'Marked {marked_count} notifications as read',
                'count': marked_count
            })
        else:
            return Response({
                'error': 'Either notification_ids or mark_all must be provided'
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='mark-all-read')
    def mark_all_read(self, request):
        """Mark all notifications as read"""
        count = InAppNotificationService.mark_all_as_read(request.user.id)
        return Response({
            'message': f'Marked {count} notifications as read',
            'count': count
        })

    @action(detail=False, methods=['get'], url_path='unread-count')
    def unread_count(self, request):
        """Get count of unread notifications"""
        count = InAppNotificationService.get_unread_count(request.user.id)
        return Response({'unread_count': count})


class NotificationPreferenceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing notification preferences
    """
    serializer_class = NewNotificationPreferenceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return NewNotificationPreference.objects.filter(user=self.request.user)

    def get_object(self):
        """Get or create notification preferences for user"""
        obj, created = NewNotificationPreference.objects.get_or_create(
            user=self.request.user
        )
        return obj

    def list(self, request):
        """Get notification preferences"""
        obj = self.get_object()
        serializer = self.get_serializer(obj)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        """Update notification preferences"""
        obj = self.get_object()
        serializer = self.get_serializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

