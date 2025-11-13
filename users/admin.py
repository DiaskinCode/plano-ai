from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserProfile


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'username', 'is_active', 'is_staff', 'created_at']
    search_fields = ['email', 'username']
    ordering = ['-created_at']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'name', 'age', 'coach_character', 'onboarding_completed', 'created_at']
    search_fields = ['user__email', 'name']
    list_filter = ['coach_character', 'onboarding_completed', 'energy_peak']
    readonly_fields = ['created_at', 'updated_at']
