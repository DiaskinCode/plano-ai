from rest_framework import serializers
from .models import UniversitySeekerProfile, ExtracurricularActivity


class ExtracurricularActivitySerializer(serializers.ModelSerializer):
    """Serializer for extracurricular activities"""

    class Meta:
        model = ExtracurricularActivity
        fields = (
            'id', 'category', 'title', 'role',
            'hours_per_week', 'weeks_per_year', 'years_participated',
            'impact_level', 'leadership_position', 'achievements', 'achievements_impact',
            'created_at', 'updated_at'
        )
        read_only_fields = ('created_at', 'updated_at')


class UniversitySeekerProfileSerializer(serializers.ModelSerializer):
    """Serializer for university seeker profile"""
    extracurriculars = ExtracurricularActivitySerializer(
        many=True,
        read_only=True,
        source='extracurriculars.all'
    )
    completion_percentage = serializers.ReadOnlyField()
    user_email = serializers.SerializerMethodField()

    class Meta:
        model = UniversitySeekerProfile
        fields = (
            'id', 'user', 'user_email',
            # Academic Profile
            'gpa', 'gpa_scale', 'sat_score', 'sat_english', 'sat_math',
            'act_score', 'toefl_score', 'ielts_score', 'duolingo_score',
            'course_rigor', 'ap_courses', 'ib_courses', 'academic_competitions',
            # Personal/Financial
            'country', 'citizenship', 'budget_currency', 'max_budget', 'financial_need',
            'need_blind_preference', 'merit_aid_required',
            # Academic Interests
            'intended_major_1', 'intended_major_2', 'intended_major_3', 'academic_interests',
            # Campus Preferences
            'preferred_size', 'preferred_location', 'preferred_region', 'weather_preference',
            # Constraints
            'target_countries', 'excluded_universities',
            'test_optional_flexible', 'early_decision_willing', 'early_action_willing',
            # Spike
            'spike_area', 'spike_achievement',
            # NEW: Additional context for LLM personalization
            'additional_context',
            # Metadata
            'extracurriculars', 'completion_percentage', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'user', 'created_at', 'updated_at', 'completion_percentage')

    def get_user_email(self, obj):
        return obj.user.email if obj.user else None


class UniversitySeekerProfileCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new profile"""

    class Meta:
        model = UniversitySeekerProfile
        fields = (
            # Academic Profile
            'gpa', 'gpa_scale', 'sat_score', 'sat_english', 'sat_math',
            'act_score', 'toefl_score', 'ielts_score', 'duolingo_score',
            'course_rigor', 'ap_courses', 'ib_courses', 'academic_competitions',
            # Personal/Financial
            'country', 'citizenship', 'budget_currency', 'max_budget', 'financial_need',
            'need_blind_preference', 'merit_aid_required',
            # Academic Interests
            'intended_major_1', 'intended_major_2', 'intended_major_3', 'academic_interests',
            # Campus Preferences
            'preferred_size', 'preferred_location', 'preferred_region', 'weather_preference',
            # Constraints
            'target_countries', 'excluded_universities',
            'test_optional_flexible', 'early_decision_willing', 'early_action_willing',
            # Spike
            'spike_area', 'spike_achievement',
            # NEW: Additional context for LLM personalization
            'additional_context',
        )

    def validate_intended_major_1(self, value):
        """Ensure at least primary major is provided"""
        if not value or value.strip() == '':
            raise serializers.ValidationError("Primary intended major is required")
        return value

    def validate_gpa(self, value):
        """Ensure GPA is valid"""
        if value < 0 or value > 100:
            raise serializers.ValidationError("GPA must be between 0 and 100")
        return value


class UniversitySeekerProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating an existing profile"""

    class Meta:
        model = UniversitySeekerProfile
        fields = (
            # Academic Profile
            'gpa', 'gpa_scale', 'sat_score', 'sat_english', 'sat_math',
            'act_score', 'toefl_score', 'ielts_score', 'duolingo_score',
            'course_rigor', 'ap_courses', 'ib_courses', 'academic_competitions',
            # Personal/Financial
            'country', 'citizenship', 'budget_currency', 'max_budget', 'financial_need',
            'need_blind_preference', 'merit_aid_required',
            # Academic Interests
            'intended_major_1', 'intended_major_2', 'intended_major_3', 'academic_interests',
            # Campus Preferences
            'preferred_size', 'preferred_location', 'preferred_region', 'weather_preference',
            # Constraints
            'target_countries', 'excluded_universities',
            'test_optional_flexible', 'early_decision_willing', 'early_action_willing',
            # Spike
            'spike_area', 'spike_achievement',
            # NEW: Additional context for LLM personalization
            'additional_context',
        )

    def update(self, instance, validated_data):
        """Update profile fields"""
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
