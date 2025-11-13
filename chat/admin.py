from django.contrib import admin
from .models import ChatMessage, ChatSummary


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'content_preview', 'is_voice', 'created_at']
    search_fields = ['user__email', 'content']
    list_filter = ['role', 'is_voice', 'created_at']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'

    def content_preview(self, obj):
        return obj.content[:100]
    content_preview.short_description = 'Content Preview'


@admin.register(ChatSummary)
class ChatSummaryAdmin(admin.ModelAdmin):
    list_display = ['user', 'messages_start_id', 'messages_end_id', 'token_count', 'created_at']
    search_fields = ['user__email']
    readonly_fields = ['created_at', 'updated_at']
