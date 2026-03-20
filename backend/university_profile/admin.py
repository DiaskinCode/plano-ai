from django.contrib import admin
from .models import UniversitySeekerProfile, ExtracurricularActivity


@admin.register(UniversitySeekerProfile)
class UniversitySeekerProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'gpa', 'gpa_scale', 'intended_major_1', 'country', 'citizenship', 'completion_percentage', 'updated_at']
    search_fields = ['user__email', 'intended_major_1', 'country']
    list_filter = ['gpa_scale', 'course_rigor', 'financial_need', 'preferred_size', 'preferred_location', 'spike_area']
    readonly_fields = ['created_at', 'updated_at', 'completion_percentage']

    fieldsets = (
        ('Academic Profile', {
            'fields': ('gpa', 'gpa_scale', 'sat_score', 'act_score', 'course_rigor')
        }),
        ('Personal/Financial', {
            'fields': ('country', 'citizenship', 'max_budget', 'financial_need')
        }),
        ('Academic Interests', {
            'fields': ('intended_major_1', 'intended_major_2', 'intended_major_3', 'academic_interests')
        }),
        ('Campus Preferences', {
            'fields': ('preferred_size', 'preferred_location', 'preferred_region')
        }),
        ('Constraints', {
            'fields': ('target_countries', 'test_optional_flexible', 'early_decision_willing')
        }),
        ('Spike Factors', {
            'fields': ('spike_area', 'spike_achievement')
        }),
        ('Metadata', {
            'fields': ('user', 'created_at', 'updated_at', 'completion_percentage')
        }),
    )


@admin.register(ExtracurricularActivity)
class ExtracurricularActivityAdmin(admin.ModelAdmin):
    list_display = ['profile', 'title', 'category', 'role', 'impact_level', 'leadership_position', 'hours_per_week', 'years_participated']
    search_fields = ['profile__user__email', 'title', 'category']
    list_filter = ['category', 'impact_level', 'leadership_position', 'achievements_impact']
    readonly_fields = ['created_at', 'updated_at']
