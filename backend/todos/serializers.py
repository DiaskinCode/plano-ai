from django.utils import timezone
from rest_framework import serializers

from .artifact_models import TaskArtifact, TaskEvidence, TaskRun
from .models import TaskCategory, Todo


class TaskCategorySerializer(serializers.ModelSerializer):
    """Serializer for task categories"""

    class Meta:
        model = TaskCategory
        fields = ("id", "name", "icon", "color", "description", "order")


class TaskArtifactSerializer(serializers.ModelSerializer):
    """Serializer for task artifacts"""

    class Meta:
        model = TaskArtifact
        fields = "__all__"
        read_only_fields = ("created_at", "updated_at")


class TaskEvidenceSerializer(serializers.ModelSerializer):
    """Serializer for task evidence"""

    class Meta:
        model = TaskEvidence
        fields = "__all__"
        read_only_fields = ("uploaded_at", "uploaded_by")


class TaskRunSerializer(serializers.ModelSerializer):
    """Serializer for task run sessions"""

    class Meta:
        model = TaskRun
        fields = "__all__"
        read_only_fields = ("started_at", "completed_at")


class TodoSerializer(serializers.ModelSerializer):
    is_overdue = serializers.ReadOnlyField()
    days_overdue = serializers.ReadOnlyField()
    progress_percentage = serializers.ReadOnlyField()

    # NEW: University-related fields for eligibility system
    university_name = serializers.CharField(source="university.name", read_only=True)
    university_logo = serializers.SerializerMethodField()
    university_short_name = serializers.CharField(
        source="university.short_name", read_only=True
    )
    university_location = serializers.CharField(
        source="university.location_country", read_only=True
    )

    # Related objects
    artifacts = TaskArtifactSerializer(many=True, read_only=True)
    evidence = TaskEvidenceSerializer(many=True, read_only=True)
    runs = TaskRunSerializer(many=True, read_only=True)

    class Meta:
        model = Todo
        fields = "__all__"
        read_only_fields = (
            "user",
            "created_at",
            "updated_at",
            "is_overdue",
            "days_overdue",
            "progress_percentage",
            "artifacts",
            "evidence",
            "runs",
        )

    def get_university_logo(self, obj):
        """Get university logo with empty fallback"""
        if obj.university and obj.university.logo_url:
            return obj.university.logo_url
        return ""

    def update(self, instance, validated_data):
        # Auto-set completion timestamps
        if validated_data.get("status") == "done" and not instance.completed_at:
            validated_data["completed_at"] = timezone.now()
            # Unlock dependent tasks
            instance.unlock_dependents()
        elif validated_data.get("status") == "skipped" and not instance.skipped_at:
            validated_data["skipped_at"] = timezone.now()

        # Update progress if DoD changed
        if "definition_of_done" in validated_data:
            instance = super().update(instance, validated_data)
            instance.update_progress()
            return instance

        return super().update(instance, validated_data)


class TodoCreateSerializer(serializers.ModelSerializer):
    """Serializer for user-created todos (simplified for manual entry)"""

    class Meta:
        model = Todo
        fields = (
            "title",
            "description",
            "priority",
            "scheduled_date",
            "scheduled_time",
            "task_type",
            "timebox_minutes",
            "deliverable_type",
            "constraints",
            "definition_of_done",
        )

    def create(self, validated_data):
        validated_data["source"] = "user_added"
        validated_data["user"] = self.context["request"].user

        # Set default status
        if "status" not in validated_data:
            validated_data["status"] = "ready"

        # Generate idempotency key if not provided
        if "idempotency_key" not in validated_data:
            user_id = self.context["request"].user.id
            date = validated_data.get("scheduled_date")
            title = validated_data.get("title", "")[:50]
            validated_data["idempotency_key"] = f"{user_id}_{date}_{title}"

        return super().create(validated_data)


class TodoListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing todos"""

    is_overdue = serializers.ReadOnlyField()
    category = TaskCategorySerializer(read_only=True)
    university_name = serializers.CharField(source="university.name", read_only=True)
    university_short_name = serializers.CharField(source="university.short_name", read_only=True)
    university_checklist = serializers.JSONField(read_only=True)  # ✅ Add university_checklist for global tasks

    # ✅ FIX: Return university as object with id for frontend grouping
    # Frontend groups by todo.university.id, so we need to return {id, name}
    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Transform university from ID to object
        if instance.university:
            data['university'] = {
                'id': instance.university.id,
                'name': instance.university.name,
                'short_name': instance.university.short_name,
            }
        return data

    class Meta:
        model = Todo
        fields = (
            "id",
            "title",
            "priority",
            "scheduled_date",
            "scheduled_time",
            "status",
            "is_overdue",
            "source",
            "task_type",
            "timebox_minutes",
            "deliverable_type",
            "progress_percentage",
            "goalspec",
            "energy_level",
            "reminder_time",  # For local notification scheduling
            "category",  # Add category field for college admissions tasks
            "university",  # ✅ Add university field
            "university_name",  # ✅ Add university_name for display
            "university_short_name",  # ✅ Add short_name
            "university_checklist",  # ✅ Add checklist showing which universities require this global task
            "scope",  # ✅ Add scope for grouping
            "stage",  # ✅ Add stage for filtering
            "description",  # ✅ Add description for AI-enhanced tasks
            "notes",  # ✅ Add notes for AI-generated steps and tips
            "link_url",  # ✅ Add link URL
            "link_type",  # ✅ Add link type
            "evidence_fields",  # ✅ Add evidence fields
            "evidence_status",  # ✅ Add evidence status
            "is_auto_generated",  # ✅ Add auto-generated flag
        )


class AtomicTaskSerializer(serializers.ModelSerializer):
    """
    Full serializer for atomic tasks with all fields
    Used for AI-generated tasks and detailed views
    """

    is_overdue = serializers.ReadOnlyField()
    days_overdue = serializers.ReadOnlyField()
    progress_percentage = serializers.ReadOnlyField()
    is_blocked_status = serializers.SerializerMethodField()

    class Meta:
        model = Todo
        fields = (
            # Basic info
            "id",
            "title",
            "description",
            "priority",
            "scheduled_date",
            "scheduled_time",
            "status",
            "source",
            # Atomic task fields
            "task_type",
            "timebox_minutes",
            "constraints",
            "definition_of_done",
            "progress_percentage",
            "deliverable_type",
            # Dependencies
            "blocked_by",
            "unlocks",
            "parent_task",
            # Let's Go flow
            "artifact_template",
            "lets_go_inputs",
            # Evidence
            "evidence_url",
            "external_url",
            "notes",
            # Status tracking
            "completed_at",
            "skipped_at",
            "skip_reason",
            # Computed fields
            "is_overdue",
            "days_overdue",
            "is_blocked_status",
            # Timestamps
            "created_at",
            "updated_at",
            # Notifications
            "reminder_time",  # For local notification scheduling
        )
        read_only_fields = (
            "created_at",
            "updated_at",
            "completed_at",
            "skipped_at",
            "is_overdue",
            "days_overdue",
            "progress_percentage",
            "is_blocked_status",
            "reminder_time",
        )

    def get_is_blocked_status(self, obj):
        """Check if task is currently blocked"""
        return obj.is_blocked()
