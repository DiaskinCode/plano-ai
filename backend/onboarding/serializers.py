"""
Serializers for the onboarding API.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    OnboardingState,
    SubscriptionPlan,
    UserSubscription,
    TargetUniversity,
    ExtracurricularActivity,
    OnboardingSnapshot,
)

User = get_user_model()


class OnboardingStateSerializer(serializers.ModelSerializer):
    """Serializer for OnboardingState model"""
    progress_percentage = serializers.SerializerMethodField()

    class Meta:
        model = OnboardingState
        fields = [
            'id',
            'user',
            'current_step',
            'completed_steps',
            'data',
            'selected_language',
            'is_onboarding_complete',
            'progress_percentage',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']

    def get_progress_percentage(self, obj):
        return obj.get_progress_percentage()


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    """Serializer for SubscriptionPlan model"""

    class Meta:
        model = SubscriptionPlan
        fields = [
            'id',
            'name',
            'display_name',
            'price_monthly',
            'price_yearly',
            'features',
            'is_popular',
            'is_active',
            'order',
            'monthly_video_calls',
            'monthly_text_questions',
            'monthly_mentor_bookings',
            'dedicated_mentor',
        ]


class UserSubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for UserSubscription model"""
    plan_details = SubscriptionPlanSerializer(source='plan', read_only=True)
    is_active_status = serializers.SerializerMethodField()
    can_book_mentor_session = serializers.SerializerMethodField()
    mentor_booking_limit = serializers.SerializerMethodField()

    class Meta:
        model = UserSubscription
        fields = [
            'id',
            'user',
            'plan',
            'plan_details',
            'status',
            'stripe_subscription_id',
            'stripe_customer_id',
            'current_period_start',
            'current_period_end',
            'cancel_at_period_end',
            'mentor_assigned',
            'remaining_video_calls',
            'remaining_text_questions',
            'remaining_mentor_bookings',
            'promo_code_used',
            'discount_percentage',
            'is_active_status',
            'can_book_mentor_session',
            'mentor_booking_limit',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'user',
            'stripe_subscription_id',
            'stripe_customer_id',
            'created_at',
            'updated_at',
        ]

    def get_is_active_status(self, obj):
        return obj.is_active()

    def get_can_book_mentor_session(self, obj):
        return obj.can_book_mentor_session()

    def get_mentor_booking_limit(self, obj):
        return obj.get_mentor_booking_limit()


