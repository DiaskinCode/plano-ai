"""
Django Admin configuration for Requirement Engine models
"""

from django.contrib import admin
from .models import (
    RequirementTemplate,
    RequirementRule,
    RequirementInstance,
    RequirementPack,
    DocumentVaultItem,
    RequirementSourceSnapshot,
)


@admin.register(RequirementTemplate)
class RequirementTemplateAdmin(admin.ModelAdmin):
    list_display = ['key', 'title', 'category', 'is_active', 'created_at']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['key', 'title', 'description']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('key', 'title', 'description', 'category', 'is_active')
        }),
        ('Defaults', {
            'fields': ('default_evidence_fields', 'default_link_url')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(RequirementRule)
class RequirementRuleAdmin(admin.ModelAdmin):
    list_display = ['template', 'scope', 'get_target', 'priority', 'is_active', 'created_at']
    list_filter = ['scope', 'priority', 'is_active', 'template__category']
    search_fields = ['template__key', 'template__title', 'country', 'university__name']
    readonly_fields = ['created_at', 'updated_at']

    def get_target(self, obj):
        if obj.university:
            return obj.university.name
        return obj.country or "Global"
    get_target.short_description = 'Target'

    fieldsets = (
        ('Rule Configuration', {
            'fields': ('template', 'scope', 'country', 'university')
        }),
        ('Conditions & Overrides', {
            'fields': ('conditions', 'overrides', 'link_url', 'priority')
        }),
        ('Status', {
            'fields': ('is_active', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(RequirementInstance)
class RequirementInstanceAdmin(admin.ModelAdmin):
    list_display = ['user_email', 'requirement_key', 'scope_level', 'get_scope_target', 'status', 'verification_level', 'created_at']
    list_filter = ['scope_level', 'status', 'verification_level', 'source_domain_type', 'created_at']
    search_fields = ['user__email', 'requirement_key', 'country', 'university__name']
    readonly_fields = ['created_at', 'updated_at', 'verified_at']

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User'

    def get_scope_target(self, obj):
        if obj.university:
            return obj.university.name
        if obj.country:
            return obj.country
        return "Global"
    get_scope_target.short_description = 'Scope Target'

    fieldsets = (
        ('User & Scope', {
            'fields': ('user', 'scope_level', 'university', 'country')
        }),
        ('Requirement', {
            'fields': ('requirement_key', 'status', 'verification_level', 'source')
        }),
        ('Academic Context', {
            'fields': ('track', 'intake', 'degree_level', 'citizenship'),
            'classes': ('collapse',)
        }),
        ('Evidence & Links', {
            'fields': ('evidence_fields', 'source_domain_type', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'verified_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(RequirementPack)
class RequirementPackAdmin(admin.ModelAdmin):
    list_display = ['name', 'pack_type', 'country', 'priority', 'is_active', 'created_at']
    list_filter = ['pack_type', 'is_active', 'country']
    search_fields = ['name', 'country']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Pack Information', {
            'fields': ('name', 'pack_type', 'country', 'priority', 'is_active')
        }),
        ('Pack Contents', {
            'fields': ('requirement_templates', 'conditions')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(DocumentVaultItem)
class DocumentVaultItemAdmin(admin.ModelAdmin):
    list_display = ['user_email', 'doc_type', 'file_name', 'is_verified', 'uploaded_at']
    list_filter = ['doc_type', 'is_verified', 'uploaded_at']
    search_fields = ['user__email', 'file_name', 'doc_type']
    readonly_fields = ['uploaded_at', 'verified_at']

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User'

    fieldsets = (
        ('Document Information', {
            'fields': ('user', 'doc_type', 'file_name', 'file_url', 'file_size')
        }),
        ('Verification', {
            'fields': ('is_verified', 'verified_at', 'verification_notes')
        }),
        ('Metadata', {
            'fields': ('metadata', 'uploaded_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(RequirementSourceSnapshot)
class RequirementSourceSnapshotAdmin(admin.ModelAdmin):
    list_display = ['requirement_key', 'link_url', 'updated_by', 'is_valid', 'fetched_at']
    list_filter = ['updated_by', 'is_valid', 'fetched_at']
    search_fields = ['requirement_instance__requirement_key', 'link_url']
    readonly_fields = ['fetched_at', 'requirement_instance']

    def requirement_key(self, obj):
        return obj.requirement_instance.requirement_key
    requirement_key.short_description = 'Requirement Key'

    fieldsets = (
        ('Snapshot Information', {
            'fields': ('requirement_instance', 'link_url', 'hash_excerpt')
        }),
        ('Metadata', {
            'fields': ('updated_by', 'is_valid', 'validation_notes', 'fetched_at')
        }),
    )
