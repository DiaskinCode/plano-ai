from django.contrib import admin
from .models import (
    OnboardingState,
    SubscriptionPlan,
    UserSubscription,
    TargetUniversity,
    ExtracurricularActivity,
    OnboardingSnapshot,
)


@admin.register(OnboardingState)
class OnboardingStateAdmin(admin.ModelAdmin):
    list_display = ['user', 'current_step', 'selected_language', 'is_onboarding_complete', 'created_at']
    list_filter = ['current_step', 'selected_language', 'is_onboarding_complete']
    search_fields = ['user__email']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ['display_name', 'name', 'price_monthly', 'price_yearly', 'is_popular', 'is_active', 'order']
    list_filter = ['name', 'is_popular', 'is_active']
    search_fields = ['display_name', 'name']
    readonly_fields = []


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan', 'status', 'current_period_start', 'current_period_end', 'mentor_assigned']
    list_filter = ['status', 'plan']
    search_fields = ['user__email', 'stripe_subscription_id', 'stripe_customer_id']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(TargetUniversity)
class TargetUniversityAdmin(admin.ModelAdmin):
    list_display = ['user', 'university_name', 'category', 'country', 'major', 'is_ai_suggested', 'is_selected']
    list_filter = ['category', 'country', 'is_ai_suggested', 'is_selected']
    search_fields = ['user__email', 'university_name', 'major']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ExtracurricularActivity)
class ExtracurricularActivityAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'category', 'organization', 'role', 'is_ongoing', 'hours_per_week']
    list_filter = ['category', 'is_ongoing', 'leadership_role']
    search_fields = ['user__email', 'title', 'organization', 'role']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(OnboardingSnapshot)
class OnboardingSnapshotAdmin(admin.ModelAdmin):
    list_display = ['user', 'step', 'time_spent_seconds', 'created_at']
    list_filter = ['step']
    search_fields = ['user__email']
    readonly_fields = ['created_at']
