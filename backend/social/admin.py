"""
Admin Configuration for Social Models
"""

from django.contrib import admin
from .models import Follow, DirectMessage, BlockedUser


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    """Admin interface for Follow model"""
    list_display = ['follower', 'following', 'created_at']
    list_filter = ['created_at']
    search_fields = ['follower__email', 'following__email']
    readonly_fields = ['created_at']


@admin.register(DirectMessage)
class DirectMessageAdmin(admin.ModelAdmin):
    """Admin interface for DirectMessage model"""
    list_display = ['sender', 'recipient', 'content_preview', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['sender__email', 'recipient__email', 'content']
    readonly_fields = ['created_at', 'updated_at']

    def content_preview(self, obj):
        """Show preview of message content"""
        return obj.content[:50] + ('...' if len(obj.content) > 50 else '')
    content_preview.short_description = 'Message'


@admin.register(BlockedUser)
class BlockedUserAdmin(admin.ModelAdmin):
    """Admin interface for BlockedUser model"""
    list_display = ['blocker', 'blocked', 'reason', 'created_at']
    list_filter = ['created_at']
    search_fields = ['blocker__email', 'blocked__email', 'reason']
    readonly_fields = ['created_at']
