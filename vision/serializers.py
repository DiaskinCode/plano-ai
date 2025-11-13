from rest_framework import serializers
from .models import Scenario, Vision, Milestone
from todos.serializers import TodoListSerializer


class ScenarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scenario
        fields = '__all__'
        read_only_fields = ('user', 'created_at', 'updated_at')


class MilestoneSerializer(serializers.ModelSerializer):
    tasks = TodoListSerializer(many=True, read_only=True)
    task_count = serializers.SerializerMethodField()
    completed_tasks_count = serializers.SerializerMethodField()

    class Meta:
        model = Milestone
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

    def get_task_count(self, obj):
        return obj.tasks.count()

    def get_completed_tasks_count(self, obj):
        return obj.tasks.filter(status='done').count()


class VisionSerializer(serializers.ModelSerializer):
    milestones = MilestoneSerializer(many=True, read_only=True)
    scenario = ScenarioSerializer(read_only=True)

    class Meta:
        model = Vision
        fields = '__all__'
        read_only_fields = ('user', 'created_at', 'updated_at')


class VisionDetailSerializer(serializers.ModelSerializer):
    """Detailed vision serializer with all related data"""
    milestones = MilestoneSerializer(many=True, read_only=True)
    scenario = ScenarioSerializer(read_only=True)
    total_milestones = serializers.SerializerMethodField()
    completed_milestones = serializers.SerializerMethodField()

    class Meta:
        model = Vision
        fields = '__all__'
        read_only_fields = ('user', 'created_at', 'updated_at')

    def get_total_milestones(self, obj):
        return obj.milestones.count()

    def get_completed_milestones(self, obj):
        return obj.milestones.filter(is_completed=True).count()
