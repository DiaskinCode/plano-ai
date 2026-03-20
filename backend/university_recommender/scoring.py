"""
Three-score system for university recommendations.

This module implements:
- Fit Score: How well university matches preferences (0-100)
- Chance Score: How likely admission is (0-100)
- Finance Score: How feasible paying is (0-100)
"""

from .models import UniversityShortlist


def score_universities(filtered_universities, profile):
    """
    Produces THREE independent scores per university.

    Args:
        filtered_universities: QuerySet of University objects
        profile: UniversitySeekerProfile instance

    Returns:
        List of dicts with scores for each university
    """
    results = []

    for university in filtered_universities:
        # 1. Fit Score (0-100) - How well does this university match preferences?
        fit_score = calculate_fit_score(university, profile)

        # 2. Chance Score (0-100) - How likely is admission?
        chance_score = calculate_chance_score(university, profile)

        # 3. Finance Score (0-100) - How feasible is paying for this?
        finance_score = calculate_finance_score(university, profile)

        # Final ranking score = fit + finance (NOT chance)
        # Chance is used for bucket assignment only
        final_rank_score = (fit_score * 0.6) + (finance_score * 0.4)

        results.append({
            'university': university,
            'fit_score': round(fit_score, 2),
            'chance_score': round(chance_score, 2),
            'finance_score': round(finance_score, 2),
            'final_rank_score': round(final_rank_score, 2),
        })

    return results


def calculate_fit_score(university, profile):
    """
    How well does this university match student's preferences?

    FIXED: Removed SAT from fit (it's in chance score only)
    Factors: Academic programs, campus culture, opportunities, location

    Returns:
        float: Fit score (0-100)
    """
    score = 0.0

    # A. Academic Program Alignment (40 points)
    # FIXED: Use normalized major matching (case-insensitive, token-based)
    if profile.intended_major_1:
        major_norm = profile.intended_major_1.lower().strip()

        # Check against normalized majors
        if university.all_majors_normalized:
            if any(major_norm in m.lower() for m in university.all_majors_normalized):
                score += 20
        if university.strength_programs_normalized:
            if any(major_norm in m.lower() for m in university.strength_programs_normalized):
                score += 20  # Bonus for being in top programs

    # B. Campus Preferences (30 points)
    if profile.preferred_size:
        size_match = {
            'small': university.undergraduate_enrollment < 5000,
            'medium': 5000 <= university.undergraduate_enrollment <= 15000,
            'large': university.undergraduate_enrollment > 15000,
        }
        if size_match.get(profile.preferred_size):
            score += 15

    if profile.preferred_location:
        if profile.preferred_location.lower() in university.campus_type.lower():
            score += 15

    # C. Opportunity Alignment (30 points)
    if university.co_op_programs:
        score += 10
    if university.research_intensity in ['very_high', 'high']:
        score += 10
    if university.employed_within_6_months and university.employed_within_6_months >= 85:
        score += 10

    return min(score, 100)


