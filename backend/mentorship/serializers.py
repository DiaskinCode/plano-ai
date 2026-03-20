from rest_framework import serializers
from django.utils import timezone

from .models import (
    MentorAvailabilityRule,
    MentorBooking,
    MentorProfile,
    MentorReviewRequest,
    MentorReviewResponse,
)


class MentorProfileSerializer(serializers.ModelSerializer):
    """Serializer for mentor profile with verification fields"""

    class Meta:
        model = MentorProfile
        fields = [
            "id",
            "title",
            "bio",
            "photo_url",
            "education",
            "expertise_areas",
            "hourly_rate_credits",
            "timezone",
            "meeting_link",
            # Verification fields
            "verification_status",
            "verification_video_url",
            "verification_submitted_at",
            "verification_reviewed_at",
            "verification_notes",
            "flag_count",
            "flagged_at",
            # Legacy
            "is_verified",
            "is_active",
            "rating",
            "total_sessions",
            "created_at",
        ]
        read_only_fields = [
            "rating",
            "total_sessions",
            "created_at",
            "verification_reviewed_at",
            "flagged_at",
        ]

    def validate(self, data):
        """Validate and handle verification logic"""
        # If setting video URL for first time, update submission timestamp
        if 'verification_video_url' in data:
            video_url = data.get('verification_video_url')
            if video_url and video_url.strip():
                # Check if this is a new profile (no submission time yet)
                if self.instance and not self.instance.verification_submitted_at:
                    data['verification_submitted_at'] = timezone.now()
                elif self.instance and self.instance.verification_status == 'rejected':
                    # If rejected profile being updated, reset to pending
                    data['verification_status'] = 'pending'
                    data['verification_notes'] = ''  # Clear old notes

        return data


class MentorAvailabilityRuleSerializer(serializers.ModelSerializer):
    """Serializer for availability rules"""

    day_name = serializers.SerializerMethodField()

    class Meta:
        model = MentorAvailabilityRule
        fields = [
            "id",
            "day_of_week",
            "day_name",
            "start_minute",
            "end_minute",
            "is_active",
        ]

    def get_day_name(self, obj):
        day_names = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]
        return day_names[obj.day_of_week]


class MentorBookingSerializer(serializers.ModelSerializer):
    """Serializer for bookings"""

    mentor_title = serializers.CharField(source="mentor.title", read_only=True)
    student_email = serializers.CharField(source="student.email", read_only=True)

    class Meta:
        model = MentorBooking
        fields = [
            "id",
            "mentor",
            "mentor_title",
            "student",
            "student_email",
            "start_at_utc",
            "end_at_utc",
            "duration_minutes",
            "status",
            "topic",
            "student_notes",
            "meeting_url",
            "mentor_summary",
            "action_items",
            "rating",
            "review_text",
            # Flagging fields
            "is_flagged",
            "flag_reason",
            "flagged_at",
            # Timestamps
            "created_at",
            "confirmed_at",
            "completed_at",
        ]
        read_only_fields = ["created_at", "confirmed_at", "completed_at", "flagged_at"]


class MentorReviewRequestSerializer(serializers.ModelSerializer):
    """Serializer for review requests

    Maps 'questions' to 'student_questions' for human-friendly API.
    """

    # Human-friendly field names
    questions = serializers.CharField(
        source="student_questions", required=False, allow_blank=True
    )

    mentor_title = serializers.CharField(source="mentor.title", read_only=True)
    student_email = serializers.CharField(source="student.email", read_only=True)

    class Meta:
        model = MentorReviewRequest
        fields = [
            "id",
            "mentor",
            "mentor_title",
            "student",
            "student_email",
            "request_type",
            "goal_spec",
            "essay_project",
            "status",
            "questions",
            "price_credits",
            "created_at",
            "responded_at",
        ]
        read_only_fields = ["created_at", "responded_at"]


class PlanReviewSubmissionSerializer(serializers.Serializer):
    """Human-friendly serializer for plan review submission"""

    overall_comment = serializers.CharField()
    verdict = serializers.ChoiceField(
        choices=[
            ("approved", "Approved"),
            ("approved_with_changes", "Approved with Changes"),
            ("rejected", "Rejected"),
        ]
    )
    top_risks = serializers.ListField(
        child=serializers.CharField(), required=False, default=[]
    )
    next_steps = serializers.ListField(
        child=serializers.CharField(), required=False, default=[]
    )
    suggestions = serializers.ListField(
        child=serializers.DictField(), required=False, default=[]
    )

    def validate_suggestions(self, value):
        """Validate suggestion structure"""
        for sugg in value:
            if "type" not in sugg:
                raise serializers.ValidationError("Each suggestion must have a 'type'")

            sugg_type = sugg["type"]

            if sugg_type == "change_deadline":
                if "task_id" not in sugg or "new_due_date" not in sugg:
                    raise serializers.ValidationError(
                        "change_deadline suggestions require 'task_id' and 'new_due_date'"
                    )
            elif sugg_type == "add_task":
                if "title" not in sugg or "due_date" not in sugg:
                    raise serializers.ValidationError(
                        "add_task suggestions require 'title' and 'due_date'"
                    )
            else:
                raise serializers.ValidationError(
                    f"Unknown suggestion type: {sugg_type}"
                )

        return value


class EssayReviewSubmissionSerializer(serializers.Serializer):
    """Human-friendly serializer for essay review submission"""

    overall_comment = serializers.CharField()
    strengths = serializers.ListField(
        child=serializers.CharField(), required=False, default=[]
    )
    improvements = serializers.ListField(
        child=serializers.CharField(), required=False, default=[]
    )
    rewrite_suggestions = serializers.ListField(
        child=serializers.DictField(), required=False, default=[]
    )
    scores = serializers.DictField(
        child=serializers.IntegerField(min_value=1, max_value=10),
        required=False,
        default={},
    )


class MentorReviewResponseSerializer(serializers.ModelSerializer):
    """Serializer for review responses"""

    mentor_title = serializers.CharField(source="mentor.title", read_only=True)

    class Meta:
        model = MentorReviewResponse
        fields = [
            "id",
            "request",
            "mentor_title",
            "overall_comment",
            "payload_json",
            "created_at",
        ]
        read_only_fields = ["created_at"]


class TimeSlotSerializer(serializers.Serializer):
    """Serializer for generated time slots"""

    start_at_utc = serializers.DateTimeField()
    end_at_utc = serializers.DateTimeField()
    duration_minutes = serializers.IntegerField()


class AvailabilitySerializer(serializers.Serializer):
    """Serializer for availability response"""

    mentor_timezone = serializers.CharField()
    slots = TimeSlotSerializer(many=True)
