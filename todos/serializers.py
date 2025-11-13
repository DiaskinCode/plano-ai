from rest_framework import serializers
from .models import Todo
from .artifact_models import TaskArtifact, TaskEvidence, TaskRun
from django.utils import timezone


class TaskArtifactSerializer(serializers.ModelSerializer):
    """Serializer for task artifacts"""
    class Meta:
        model = TaskArtifact
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')


class TaskEvidenceSerializer(serializers.ModelSerializer):
    """Serializer for task evidence"""
    class Meta:
        model = TaskEvidence
        fields = '__all__'
        read_only_fields = ('uploaded_at', 'uploaded_by')


class TaskRunSerializer(serializers.ModelSerializer):
    """Serializer for task run sessions"""
    class Meta:
        model = TaskRun
        fields = '__all__'
        read_only_fields = ('started_at', 'completed_at')


class TodoSerializer(serializers.ModelSerializer):
    is_overdue = serializers.ReadOnlyField()
    days_overdue = serializers.ReadOnlyField()
    progress_percentage = serializers.ReadOnlyField()

    # Related objects
    artifacts = TaskArtifactSerializer(many=True, read_only=True)
    evidence = TaskEvidenceSerializer(many=True, read_only=True)
    runs = TaskRunSerializer(many=True, read_only=True)

    class Meta:
        model = Todo
        fields = '__all__'
        read_only_fields = (
            'user', 'created_at', 'updated_at',
            'is_overdue', 'days_overdue', 'progress_percentage',
            'artifacts', 'evidence', 'runs'
        )

    def update(self, instance, validated_data):
        # Auto-set completion timestamps
        if validated_data.get('status') == 'done' and not instance.completed_at:
            validated_data['completed_at'] = timezone.now()
            # Unlock dependent tasks
            instance.unlock_dependents()
        elif validated_data.get('status') == 'skipped' and not instance.skipped_at:
            validated_data['skipped_at'] = timezone.now()

        # Update progress if DoD changed
        if 'definition_of_done' in validated_data:
            instance = super().update(instance, validated_data)
            instance.update_progress()
            return instance

        return super().update(instance, validated_data)


class TodoCreateSerializer(serializers.ModelSerializer):
    """Serializer for user-created todos (simplified for manual entry)"""
    class Meta:
        model = Todo
        fields = (
            'title', 'description', 'priority', 'scheduled_date', 'scheduled_time',
            'task_type', 'timebox_minutes', 'deliverable_type',
            'constraints', 'definition_of_done'
        )

    def create(self, validated_data):
        validated_data['source'] = 'user_added'
        validated_data['user'] = self.context['request'].user

        # Set default status
        if 'status' not in validated_data:
            validated_data['status'] = 'ready'

        # Generate idempotency key if not provided
        if 'idempotency_key' not in validated_data:
            user_id = self.context['request'].user.id
            date = validated_data.get('scheduled_date')
            title = validated_data.get('title', '')[:50]
            validated_data['idempotency_key'] = f"{user_id}_{date}_{title}"

        return super().create(validated_data)


class TodoListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing todos"""
    is_overdue = serializers.ReadOnlyField()

    class Meta:
        model = Todo
        fields = (
            'id', 'title', 'priority', 'scheduled_date', 'scheduled_time',
            'status', 'is_overdue', 'source',
            'task_type', 'timebox_minutes', 'deliverable_type',
            'progress_percentage', 'goalspec', 'energy_level'
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
            'id', 'title', 'description', 'priority',
            'scheduled_date', 'scheduled_time', 'status', 'source',

            # Atomic task fields
            'task_type', 'timebox_minutes', 'constraints',
            'definition_of_done', 'progress_percentage',
            'deliverable_type',

            # Dependencies
            'blocked_by', 'unlocks', 'parent_task',

            # Let's Go flow
            'artifact_template', 'lets_go_inputs',

            # Evidence
            'evidence_url', 'external_url', 'notes',

            # Status tracking
            'completed_at', 'skipped_at', 'skip_reason',

            # Computed fields
            'is_overdue', 'days_overdue', 'is_blocked_status',

            # Timestamps
            'created_at', 'updated_at'
        )
        read_only_fields = (
            'created_at', 'updated_at', 'completed_at', 'skipped_at',
            'is_overdue', 'days_overdue', 'progress_percentage', 'is_blocked_status'
        )

    def get_is_blocked_status(self, obj):
        """Check if task is currently blocked"""
        return obj.is_blocked()
