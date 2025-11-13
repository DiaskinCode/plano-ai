from rest_framework import serializers
from .models import CheckInEvent, OpportunityEvent


class CheckInEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = CheckInEvent
        fields = '__all__'
        read_only_fields = ('user', 'ai_response', 'ai_recommendations', 'created_at', 'updated_at')


class CheckInEventCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating check-in events"""
    class Meta:
        model = CheckInEvent
        fields = ('date', 'completed_tasks', 'completed_tasks_text',
                  'missed_tasks', 'missed_tasks_text', 'missed_reason',
                  'new_opportunities')

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class OpportunityEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = OpportunityEvent
        fields = '__all__'
        read_only_fields = ('user', 'ai_impact_assessment', 'ai_recommendation',
                            'requires_vision_change', 'created_at', 'updated_at')


class OpportunityEventCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating opportunity events"""
    class Meta:
        model = OpportunityEvent
        fields = ('title', 'description', 'date_occurred')

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
