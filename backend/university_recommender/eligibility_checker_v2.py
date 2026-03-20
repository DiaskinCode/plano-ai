"""
Eligibility Checker V2 - Deterministic, University-Specific Checks

This replaces the generic eligibility checker with deterministic rules that:
1. Check education years against university/foundation requirements
2. Check language scores with sub-score validation and expiry
3. Return structured EligibilityGap objects for task generation
4. Support both 'direct' and 'foundation' tracks
"""

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import List, Optional, Dict, Literal
from django.utils import timezone

from university_database.models import University, CountryRequirement
from university_profile.models import UniversitySeekerProfile


@dataclass
class EligibilityGap:
    """
    Represents a single eligibility gap that needs to be resolved.

    Attributes:
        gap_type: Type of gap (education_years, language, gpa, missing_data)
        severity: 'blocker' (cannot apply) or 'fixable' (can be resolved)
        title: Human-readable title
        description: Detailed explanation
        current_value: What user currently has
        required_value: What is required
        is_blocker: True if this prevents application
        alternative_path: Suggested alternative (e.g., foundation program)
        resolution_tasks: List of task titles to resolve this gap
        university_related: University this gap applies to (None if global)
    """
    gap_type: Literal['education_years', 'language', 'gpa', 'missing_data']
    severity: Literal['blocker', 'fixable']
    title: str
    description: str
    current_value: str
    required_value: str
    is_blocker: bool = True
    alternative_path: str = ""
    resolution_tasks: List[str] = field(default_factory=list)
    university_related: Optional[str] = None  # University short_name or None


@dataclass
class EligibilityResult:
    """
    Result of eligibility check for a university.

    Attributes:
        university_short_name: University identifier
        status: Overall eligibility status
        blockers: List of gaps that prevent application
        gaps: List of all gaps (blockers + fixable)
        can_apply_direct: Whether user can apply directly
        can_apply_foundation: Whether user can apply via foundation
        foundation_available: Whether foundation is an option at this uni
        track: The track used for this check ('direct' or 'foundation')
    """
    university_short_name: str
    status: Literal['eligible', 'partially_eligible', 'not_eligible']
    blockers: List[EligibilityGap] = field(default_factory=list)
    gaps: List[EligibilityGap] = field(default_factory=list)
    can_apply_direct: bool = True
    can_apply_foundation: bool = False
    foundation_available: bool = False
    track: Literal['direct', 'foundation'] = 'direct'


