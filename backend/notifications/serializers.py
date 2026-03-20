from rest_framework import serializers
from users.models import User, NotificationPreferences
from .models import Notification, NotificationPreference as NewNotificationPreference


class PushTokenSerializer(serializers.Serializer):
    """Serializer for registering Expo push token"""
    push_token = serializers.CharField(max_length=255, required=True)

    def update(self, instance, validated_data):
        instance.push_token = validated_data.get('push_token')
        instance.push_enabled = True
        instance.save()
        return instance


class NotificationPreferencesSerializer(serializers.ModelSerializer):
    """Serializer for notification preferences"""
    class Meta:
        model = NotificationPreferences
        fields = [
            'task_reminders_enabled',
            'deadline_notifications_enabled',
            'ai_motivation_enabled',
            'daily_pulse_reminder_enabled',
            'task_reminder_minutes_before',
            'daily_pulse_time',
            'quiet_hours_enabled',
            'quiet_hours_start',
            'quiet_hours_end',
        ]

    def create(self, validated_data):
        # Auto-assign user from request context
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data)


class TestNotificationSerializer(serializers.Serializer):
    """Serializer for test notification"""
    title = serializers.CharField(max_length=100, required=False, default="Test Notification")
    body = serializers.CharField(max_length=200, required=False, default="This is a test push notification from PathAI")


# In-App Notification Serializers

class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for in-app Notification model"""

    actor_username = serializers.SerializerMethodField()
    actor_avatar = serializers.SerializerMethodField()
    time_ago = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            'id',
            'notification_type',
            'title',
            'message',
            'data',
            'is_read',
            'read_at',
            'created_at',
            'time_ago',
            'actor',
            'actor_username',
            'actor_avatar',
        ]
        read_only_fields = ['created_at', 'read_at']

    def get_actor_username(self, obj):
        """Get username of actor"""
        if obj.actor:
            return getattr(obj.actor, 'username', obj.actor.email)
        return None

    def get_actor_avatar(self, obj):
        """Get avatar URL of actor"""
        if obj.actor:
            profile = getattr(obj.actor, 'profile', None)
            if profile:
                return getattr(profile, 'avatar_url', None)
        return None

    def get_time_ago(self, obj):
        """Get human-readable time ago"""
        from django.utils import timezone
        import math

        if not obj.created_at:
            return None

        now = timezone.now()
        diff = now - obj.created_at
        seconds = diff.total_seconds()

        if seconds < 60:
            return 'just now'
        elif seconds < 3600:
            minutes = math.floor(seconds / 60)
            return f'{minutes}m ago'
        elif seconds < 86400:
            hours = math.floor(seconds / 3600)
            return f'{hours}h ago'
        elif seconds < 604800:
            days = math.floor(seconds / 86400)
            return f'{days}d ago'
        else:
            weeks = math.floor(seconds / 604800)
            return f'{weeks}w ago'


class NewNotificationPreferenceSerializer(serializers.ModelSerializer):
    """Serializer for enhanced NotificationPreference model"""

    class Meta:
        model = NewNotificationPreference
        fields = '__all__'


class UnreadCountSerializer(serializers.Serializer):
    """Serializer for unread count"""
    unread_count = serializers.IntegerField()


class MarkReadSerializer(serializers.Serializer):
    """Serializer for marking notifications as read"""
    notification_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False
    )
    mark_all = serializers.BooleanField(required=False, default=False)

