from django.contrib import admin
from .models import Scenario, Vision, Milestone


@admin.register(Scenario)
class ScenarioAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'plan_type', 'is_selected', 'created_at']
    search_fields = ['user__email', 'title']
    list_filter = ['plan_type', 'is_selected']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Vision)
class VisionAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'horizon_start', 'horizon_end', 'progress_percentage', 'is_active']
    search_fields = ['user__email', 'title']
    list_filter = ['is_active', 'horizon_start']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Milestone)
class MilestoneAdmin(admin.ModelAdmin):
    list_display = ['vision', 'title', 'due_date', 'is_completed', 'completed_at']
    search_fields = ['vision__title', 'title']
    list_filter = ['is_completed', 'due_date']
    readonly_fields = ['created_at', 'updated_at']
