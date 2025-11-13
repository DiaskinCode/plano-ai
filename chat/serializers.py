from rest_framework import serializers
from .models import ChatConversation, ChatMessage, ChatSummary


class ChatConversationSerializer(serializers.ModelSerializer):
    message_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = ChatConversation
        fields = ('id', 'title', 'message_count', 'last_message', 'created_at', 'updated_at')
        read_only_fields = ('created_at', 'updated_at')

    def get_message_count(self, obj):
        return obj.messages.count()

    def get_last_message(self, obj):
        last = obj.messages.last()
        return last.content[:50] if last else None


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = '__all__'
        read_only_fields = ('user', 'created_at', 'context_used')


class ChatMessageCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating user messages"""
    class Meta:
        model = ChatMessage
        fields = ('content', 'is_voice', 'audio_url')

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        validated_data['role'] = 'user'
        return super().create(validated_data)


class ChatMessageListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing messages"""
    class Meta:
        model = ChatMessage
        fields = ('id', 'role', 'content', 'is_voice', 'created_at')


class ChatSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatSummary
        fields = '__all__'
        read_only_fields = ('user', 'created_at', 'updated_at')
