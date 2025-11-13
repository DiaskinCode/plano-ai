from rest_framework import serializers
from users.models import User, NotificationPreferences


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
