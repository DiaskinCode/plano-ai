"""
Analytics and metrics for university recommendation system.

This module provides functions to calculate:
- Recommendation quality metrics
- Bucket distribution
- LLM confidence distribution
- User engagement metrics
"""

from django.db.models import Q, Count, Avg
from django.utils import timezone
from datetime import timedelta
from .models import RecommendationLog, RecommendationItem, RecommendationFeedback


def calculate_recommendation_quality(days=30):
    """
    Core metric: % of recommended universities that get shortlisted.

    Args:
        days: Number of days to look back (default: 30)

    Returns:
        float: Percentage of shortlisted recommendations (0-100)
    """
    cutoff = timezone.now() - timedelta(days=days)

    # Total recommendations shown
    total_shown = RecommendationItem.objects.filter(
        log__timestamp__gte=cutoff
    ).count()

    # Total shortlisted
    total_shortlisted = RecommendationFeedback.objects.filter(
        item__log__timestamp__gte=cutoff,
        action='shortlisted'
    ).count()

    if total_shown == 0:
        return 0

    return (total_shortlisted / total_shown) * 100


def calculate_bucket_distribution(days=30):
    """
    Distribution of buckets across recommendations.

    Args:
        days: Number of days to look back (default: 30)

    Returns:
        QuerySet: Bucket counts
    """
    cutoff = timezone.now() - timedelta(days=days)

    return RecommendationItem.objects.filter(
        log__timestamp__gte=cutoff
    ).values('bucket').annotate(
        count=Count('id')
    ).order_by('bucket')


def calculate_llm_confidence_distribution(days=30):
    """
    Distribution of LLM confidence levels.

    Args:
        days: Number of days to look back (default: 30)

    Returns:
        QuerySet: LLM confidence counts
    """
    cutoff = timezone.now() - timedelta(days=days)

    return RecommendationItem.objects.filter(
        log__timestamp__gte=cutoff,
        llm_confidence__isnull=False
    ).values('llm_confidence').annotate(
        count=Count('id')
    ).order_by('llm_confidence')


def calculate_average_scores_by_bucket(days=30):
    """
    Average fit, chance, and finance scores by bucket.

    Args:
        days: Number of days to look back (default: 30)

    Returns:
        list: Dict with bucket names and average scores
    """
    cutoff = timezone.now() - timedelta(days=days)

    return RecommendationItem.objects.filter(
        log__timestamp__gte=cutoff
    ).values('bucket').annotate(
        avg_fit_score=Avg('fit_score'),
        avg_chance_score=Avg('chance_score'),
        avg_finance_score=Avg('finance_score'),
        count=Count('id')
    ).order_by('bucket')


def calculate_most_shortlisted_universities(days=30, limit=10):
    """
    Most shortlisted universities.

    Args:
        days: Number of days to look back (default: 30)
        limit: Maximum number of results (default: 10)

    Returns:
        list: Top shortlisted universities
    """
    cutoff = timezone.now() - timedelta(days=days)

    return RecommendationItem.objects.filter(
        log__timestamp__gte=cutoff,
        feedback__action='shortlisted'
    ).values('university__short_name', 'university__name').annotate(
        shortlist_count=Count('id')
    ).order_by('-shortlist_count')[:limit]


def calculate_user_engagement_metrics(days=30):
    """
    User engagement metrics.

    Args:
        days: Number of days to look back (default: 30)

    Returns:
        dict: Engagement metrics
    """
    cutoff = timezone.now() - timedelta(days=days)

    # Number of unique users who got recommendations
    unique_users = RecommendationLog.objects.filter(
        timestamp__gte=cutoff
    ).values('user').distinct().count()

    # Average recommendations per user
    total_recommendations = RecommendationLog.objects.filter(
        timestamp__gte=cutoff
    ).aggregate(avg=Avg('total_recommendations'))['avg'] or 0

    # Percentage of users who provided feedback
    users_with_feedback = RecommendationLog.objects.filter(
        timestamp__gte=cutoff,
        items__feedback__isnull=False
    ).values('user').distinct().count()

    feedback_rate = (users_with_feedback / unique_users * 100) if unique_users > 0 else 0

    # Average shortlist size
    from .models import UniversityShortlist
    avg_shortlist_size = UniversityShortlist.objects.filter(
        user__recommendation_logs__timestamp__gte=cutoff
    ).values('user').annotate(
        count=Count('id')
    ).aggregate(avg=Avg('count'))['avg'] or 0

    return {
        'unique_users': unique_users,
        'avg_recommendations_per_user': round(total_recommendations, 2),
        'feedback_rate': round(feedback_rate, 2),
        'avg_shortlist_size': round(avg_shortlist_size, 2),
    }


def get_recommendation_analytics(days=30):
    """
    Get comprehensive recommendation analytics.

    Args:
        days: Number of days to look back (default: 30)

    Returns:
        dict: Comprehensive analytics
    """
    return {
        'quality': {
            'shortlist_rate': calculate_recommendation_quality(days),
        },
        'buckets': list(calculate_bucket_distribution(days)),
        'llm_confidence': list(calculate_llm_confidence_distribution(days)),
        'scores_by_bucket': list(calculate_average_scores_by_bucket(days)),
        'top_universities': list(calculate_most_shortlisted_universities(days)),
        'engagement': calculate_user_engagement_metrics(days),
    }
