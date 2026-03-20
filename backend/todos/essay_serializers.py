"""
Serializers for Essay Writing Assistance Models

Handles JSON serialization/deserialization for:
- EssayTemplate
- EssayProject
- EssayFeedback
"""

from rest_framework import serializers
from .essay_models import EssayTemplate, EssayProject, EssayFeedback


class EssayTemplateSerializer(serializers.ModelSerializer):
    """Serializer for essay templates"""

    icon = serializers.ReadOnlyField()

    class Meta:
        model = EssayTemplate
        fields = [
            'id', 'name', 'essay_type', 'icon', 'prompt',
            'word_count_min', 'word_count_max', 'universities',
            'structure_outline', 'key_themes', 'tips', 'sample_essays',
            'order', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class EssayTemplateListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing templates"""

    icon = serializers.ReadOnlyField()

    class Meta:
        model = EssayTemplate
        fields = ['id', 'name', 'essay_type', 'icon', 'word_count_min', 'word_count_max']


class EssayFeedbackSerializer(serializers.ModelSerializer):
    """Serializer for essay feedback"""

    class Meta:
        model = EssayFeedback
        fields = [
            'id', 'essay_project', 'draft_content', 'draft_word_count',
            'ai_strengths', 'ai_improvements', 'ai_structure_feedback',
            'ai_content_feedback', 'ai_voice_feedback', 'ai_grammar_feedback',
            'ai_score', 'ai_detailed_feedback',
            'human_feedback', 'human_score', 'human_reviewer',
            'feedback_type', 'created_at'
        ]
        read_only_fields = ['created_at']


class EssayProjectSerializer(serializers.ModelSerializer):
    """Full serializer for essay projects"""

    template = EssayTemplateSerializer(read_only=True)
    template_id = serializers.IntegerField(write_only=True, required=False)
    feedback_history_data = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = EssayProject
        fields = [
            'id', 'user', 'template', 'template_id',
            'title', 'essay_type', 'target_university', 'target_prompt',
            'status', 'status_display',
            'current_draft', 'word_count', 'revision_count',
            'brainstorming_notes', 'selected_topic', 'outline_suggestions',
            'feedback_history', 'feedback_history_data',
            'deadline', 'word_count_goal', 'progress_percentage',
            'related_task',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'user', 'created_at', 'updated_at',
            'feedback_history_data', 'status_display'
        ]

    def get_feedback_history_data(self, obj):
        """Get detailed feedback history"""
        feedback_sessions = obj.feedback_sessions.all()[:5]  # Last 5 feedback sessions
        return EssayFeedbackSerializer(feedback_sessions, many=True).data

    def create(self, validated_data):
        """Create essay project"""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class EssayProjectListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing essay projects"""

    template_name = serializers.CharField(source='template.name', read_only=True)
    template_icon = serializers.CharField(source='template.icon', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = EssayProject
        fields = [
            'id', 'title', 'essay_type', 'target_university',
            'template_name', 'template_icon',
            'status', 'status_display',
            'word_count', 'word_count_goal', 'progress_percentage',
            'deadline', 'updated_at'
        ]


class EssayProjectDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for single essay project view"""

    template = EssayTemplateSerializer(read_only=True)
    feedback_sessions = EssayFeedbackSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = EssayProject
        fields = [
            'id', 'user', 'template',
            'title', 'essay_type', 'target_university', 'target_prompt',
            'status', 'status_display',
            'current_draft', 'word_count', 'revision_count',
            'brainstorming_notes', 'selected_topic', 'outline_suggestions',
            'feedback_sessions', 'feedback_history',
            'deadline', 'word_count_goal', 'progress_percentage',
            'related_task',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']