class TargetUniversitySerializer(serializers.ModelSerializer):
    """Serializer for TargetUniversity model"""

    class Meta:
        model = TargetUniversity
        fields = [
            'id',
            'user',
            'university_name',
            'university_slug',
            'category',
            'country',
            'state_province',
            'city',
            'acceptance_rate',
            'avg_sat',
            'avg_act',
            'tuition_per_year',
            'application_deadline',
            'major',
            'why_suggested',
            'is_ai_suggested',
            'is_selected',
            'priority_order',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']


class ExtracurricularActivitySerializer(serializers.ModelSerializer):
    """Serializer for ExtracurricularActivity model"""

    class Meta:
        model = ExtracurricularActivity
        fields = [
            'id',
            'user',
            'category',
            'title',
            'organization',
            'role',
            'description',
            'start_date',
            'end_date',
            'is_ongoing',
            'hours_per_week',
            'achievements',
            'leadership_role',
            'priority_order',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']


class OnboardingSnapshotSerializer(serializers.ModelSerializer):
    """Serializer for OnboardingSnapshot model"""

    class Meta:
        model = OnboardingSnapshot
        fields = [
            'id',
            'user',
            'step',
            'data',
            'time_spent_seconds',
            'created_at',
        ]
        read_only_fields = ['user', 'created_at']


# ==================== Request Serializers ====================

class StartOnboardingSerializer(serializers.Serializer):
    """Serializer for starting onboarding"""
    language = serializers.ChoiceField(
        choices=['en', 'ru', 'kk', 'zh'],
        default='en',
        help_text="Selected language code"
    )


class SaveStepSerializer(serializers.Serializer):
    """Serializer for saving onboarding step data"""
    step = serializers.IntegerField(min_value=0, max_value=13, help_text="Step number (0-13)")
    data = serializers.JSONField(help_text="Data collected at this step")
    time_spent_seconds = serializers.IntegerField(
        default=0,
        min_value=0,
        help_text="Time spent on this step in seconds"
    )
    mark_complete = serializers.BooleanField(
        default=False,
        help_text="Whether to mark this step as complete"
    )


class AcademicProfileSerializer(serializers.Serializer):
    """Serializer for academic profile data (Step 4)"""
    student_status = serializers.ChoiceField(
        choices=['high_school', 'graduate', 'college', 'gap_year']
    )
    school_name = serializers.CharField(max_length=200)
    graduation_year = serializers.IntegerField()
    gpa = serializers.DecimalField(max_digits=3, decimal_places=2, required=False)
    gpa_scale = serializers.ChoiceField(
        choices=['4.0', '5.0', '100', 'A-F'],
        required=False
    )
    specialization = serializers.CharField(max_length=100, required=False)
    favorite_subjects = serializers.ListField(
        child=serializers.CharField(max_length=50),
        max_length=3,
        required=False
    )


class TestScoresSerializer(serializers.Serializer):
    """Serializer for test scores (Step 5)"""
    sat_status = serializers.ChoiceField(choices=['not_taken', 'taken', 'planning'])
    sat_score = serializers.IntegerField(required=False, min_value=400, max_value=1600)
    sat_math = serializers.IntegerField(required=False, min_value=200, max_value=800)
    sat_reading = serializers.IntegerField(required=False, min_value=200, max_value=800)
    sat_date = serializers.DateField(required=False)

    ielts_status = serializers.ChoiceField(choices=['not_taken', 'taken', 'planning'])
    ielts_score = serializers.DecimalField(max_digits=3, decimal_places=1, required=False)
    ielts_date = serializers.DateField(required=False)

    toefl_status = serializers.ChoiceField(choices=['not_taken', 'taken', 'planning'])
    toefl_score = serializers.IntegerField(required=False, min_value=0, max_value=120)
    toefl_date = serializers.DateField(required=False)

    act_status = serializers.ChoiceField(choices=['not_taken', 'taken', 'planning'])
    act_score = serializers.IntegerField(required=False, min_value=1, max_value=36)
    act_date = serializers.DateField(required=False)


class PlanSelectionSerializer(serializers.Serializer):
    """Serializer for plan selection (Step 8)"""
    selected_plans = serializers.ListField(
        child=serializers.ChoiceField(choices=['university', 'exam_prep', 'language_tests']),
        help_text="Selected plan types"
    )
    exam_types = serializers.ListField(
        child=serializers.ChoiceField(choices=['SAT', 'ACT', 'CSEE']),
        required=False,
        help_text="Selected exam types for exam_prep plan"
    )
    language_test_types = serializers.ListField(
        child=serializers.ChoiceField(choices=['IELTS', 'TOEFL', 'HSK', 'DELF']),
        required=False,
        help_text="Selected language test types"
    )


class GeneratePlanSerializer(serializers.Serializer):
    """Serializer for generating AI plan"""
    include_timeline = serializers.BooleanField(default=True)
    include_tasks = serializers.BooleanField(default=True)
    include_milestones = serializers.BooleanField(default=True)


class CreateCheckoutSessionSerializer(serializers.Serializer):
    """Serializer for creating Stripe checkout session"""
    plan_name = serializers.ChoiceField(choices=['basic', 'pro', 'premium'])
    billing_cycle = serializers.ChoiceField(choices=['monthly', 'yearly'], default='monthly')
    promo_code = serializers.CharField(max_length=50, required=False)
    success_url = serializers.URLField(required=False)
    cancel_url = serializers.URLField(required=False)


class CancelSubscriptionSerializer(serializers.Serializer):
    """Serializer for canceling subscription"""
    cancel_at_period_end = serializers.BooleanField(
        default=True,
        help_text="If True, subscription cancels at period end. If False, cancels immediately."
    )
