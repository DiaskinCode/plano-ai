"""
Rule-based filtering for university recommendations.

This module implements deterministic filtering based on hard constraints
to eliminate impossible matches before scoring.
"""

from django.db.models import Q
from datetime import datetime, timedelta
from university_database.models import University


def filter_universities(profile):
    """
    Hard constraint filtering - eliminates impossible matches.

    Args:
        profile: UniversitySeekerProfile instance

    Returns:
        QuerySet: Filtered universities (typically returns 50-150 universities)
    """
    import logging
    logger = logging.getLogger(__name__)

    queryset = University.objects.all()
    logger.info(f"Initial university count: {queryset.count()}")

    # A. Geographic Constraints
    if profile.target_countries:
        queryset = queryset.filter(location_country__in=profile.target_countries)
        logger.info(f"After geographic filter: {queryset.count()}")

    # B. Test Requirements (FIXED - Logic Corrected)
    # If student has NO test and NOT flexible → exclude test-required schools
    has_sat = bool(profile.sat_score)
    has_act = bool(profile.act_score)
    has_tests = has_sat or has_act

    if not has_tests and not profile.test_optional_flexible:
        # No tests, not flexible → must be test-optional or test-not-required
        queryset = queryset.filter(
            Q(sat_optional=True) | Q(sat_required=False)
        )
        logger.info(f"After test filter: {queryset.count()}")
    # If student HAS tests → can apply anywhere (no filtering)

    # C. Financial Constraints - MADE LESS STRICT
    # Only filter for full-ride seekers with very specific budget
    if profile.max_budget and profile.financial_need == 'full_ride':
        queryset = queryset.filter(
            Q(total_cost_per_year__lte=profile.max_budget) |
            Q(full_ride_available=True)
        )
        logger.info(f"After financial filter: {queryset.count()}")

    # D. Academic Major Constraints - MADE OPTIONAL/SOFT
    # Only apply if we have enough universities to filter
    if profile.intended_major_1 and queryset.count() > 20:
        university_ids_with_major = []
        major_lower = profile.intended_major_1.lower()

        for uni in queryset:
            popular_majors = uni.popular_majors or []
            all_majors = uni.all_majors_normalized or []

            # More lenient matching - partial string match
            if any(major_lower in str(m).lower() for m in popular_majors) or \
               any(major_lower in str(m).lower() for m in all_majors):
                university_ids_with_major.append(uni.id)

        # Only apply if we get results, otherwise skip this filter
        if university_ids_with_major:
            queryset = queryset.filter(id__in=university_ids_with_major)
            logger.info(f"After major filter (major={profile.intended_major_1}): {queryset.count()}")
        else:
            logger.warning(f"Major filter returned no results for '{profile.intended_major_1}', skipping")

    # E. Deadline Constraints - SKIP for now (less critical)
    # if not profile.early_decision_willing and not profile.early_action_willing:
    #     deadline_threshold = datetime.now() + timedelta(days=60)
    #     queryset = queryset.filter(
    #         regular_decision_deadline__gt=deadline_threshold.date()
    #     )

    # F. Exclusions
    if profile.excluded_universities:
        queryset = queryset.exclude(
            short_name__in=profile.excluded_universities
        )

    logger.info(f"Final filtered count: {queryset.count()}")

    # If we have 0 universities, return all (fallback)
    if queryset.count() == 0:
        logger.warning("No universities matched criteria, returning all universities")
        return University.objects.all()

    return queryset