class EligibilityCheckerV2:
    """
    V2 Eligibility Checker - Deterministic, University-Specific

    Core Rules:
    1. Education Years: Check against uni min, then check foundation eligibility
    2. Language: Check total + sub-scores + validity date
    3. No blockers = Generate application tasks
    4. Blockers exist = Generate gap-closure tasks only
    """

    # Education system year mappings
    EDUCATION_YEARS = {
        '11_year': 11,
        '12_year': 12,
        'ib': 13,  # IB is considered 13-year equivalent
        'a_level': 13,  # A-Level is 13-year
        'ap': 12,
        'foundation': 13,  # Foundation completed = 13 years equivalent
        'other': None,  # Need manual check
    }

    def __init__(self, country_req_cache: Optional[Dict[str, CountryRequirement]] = None):
        """
        Args:
            country_req_cache: Optional dict {country: CountryRequirement} to avoid N+1 queries
        """
        self.country_req_cache = country_req_cache or {}

    def check_eligibility_for_university(
        self,
        profile: UniversitySeekerProfile,
        university: University,
        track: Literal['direct', 'foundation'] = 'direct'
    ) -> EligibilityResult:
        """
        Check eligibility for a single university.

        Args:
            profile: User's university seeker profile
            university: University to check against
            track: 'direct' or 'foundation' path

        Returns:
            EligibilityResult with blockers and gaps
        """
        gaps = []
        blockers = []

        # 1. Check for missing profile data
        missing_data = self._check_missing_profile_data(profile)
        if missing_data:
            gaps.extend(missing_data)
            blockers.extend([g for g in missing_data if g.is_blocker])

        # 2. Check education years
        education_gap = self._check_education_years(profile, university, track)
        if education_gap:
            gaps.append(education_gap)
            if education_gap.is_blocker:
                blockers.append(education_gap)

        # 3. Check language requirements
        language_gaps = self._check_language_requirements(profile, university)
        gaps.extend(language_gaps)
        blockers.extend([g for g in language_gaps if g.is_blocker])

        # Determine status
        if blockers:
            status = 'not_eligible'
            can_apply_direct = False
        elif gaps:
            status = 'partially_eligible'
            can_apply_direct = True
        else:
            status = 'eligible'
            can_apply_direct = True

        # Check foundation availability
        foundation_settings = university.get_foundation_settings(self.country_req_cache)
        can_apply_foundation = foundation_settings['available'] and track == 'foundation'

        return EligibilityResult(
            university_short_name=university.short_name,
            status=status,
            blockers=blockers,
            gaps=gaps,
            can_apply_direct=can_apply_direct,
            can_apply_foundation=can_apply_foundation,
            foundation_available=foundation_settings['available'],
            track=track
        )

    def check_eligibility_for_shortlist(
        self,
        profile: UniversitySeekerProfile,
        universities: List[University],
        track: Literal['direct', 'foundation'] = 'direct'
    ) -> Dict[str, EligibilityResult]:
        """
        Check eligibility for multiple universities.

        Returns:
            Dict mapping university short_name to EligibilityResult
        """
        results = {}
        for uni in universities:
            results[uni.short_name] = self.check_eligibility_for_university(
                profile, uni, track
            )
        return results

    def _check_missing_profile_data(
        self,
        profile: UniversitySeekerProfile
    ) -> List[EligibilityGap]:
        """
        Check for missing critical profile data.
        Returns gaps that prevent ANY task generation.
        """
        gaps = []

        # Check education system
        if not profile.education_system:
            gaps.append(EligibilityGap(
                gap_type='missing_data',
                severity='blocker',
                title='Education System Not Specified',
                description='Please specify your education system (11-year, 12-year, IB, A-Level, etc.)',
                current_value='Not specified',
                required_value='Education system (e.g., 12-year, IB)',
                is_blocker=True,
                resolution_tasks=['Complete Education System in Profile'],
                university_related=None
            ))

        # Check intended major
        if not profile.intended_major_1:
            gaps.append(EligibilityGap(
                gap_type='missing_data',
                severity='blocker',
                title='Intended Major Not Specified',
                description='Please specify your primary intended major',
                current_value='Not specified',
                required_value='Intended major',
                is_blocker=True,
                resolution_tasks=['Complete Intended Major in Profile'],
                university_related=None
            ))

        return gaps

    def _check_education_years(
        self,
        profile: UniversitySeekerProfile,
        university: University,
        track: Literal['direct', 'foundation']
    ) -> Optional[EligibilityGap]:
        """
        Check if education years meet requirements.

        IMPORTANT TRACK HANDLING:
        - Direct track: User years >= uni.min_years_of_education
        - Foundation track: User years >= foundation_min_years
        - When on foundation track AND user meets foundation req: Return None (SATISFIED, no gap!)
        - This prevents generating fake gaps for foundation-eligible users

        Returns:
            None: Requirement satisfied
            EligibilityGap: Requirement not met
        """
        if not profile.education_system:
            return None  # Already caught by missing data check

        user_years = self.EDUCATION_YEARS.get(profile.education_system)
        if user_years is None:
            # Treat 'other' as 12-year system (most common default)
            user_years = 12

        # FOUNDATION TRACK: Check foundation eligibility specifically
        if track == 'foundation':
            foundation_settings = university.get_foundation_settings(self.country_req_cache)

            # If foundation not available at all, user can't apply via foundation
            if not foundation_settings['available']:
                return EligibilityGap(
                    gap_type='education_years',
                    severity='blocker',
                    title='Foundation Not Available',
                    description=f'{university.name} does not offer a foundation program track',
                    current_value=f'{user_years}-year education',
                    required_value=f'Foundation track not available at {university.name}',
                    is_blocker=True,
                    alternative_path='Remove this university from shortlist or choose direct track',
                    resolution_tasks=[
                        'Remove this university from shortlist',
                        'Consider universities with foundation programs',
                    ],
                    university_related=university.short_name
                )

            # Check if user meets foundation minimum years
            foundation_min_years = foundation_settings.get('min_years')
            if foundation_min_years is None:
                # No specific minimum - assume same as standard requirement
                foundation_min_years = university.min_years_of_education or 12

            # CRITICAL: If user meets foundation requirements, return None (SATISFIED)
            # Do NOT create a fake gap - the track info is in EligibilityResult
            if user_years >= foundation_min_years:
                return None  # User is eligible for foundation track - NO GAP

            # Even foundation track requires more years than user has
            return EligibilityGap(
                gap_type='education_years',
                severity='blocker',
                title=f'Insufficient Education for Foundation ({user_years}-year vs {foundation_min_years}-year minimum)',
                description=f'{university.name} foundation program requires minimum {foundation_min_years} years of education. You have {user_years} years.',
                current_value=f'{user_years} years',
                required_value=f'At least {foundation_min_years} years for foundation eligibility',
                is_blocker=True,
                alternative_path='Consider universities accepting your education system',
                resolution_tasks=[
                    'Remove this university from shortlist',
                    'Consider universities in countries with 11-year system compatibility',
                ],
                university_related=university.short_name
            )

        # DIRECT TRACK: Standard direct admission check
        required_years = university.min_years_of_education or 12

        # User meets direct admission requirement
        if user_years >= required_years:
            return None  # Eligible - NO GAP

        # User doesn't meet direct requirement - check if foundation is alternative
        foundation_settings = university.get_foundation_settings(self.country_req_cache)

        if foundation_settings['available']:
            # Foundation is available as an alternative
            foundation_min_years = foundation_settings.get('min_years', 11)
            if user_years >= foundation_min_years:
                return EligibilityGap(
                    gap_type='education_years',
                    severity='blocker',
                    title=f'Education Years Mismatch ({user_years}-year vs {required_years}-year for direct admission)',
                    description=f'{university.name} requires {required_years} years for direct admission. You have {user_years} years.',
                    current_value=f'{user_years} years ({profile.education_system})',
                    required_value=f'{required_years} years for direct admission',
                    is_blocker=True,
                    alternative_path=f'Foundation Year Program available ({foundation_settings["duration"]} years)',
                    resolution_tasks=[
                        f'Complete Foundation Year Program for {university.name}',
                        f'Research Foundation Providers in {university.location_country}',
                        'Prepare Foundation Application Documents',
                    ],
                    university_related=university.short_name
                )

        # No foundation available or user doesn't qualify for foundation either
        return EligibilityGap(
            gap_type='education_years',
            severity='blocker',
            title=f'Insufficient Education Years ({user_years}-year vs {required_years}-year required)',
            description=f'{university.name} requires {required_years} years of education. You have {user_years} years.',
            current_value=f'{user_years} years ({profile.education_system})',
            required_value=f'{required_years} years',
            is_blocker=True,
            alternative_path='Consider universities accepting your education system',
            resolution_tasks=[
                'Remove this university from shortlist',
                'Consider universities in countries with 11-year system compatibility',
            ],
            university_related=university.short_name
        )

    def _check_language_requirements(
        self,
        profile: UniversitySeekerProfile,
        university: University
    ) -> List[EligibilityGap]:
        """
        Check language score requirements.

        Checks:
        1. Total score meets minimum
        2. Sub-scores meet minimums (if specified)
        3. Score is still valid (not expired)
        """
        gaps = []

        # Get requirements
        # Priority: University specific > Country default
        min_ielts = university.min_ielts_score
        min_reading = university.min_ielts_reading
        min_writing = university.min_ielts_writing
        min_listening = university.min_ielts_listening
        min_speaking = university.min_ielts_speaking
        validity_years = university.ielts_validity_years or 2

        # Fall back to country default if uni doesn't specify
        if min_ielts is None:
            country_req = self.country_req_cache.get(university.location_country)
            if country_req:
                min_ielts = country_req.default_min_ielts
            else:
                min_ielts = 6.5  # Global default

        # Check if user has IELTS
        user_ielts = profile.ielts_score
        if user_ielts is None:
            # No score - need to take test
            gaps.append(EligibilityGap(
                gap_type='language',
                severity='blocker',
                title='IELTS Score Required',
                description=f'{university.name} requires IELTS {min_ielts} for admission',
                current_value='No score',
                required_value=f'IELTS {min_ielts}',
                is_blocker=True,
                resolution_tasks=[
                    'Register for IELTS Exam',
                    'Complete IELTS Preparation',
                    'Take IELTS Exam',
                ],
                university_related=university.short_name
            ))
            return gaps

        # Check score validity
        ielts_date = profile.ielts_date
        if ielts_date:
            expiry_date = ielts_date + timedelta(days=validity_years * 365)
            if date.today() > expiry_date:
                gaps.append(EligibilityGap(
                    gap_type='language',
                    severity='blocker',
                    title='IELTS Score Expired',
                    description=f'Your IELTS score expired on {expiry_date}. Universities require scores from the last {validity_years} years.',
                    current_value=f'IELTS {user_ielts} (expired {expiry_date})',
                    required_value=f'Valid IELTS {min_ielts}',
                    is_blocker=True,
                    resolution_tasks=[
                        'Register for IELTS Exam',
                        'Retake IELTS Exam',
                    ],
                    university_related=university.short_name
                ))
                return gaps  # Invalid score, no point checking sub-scores

        # Check total score
        if user_ielts < min_ielts:
            gaps.append(EligibilityGap(
                gap_type='language',
                severity='blocker',
                title=f'IELTS Score Below Requirement ({user_ielts} vs {min_ielts})',
                description=f'{university.name} requires IELTS {min_ielts}. Your score: {user_ielts}',
                current_value=f'IELTS {user_ielts}',
                required_value=f'IELTS {min_ielts}',
                is_blocker=True,
                resolution_tasks=[
                    f'Improve IELTS score from {user_ielts} to {min_ielts}',
                    'Complete IELTS Preparation Course',
                    'Retake IELTS Exam',
                ],
                university_related=university.short_name
            ))
            # Total score too low - sub-scores won't matter
            return gaps

        # Check sub-scores
        sub_score_issues = []
        if min_reading and profile.ielts_reading_score and profile.ielts_reading_score < min_reading:
            sub_score_issues.append(f'Reading {profile.ielts_reading_score} < {min_reading}')
        if min_writing and profile.ielts_writing_score and profile.ielts_writing_score < min_writing:
            sub_score_issues.append(f'Writing {profile.ielts_writing_score} < {min_writing}')
        if min_listening and profile.ielts_listening_score and profile.ielts_listening_score < min_listening:
            sub_score_issues.append(f'Listening {profile.ielts_listening_score} < {min_listening}')
        if min_speaking and profile.ielts_speaking_score and profile.ielts_speaking_score < min_speaking:
            sub_score_issues.append(f'Speaking {profile.ielts_speaking_score} < {min_speaking}')

        if sub_score_issues:
            gaps.append(EligibilityGap(
                gap_type='language',
                severity='blocker',
                title='IELTS Sub-Scores Below Requirement',
                description=f'{university.name} requires minimum sub-scores. Issues: {", ".join(sub_score_issues)}',
                current_value=f'Total: {user_ielts}',
                required_value=f'Total: {min_ielts}, Sub-scores: {min_reading}/{min_writing}/{min_listening}/{min_speaking}',
                is_blocker=True,
                resolution_tasks=[
                    'Improve specific IELTS sub-scores',
                    'Focus preparation on weak areas',
                    'Retake IELTS Exam',
                ],
                university_related=university.short_name
            ))

        return gaps

    def _check_gpa_requirements(
        self,
        profile: UniversitySeekerProfile,
        university: University
    ) -> Optional[EligibilityGap]:
        """
        Check GPA requirements.
        Note: GPA is typically 'fixable' not a hard blocker like education years.
        """
        # Get min GPA from education_requirements
        edu_reqs = university.education_requirements or {}
        min_gpa = edu_reqs.get('min_gpa')

        if min_gpa is None:
            return None  # No specific requirement

        # Normalize user GPA to 4.0 scale
        user_gpa = profile.gpa
        if profile.gpa_scale == '5.0':
            user_gpa = (profile.gpa / 5.0) * 4.0
        elif profile.gpa_scale == '100':
            user_gpa = (profile.gpa / 100.0) * 4.0

        if user_gpa >= min_gpa:
            return None

        return EligibilityGap(
            gap_type='gpa',
            severity='fixable',  # GPA can sometimes be flexible
            title=f'GPA Below Recommendation (Your {profile.gpa} vs Recommended {min_gpa})',
            description=f'{university.name} recommends a GPA of {min_gpa}. Your GPA: {profile.gpa} ({profile.gpa_scale} scale)',
            current_value=f'GPA {profile.gpa} ({profile.gpa_scale} scale)',
            required_value=f'GPA {min_gpa} (4.0 scale)',
            is_blocker=False,  # GPA is rarely a hard blocker
            resolution_tasks=[
                'Consider test-optional application strategy',
                'Highlight other strengths in application',
            ],
            university_related=university.short_name
        )
