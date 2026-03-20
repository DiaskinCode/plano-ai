from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.contrib import messages

from .models import (
    MentorAvailabilityRule,
    MentorBooking,
    MentorProfile,
    MentorReviewRequest,
    MentorReviewResponse,
)


@admin.register(MentorProfile)
class MentorProfileAdmin(admin.ModelAdmin):
    """Enhanced admin interface for mentor profile management with verification workflow"""

    list_display = [
        "title",
        "user_email",
        "verification_status_badge",
        "is_active",
        "rating",
        "flag_count_badge",
        "verification_submitted_at",
    ]
    list_filter = [
        "verification_status",
        "is_active",
        "flag_count",
        "created_at",
    ]
    search_fields = ["title", "user__email", "bio", "education"]
    ordering = ["-verification_submitted_at"]
    readonly_fields = [
        "created_at",
        "verification_submitted_at",
        "verification_reviewed_at",
    ]

    actions = [
        "approve_mentors",
        "reject_mentors",
        "request_resubmission",
        "suspend_mentors",
        "reinstate_mentors",
    ]

    fieldsets = (
        ("Basic Information", {
            "fields": (
                "user",
                "title",
                "bio",
                "photo_url",
                "education"
            )
        }),
        ("Verification Status", {
            "fields": (
                "verification_status",
                "verification_video_url",
                "verification_submitted_at",
                "verification_reviewed_at",
                "verification_notes",
                "is_verified",
            ),
            "classes": ("verification",),
        }),
        ("Expertise & Business", {
            "fields": (
                "expertise_areas",
                "hourly_rate_credits",
                "timezone",
                "meeting_link"
            )
        }),
        ("Status & Flags", {
            "fields": (
                "is_active",
                "flag_count",
                "flagged_at"
            )
        }),
        ("Statistics", {
            "fields": (
                "rating",
                "total_sessions",
                "created_at"
            ),
            "classes": ("collapse",),
        }),
    )

    def user_email(self, obj):
        """Display user email"""
        return obj.user.email
    user_email.short_description = "Email"
    user_email.admin_order_field = "user__email"

    def verification_status_badge(self, obj):
        """Display colored badge for verification status"""
        colors = {
            'pending': 'orange',
            'approved': 'green',
            'rejected': 'red',
            'suspended': 'darkred'
        }
        icons = {
            'pending': '⏳',
            'approved': '✅',
            'rejected': '❌',
            'suspended': '⚠️'
        }
        color = colors.get(obj.verification_status, 'gray')
        icon = icons.get(obj.verification_status, '❓')
        status = obj.get_verification_status_display()
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}</span>',
            color,
            icon,
            status
        )
    verification_status_badge.short_description = "Verification"
    verification_status_badge.admin_order_field = "verification_status"

    def flag_count_badge(self, obj):
        """Display flag count with warning if high"""
        if obj.flag_count == 0:
            return mark_safe('<span style="color: green;">No flags</span>')
        elif obj.flag_count < 3:
            return format_html(
                '<span style="color: orange; font-weight: bold;">⚠️ {} flag(s)</span>',
                obj.flag_count
            )
        else:
            return format_html(
                '<span style="color: red; font-weight: bold;">🚨 {} flags</span>',
                obj.flag_count
            )
    flag_count_badge.short_description = "Flags"
    flag_count_badge.admin_order_field = "flag_count"

    # Admin Actions
    def approve_mentors(self, request, queryset):
        """Approve selected mentor applications"""
        updated = queryset.filter(
            verification_status__in=['pending', 'rejected']
        ).update(
            verification_status='approved',
            verification_reviewed_at=timezone.now(),
            is_verified=True,
            verification_notes=''
        )

        # Send approval emails (will be implemented in email service)
        for mentor in queryset.filter(verification_status='approved'):
            try:
                from .email_service import send_mentor_approval_email
                send_mentor_approval_email(mentor)
            except ImportError:
                # Email service not yet implemented
                pass

        self.message_user(
            request,
            f'{updated} mentor(s) approved successfully.',
            messages.SUCCESS
        )
    approve_mentors.short_description = "✅ Approve selected mentors"

    def reject_mentors(self, request, queryset):
        """Reject selected mentor applications (requires notes in bulk)"""
        count = queryset.filter(
            verification_status__in=['pending', 'approved']
        ).update(
            verification_status='rejected',
            verification_reviewed_at=timezone.now(),
            is_verified=False
        )

        self.message_user(
            request,
            f'{count} mentor(s) rejected. Please add rejection notes individually.',
            messages.WARNING
        )
    reject_mentors.short_description = "❌ Reject selected mentors"

    def request_resubmission(self, request, queryset):
        """Reset rejected mentors back to pending for resubmission"""
        updated = queryset.filter(
            verification_status='rejected'
        ).update(
            verification_status='pending',
            verification_notes='',
            is_verified=False
        )

        self.message_user(
            request,
            f'{updated} mentor(s) marked for resubmission.',
            messages.INFO
        )
    request_resubmission.short_description = "🔄 Request resubmission"

    def suspend_mentors(self, request, queryset):
        """Suspend selected mentors"""
        updated = queryset.filter(
            verification_status='approved'
        ).update(
            verification_status='suspended',
            is_active=False,
            is_verified=False
        )

        self.message_user(
            request,
            f'{updated} mentor(s) suspended.',
            messages.WARNING
        )
    suspend_mentors.short_description = "⚠️ Suspend selected mentors"

    def reinstate_mentors(self, request, queryset):
        """Reinstate suspended mentors"""
        updated = queryset.filter(
            verification_status='suspended'
        ).update(
            verification_status='approved',
            is_active=True,
            is_verified=True,
            flag_count=0,
            flagged_at=None,
            verification_notes=''
        )

        self.message_user(
            request,
            f'{updated} mentor(s) reinstated.',
            messages.SUCCESS
        )
    reinstate_mentors.short_description = "♻️ Reinstate selected mentors"


@admin.register(MentorAvailabilityRule)
class MentorAvailabilityRuleAdmin(admin.ModelAdmin):
    list_display = ["mentor", "day_of_week", "start_minute", "end_minute", "is_active"]
    list_filter = ["day_of_week", "is_active"]
    search_fields = ["mentor__title"]


@admin.register(MentorBooking)
class MentorBookingAdmin(admin.ModelAdmin):
    list_display = [
        "mentor",
        "student_email",
        "start_at_utc",
        "status",
        "duration_minutes",
        "is_flagged",
    ]
    list_filter = ["status", "topic", "is_flagged"]
    search_fields = ["mentor__title", "student__email"]
    readonly_fields = ["created_at", "confirmed_at", "completed_at", "flagged_at"]

    def student_email(self, obj):
        return obj.student.email
    student_email.short_description = "Student Email"


@admin.register(MentorReviewRequest)
class MentorReviewRequestAdmin(admin.ModelAdmin):
    list_display = ["mentor", "student_email", "request_type", "status", "created_at"]
    list_filter = ["request_type", "status"]
    search_fields = ["mentor__title", "student__email"]

    def student_email(self, obj):
        return obj.student.email
    student_email.short_description = "Student Email"


@admin.register(MentorReviewResponse)
class MentorReviewResponseAdmin(admin.ModelAdmin):
    list_display = ["request", "overall_comment", "created_at"]
    search_fields = ["overall_comment"]
