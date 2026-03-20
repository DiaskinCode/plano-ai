"""
Admission Plan Enhancer - LLM-Powered Personalization

Generates personalized tasks and alternative paths based on user's additional_context,
shortlist, and eligibility report.

Features:
- 5-8 personalized tasks (portfolio, research, essays highlighting achievements)
- 2-3 alternative paths (e.g., "Take SAT for US" vs "Focus on China universities")
- Cost optimization via caching (target: 80% hit rate)
- Graceful fallback if LLM fails

Cost: ~$0.002-0.005 per user (uncached), $0.0004-0.001 (with cache)
"""

import hashlib
import json
import logging
from typing import Dict, List, Any
from django.core.cache import cache
from django.utils import timezone

from .llm_service import llm_service
from university_profile.models import UniversitySeekerProfile
from university_recommender.models import UniversityShortlist
from requirements.models import RequirementInstance

logger = logging.getLogger(__name__)


class AdmissionPlanEnhancer:
    """
    Enhances admission plans with LLM-generated personalized tasks
    and alternative path suggestions.
    """

    def __init__(self, user):
        """
        Initialize enhancer for a specific user.

        Args:
            user: User instance
        """
        self.user = user

    def enhance_plan(
        self,
        shortlist,
        eligibility_report: Dict,
        requirement_instances
    ) -> Dict[str, Any]:
        """
        Generate personalized enhancement to base admission plan.

        Args:
            shortlist: QuerySet of UniversityShortlist items
            eligibility_report: Dict with eligibility status and gaps
            requirement_instances: QuerySet of RequirementInstance

        Returns:
            {
                'personalized_tasks': List[Dict],  # 5-8 LLM-generated tasks
                'alternative_paths': List[Dict],   # 2-3 alternative paths
                'cost': Decimal,                   # LLM generation cost
                'cache_hit': bool,                 # Whether result was cached
                'generation_time': float           # Seconds
            }
        """
        start_time = timezone.now()

        # Check cache first
        cache_key = self._build_cache_key(shortlist, eligibility_report)
        cached = cache.get(cache_key)

        if cached:
            logger.info(f"[AdmissionPlanEnhancer] Cache hit for user {self.user.id}")
            cached['cache_hit'] = True
            return cached

        logger.info(f"[AdmissionPlanEnhancer] Cache miss - generating with LLM for user {self.user.id}")

        # Get user profile
        try:
            profile = UniversitySeekerProfile.objects.get(user=self.user)
        except UniversitySeekerProfile.DoesNotExist:
            logger.error(f"[AdmissionPlanEnhancer] No profile found for user {self.user.id}")
            return self._empty_response()

        # Build comprehensive prompt
        prompt = self._build_prompt(profile, shortlist, eligibility_report, requirement_instances)

        # Generate with LLM
        try:
            result = llm_service.generate(
                prompt=prompt,
                max_tokens=2500,  # Enough for 5-8 tasks + 2-3 paths
                temperature=0.7   # Creative but structured
            )

            # Track cost
            llm_service.track_cost(
                user=self.user,
                cost=result['cost'],
                operation='admission_plan_enhancement'
            )

            generation_time = (timezone.now() - start_time).total_seconds()
            logger.info(
                f"[AdmissionPlanEnhancer] LLM generated in {generation_time:.2f}s, "
                f"cost: ${result['cost']:.4f}"
            )

            # Parse response
            enhancement = self._parse_llm_response(result['text'])

            # Add metadata
            enhancement['cost'] = result['cost']
            enhancement['cache_hit'] = False
            enhancement['generation_time'] = generation_time

            # Cache results (24 hours)
            cache.set(cache_key, enhancement, timeout=86400)

            return enhancement

        except Exception as e:
            logger.error(f"[AdmissionPlanEnhancer] LLM generation failed: {e}")
            return self._empty_response()

    def _build_cache_key(self, shortlist, eligibility_report: Dict) -> str:
        """
        Build cache key from profile + universities + eligibility gaps.

        Key components:
        - User ID
        - University IDs in shortlist
        - Critical gaps from eligibility report

        Returns:
            str: Cache key (MD5 hash)
        """
        # Get university IDs
        university_ids = sorted([str(s.university.id) for s in shortlist])

        # Get critical gaps
        critical_gaps = eligibility_report.get('critical_gaps', [])
        gap_keys = sorted([gap.get('gap', '') for gap in critical_gaps])

        # Build key string
        key_data = f"{self.user.id}:{','.join(university_ids)}:{','.join(gap_keys)}"

        # Hash for shorter key
        return f"plan_enhance:{hashlib.md5(key_data.encode()).hexdigest()}"

    def _build_prompt(
        self,
        profile: UniversitySeekerProfile,
        shortlist,
        eligibility_report: Dict,
        requirement_instances
    ) -> str:
        """
        Build comprehensive LLM prompt.

        Structure:
        1. Role - Expert admission advisor
        2. User Profile - GPA, tests, majors, additional_context
        3. Shortlist - Target universities with requirements
        4. Eligibility - Gaps and blockers
        5. Requirements - What's satisfied vs missing
        6. Output Format - Structured JSON with tasks and paths
        """
        # Format shortlist
        shortlist_text = self._format_shortlist(shortlist)

        # Format eligibility
        eligibility_text = self._format_eligibility(eligibility_report)

        # Format requirements
        requirements_text = self._format_requirements(requirement_instances)

        prompt = f"""You are an expert college admission advisor with 20 years of experience helping students get into top universities worldwide.

USER PROFILE:
=============
Name: {self.user.username}
Email: {self.user.email}

Academics:
- GPA: {profile.gpa} ({profile.gpa_scale} scale)
- Education System: {profile.education_system or 'Not specified'}
- Current Grade: {profile.current_grade_level or 'Not specified'}
- Course Rigor: {profile.course_rigor or 'Not specified'}

Test Scores:
- IELTS: {profile.ielts_score or 'Not taken'} {f'(Type: {profile.ielts_type}, Date: {profile.ielts_date})' if profile.ielts_score else ''}
- TOEFL: {profile.toefl_score or 'Not taken'}
- SAT: {profile.sat_score or 'Not taken'} {f'(English: {profile.sat_english}, Math: {profile.sat_math})' if profile.sat_score else ''}
- ACT: {profile.act_score or 'Not taken'}
- Duolingo: {profile.duolingo_score or 'Not taken'}

Academic Interests:
- Primary Major: {profile.intended_major_1}
- Secondary Major: {profile.intended_major_2 or 'None'}
- Academic Interests: {profile.academic_interests or 'None provided'}

Activities & Achievements:
- Academic Competitions: {profile.academic_competitions or 'None'}
- Spike Area: {profile.spike_area or 'None identified'}
- Spike Achievement: {profile.spike_achievement or 'None'}

Background:
- Country: {profile.country}
- Citizenship: {profile.citizenship}
- Financial Need: {profile.financial_need}

Additional Context (USER'S STORY):
================================
{profile.additional_context or 'No additional context provided'}

SHORTLIST ({len(shortlist)} universities):
=====================================
{shortlist_text}

ELIGIBILITY STATUS:
===================
{eligibility_text}

REQUIREMENT STATUS:
===================
{requirements_text}

TASK: Generate personalized enhancement for this student's admission plan.
==============================================================================

Generate TWO types of content:

1. PERSONALIZED TASKS (5-8 tasks):
   - Build on their achievements mentioned in additional_context
   - Address specific gaps (e.g., portfolio, research experience, test prep)
   - Be actionable with time estimates
   - Should feel tailored to THEIR story, not generic advice
   - Categories: 'Portfolio', 'Research', 'Essays', 'Test Prep', 'Applications', 'Other'

2. ALTERNATIVE PATHS (2-3 options):
   - Address blockers (e.g., "No SAT? Consider China universities that don't require it")
   - Offer realistic options based on their profile
   - Include pros and cons of each path
   - Help them make strategic decisions

Return STRICT JSON format (no markdown, no code blocks):
{{
    "personalized_tasks": [
        {{
            "title": "Short actionable task title",
            "description": "Detailed description of what to do (2-3 sentences)",
            "category": "Portfolio|Research|Essays|Test Prep|Applications|Other",
            "priority": "high|medium|low",
            "estimated_hours": 10
        }}
    ],
    "alternative_paths": [
        {{
            "title": "Path name (e.g., 'Take SAT for US Universities')",
            "description": "Detailed explanation of this path (2-3 sentences)",
            "pros": ["Pro 1", "Pro 2"],
            "cons": ["Con 1", "Con 2"]
        }}
    ]
}}

CRITICAL: Return ONLY valid JSON. No explanation text, no markdown formatting.
"""
        return prompt

    def _format_shortlist(self, shortlist) -> str:
        """Format shortlist for prompt."""
        lines = []
        for item in shortlist:
            uni = item.university
            lines.append(f"- {uni.name} ({uni.location_country})")
            lines.append(f"  Status: {item.status}")
            if uni.sat_required:
                sat_25 = uni.sat_25th or 'N/A'
                sat_75 = uni.sat_75th or 'N/A'
                lines.append(f"  SAT range: {sat_25}-{sat_75}")
            if uni.min_ielts_score:
                lines.append(f"  Requires: IELTS {uni.min_ielts_score}+")
        return "\n".join(lines)

    def _format_eligibility(self, eligibility_report: Dict) -> str:
        """Format eligibility report for prompt."""
        status = eligibility_report.get('overall_status', 'Unknown')
        critical_gaps = eligibility_report.get('critical_gaps', [])

        lines = [f"Overall Status: {status}"]

        if critical_gaps:
            lines.append("\nCritical Gaps:")
            for gap in critical_gaps[:5]:  # Limit to 5 gaps
                lines.append(f"- {gap.get('gap', 'Unknown')}")
                if gap.get('solution'):
                    lines.append(f"  Solution: {gap['solution']}")
        else:
            lines.append("No critical gaps - student is eligible!")

        return "\n".join(lines)

    def _format_requirements(self, requirement_instances) -> str:
        """Format requirement instances for prompt."""
        # Group by status
        satisfied = []
        missing = []
        not_required = []

        for instance in requirement_instances[:20]:  # Limit to 20
            status_text = f"- {instance.requirement_key}: {instance.status}"
            if instance.university:
                status_text += f" ({instance.university.short_name})"
            if instance.notes:
                status_text += f" - {instance.notes}"

            if instance.status == 'satisfied':
                satisfied.append(status_text)
            elif instance.status == 'missing':
                missing.append(status_text)
            elif instance.status == 'not_required':
                not_required.append(status_text)

        lines = []

        if satisfied:
            lines.append("✅ Satisfied Requirements:")
            lines.extend(satisfied[:5])  # Limit display

        if missing:
            lines.append("\n❌ Missing Requirements:")
            lines.extend(missing[:5])

        if not_required:
            lines.append("\n⚪ Not Required:")
            lines.extend(not_required[:3])

        return "\n".join(lines)

    def _parse_llm_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse LLM JSON response.

        Args:
            response_text: Raw text from LLM

        Returns:
            Dict with personalized_tasks and alternative_paths
        """
        try:
            # Try to extract JSON from response
            # LLM might wrap in markdown code blocks
            text = response_text.strip()

            # Remove markdown code blocks if present
            if text.startswith('```'):
                # Find the first ``` and last ```
                first = text.find('```')
                last = text.rfind('```')
                if last > first:
                    text = text[first+3:last]
                    # Remove language identifier if present (e.g., "json")
                    text = text.strip()
                    if text.startswith('json'):
                        text = text[4:].strip()

            # Parse JSON
            data = json.loads(text)

            # Validate structure
            if 'personalized_tasks' not in data or 'alternative_paths' not in data:
                logger.error(f"[AdmissionPlanEnhancer] Invalid response structure: {data.keys()}")
                return self._empty_response()

            # Ensure lists
            data['personalized_tasks'] = data.get('personalized_tasks', [])
            data['alternative_paths'] = data.get('alternative_paths', [])

            logger.info(
                f"[AdmissionPlanEnhancer] Parsed response: "
                f"{len(data['personalized_tasks'])} tasks, "
                f"{len(data['alternative_paths'])} paths"
            )

            return data

        except json.JSONDecodeError as e:
            logger.error(f"[AdmissionPlanEnhancer] JSON parsing failed: {e}")
            logger.error(f"[AdmissionPlanEnhancer] Response text: {response_text[:500]}")
            return self._empty_response()

        except Exception as e:
            logger.error(f"[AdmissionPlanEnhancer] Response parsing failed: {e}")
            return self._empty_response()

    def _empty_response(self) -> Dict[str, Any]:
        """Return empty enhancement when LLM fails."""
        return {
            'personalized_tasks': [],
            'alternative_paths': [],
            'cost': 0,
            'cache_hit': False,
            'generation_time': 0,
            'error': 'LLM generation failed'
        }


# Convenience function
def enhance_admission_plan(user, shortlist, eligibility_report, requirement_instances) -> Dict:
    """
    Enhance admission plan with LLM-generated personalization.

    Args:
        user: User instance
        shortlist: QuerySet of UniversityShortlist
        eligibility_report: Dict with eligibility status
        requirement_instances: QuerySet of RequirementInstance

    Returns:
        Dict with personalized_tasks and alternative_paths
    """
    enhancer = AdmissionPlanEnhancer(user)
    return enhancer.enhance_plan(shortlist, eligibility_report, requirement_instances)