def calculate_chance_score(university, profile):
    """
    How likely is admission?

    FIXED: Multi-factor, not just acceptance_rate
    Factors: Academic strength, test scores, rigor, spike vs selectivity

    Returns:
        float: Chance score (0-100)
    """
    # A. Academic Index (0-100)
    # FIXED: Proper GPA scale handling for CharField
    gpa_scale_map = {'4.0': 4.0, '5.0': 5.0, '100': 100.0}
    scale = gpa_scale_map.get(profile.gpa_scale, 4.0)

    # Normalize GPA to 0-100
    gpa_normalized = (profile.gpa / scale) * 100

    # Normalize SAT (max 1600)
    sat_normalized = (profile.sat_score / 1600) * 100 if profile.sat_score else gpa_normalized

    # Take better of GPA or SAT
    academic_index = max(gpa_normalized, sat_normalized)

    # B. Rigor Bonus (0-10 points)
    rigor_bonus = 0
    if profile.course_rigor == 'ap_ib_ib_plus':
        rigor_bonus = 10
    elif profile.course_rigor == 'ap_ib':
        rigor_bonus = 7
    elif profile.course_rigor == 'honors':
        rigor_bonus = 4
    academic_index += rigor_bonus

    # C. Spike Bonus (0-15 points)
    # FIXED: Spike significantly boosts chances
    if profile.spike_area and profile.spike_achievement:
        spike_boost = {
            'research_olympiad': 15,  # IMO, IPhO, etc.
            'athletics': 12,  # Recruited athlete level
            'arts': 10,  # National-level recognition
            'leadership': 8,  # Significant achievements
        }
        academic_index += spike_boost.get(profile.spike_area, 5)

    # D. Selectivity Index (0-100, higher = more selective)
    # Use acceptance rate as baseline (inverted)
    selectivity_index = 100 - university.acceptance_rate

    # E. Chance Score - FIXED: Piecewise instead of "pretty" formula
    diff = academic_index - selectivity_index

    if diff > 30:
        # Academic strength far exceeds selectivity = Safety
        chance_score = min(100, 75 + diff // 2)
    elif diff > 10:
        # Academic strength above selectivity = Match
        chance_score = 50 + diff
    elif diff > -10:
        # Academic strength near selectivity = Match/Reach border
        chance_score = 40 + diff
    elif diff > -30:
        # Academic strength below selectivity = Reach
        chance_score = 30 + diff
    else:
        # Academic strength far below selectivity = Very High Reach
        chance_score = max(0, 10 + diff // 2)

    return max(0, min(chance_score, 100))


def calculate_finance_score(university, profile):
    """
    How feasible is paying for this university?

    FIXED: Added international student check + need_blind_preference + merit_aid_required

    Returns:
        float: Finance score (0-100)
    """
    if not profile.max_budget or profile.financial_need == 'none':
        return 100  # No budget constraints = full score

    score = 0.0

    # A. Direct Budget Fit (40 points)
    if university.total_cost_per_year <= profile.max_budget:
        score += 40
    elif university.total_cost_per_year <= profile.max_budget * 1.2:
        score += 20

    # B. Aid Availability (60 points)
    # FIXED: Check if student is international (citizenship differs from country)
    is_international = profile.citizenship != profile.country

    if profile.financial_need == 'full_ride':
        if university.full_ride_available and university.aid_verified:
            score += 60
        elif university.need_blind and university.aid_verified:
            # FIXED: Check international_aid only for international students
            if is_international:
                if university.international_aid:
                    score += 50
                else:
                    score += 20  # Need-blind but no intl aid = lower score
            else:
                score += 55  # Domestic + need-blind = excellent
        elif university.need_based_aid and university.aid_verified:
            score += 35

        # FIXED: Apply need_blind_preference - boost score for need-blind schools
        if profile.need_blind_preference and university.need_blind and university.aid_verified:
            score += 10

    elif profile.financial_need == 'significant':
        if university.need_based_aid and university.aid_verified:
            # FIXED: Check international_aid for international students
            if is_international and not university.international_aid:
                score += 20  # Need-based but not for intl = low score
            else:
                score += 40
        elif university.merit_aid_offered and university.avg_merit_award:
            score += 35
        elif university.merit_aid_offered:
            score += 20  # Unverified

        # FIXED: Apply merit_aid_required - reduce score if no merit aid
        if profile.merit_aid_required and not university.merit_aid_offered:
            score = max(0, score - 20)

    return max(0, min(score, 100))


def assign_buckets(scored_universities):
    """
    Assigns Reach/Match/Safety based on CHANCE SCORE (not fit).

    FIXED: Based on Chance Score only
    """
    for item in scored_universities:
        chance_score = item['chance_score']

        if chance_score < 35:
            bucket = 'Reach'
        elif 35 <= chance_score <= 65:
            bucket = 'Match'
        else:
            bucket = 'Safety'

        item['bucket'] = bucket

    return scored_universities


def sort_final_recommendations(scored_universities):
    """
    Sorts universities: bucket first, then fit score within each bucket.

    FIXED: Order is Match -> Safety -> Reach (more user-friendly)
    """
    bucket_order = {'Match': 0, 'Safety': 1, 'Reach': 2}

    return sorted(
        scored_universities,
        key=lambda x: (
            bucket_order.get(x['bucket'], 3),
            -x['final_rank_score']  # Descending within bucket
        )
    )
