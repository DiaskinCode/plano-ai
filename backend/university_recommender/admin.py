from django.contrib import admin
from .models import RecommendationLog, RecommendationItem, RecommendationFeedback, UniversityShortlist


@admin.register(RecommendationLog)
class RecommendationLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'timestamp', 'total_recommendations', 'filter_count', 'llm_reranked']
    search_fields = ['user__email']
    list_filter = ['llm_reranked', 'timestamp']
    readonly_fields = ['timestamp']


@admin.register(RecommendationItem)
class RecommendationItemAdmin(admin.ModelAdmin):
    list_display = ['log', 'university', 'rank', 'bucket', 'fit_score', 'chance_score', 'finance_score', 'llm_confidence']
    search_fields = ['log__user__email', 'university__short_name', 'university__name']
    list_filter = ['bucket', 'llm_confidence', 'created_at']
    readonly_fields = ['created_at']


@admin.register(RecommendationFeedback)
class RecommendationFeedbackAdmin(admin.ModelAdmin):
    list_display = ['item', 'action', 'new_bucket', 'timestamp']
    search_fields = ['item__log__user__email', 'item__university__short_name']
    list_filter = ['action', 'timestamp']
    readonly_fields = ['timestamp']


@admin.register(UniversityShortlist)
class UniversityShortlistAdmin(admin.ModelAdmin):
    list_display = ['user', 'university', 'status', 'added_at']
    search_fields = ['user__email', 'university__short_name', 'university__name']
    list_filter = ['status', 'added_at']
    readonly_fields = ['added_at']
