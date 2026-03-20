from django.contrib import admin
from .models import CheckInEvent, OpportunityEvent


@admin.register(CheckInEvent)
class CheckInEventAdmin(admin.ModelAdmin):
    list_display = ['user', 'date', 'created_at']
    search_fields = ['user__email']
    list_filter = ['date']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'date'


@admin.register(OpportunityEvent)
class OpportunityEventAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'date_occurred', 'ai_impact_assessment', 'requires_vision_change', 'user_action']
    search_fields = ['user__email', 'title']
    list_filter = ['ai_impact_assessment', 'requires_vision_change', 'user_action', 'date_occurred']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'date_occurred'
