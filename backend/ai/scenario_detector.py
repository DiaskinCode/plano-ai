"""
Scenario Detector (Week 2 Day 1-2)

Detects whether a user's background + goal combination is covered by existing templates.

Coverage tiers:
- 80-100%: Well-covered (Founder→CS, Engineer→AI) → Use templates + enhancement
- 40-79%: Partially covered (Designer→HCI, Teacher→EdTech) → Mix templates + full LLM
- 0-39%: Uncovered (Nurse→Medical AI PhD, Lawyer→Bioethics) → Full LLM generation

Key insight from user feedback:
"Templates only cover ~20% of scenarios. We need LLM for the other 80%."
"""

from typing import Dict, Any, List, Tuple
import re


class ScenarioDetector:
    """
    Detects if user scenario is covered by templates.

    Week 2: Enables smart routing between templates and full LLM generation.
    """

    # Covered background types (have dedicated templates/custom generators)
    COVERED_BACKGROUNDS = {
        'founder': ['startup', 'entrepreneur', 'co-founder', 'founder', 'ceo', 'cto'],
        'engineer': ['engineer', 'developer', 'programmer', 'software', 'data scientist', 'ml engineer'],
        'researcher': ['research', 'phd', 'postdoc', 'research assistant', 'lab'],
        'student': ['student', 'undergraduate', 'bachelor', 'master'],
    }

    # Covered target fields (have templates)
    COVERED_FIELDS = [
        'computer science', 'cs', 'software engineering',
        'artificial intelligence', 'ai', 'machine learning', 'ml',
        'data science', 'business', 'mba', 'management',
    ]

    # Edge case combinations that are NOT well-covered
    EDGE_CASE_COMBINATIONS = [
        # (background_keyword, field_keyword, reason)
        ('designer', 'hci', 'Designer→HCI needs portfolio-focused tasks'),
        ('designer', 'human-computer interaction', 'Designer→HCI needs portfolio-focused tasks'),
        ('nurse', 'medical', 'Nurse→Medical AI needs healthcare context'),
        ('nurse', 'ai', 'Nurse→Medical AI needs healthcare context'),
        ('doctor', 'ai', 'Doctor→AI needs medical context'),
        ('teacher', 'edtech', 'Teacher→EdTech needs education context'),
        ('teacher', 'education', 'Teacher→EdTech needs education context'),
        ('lawyer', 'bioethics', 'Lawyer→Bioethics is rare interdisciplinary'),
        ('artist', 'creative', 'Artist→Creative Tech needs portfolio'),
        ('musician', 'music tech', 'Musician→Music Tech needs portfolio'),
    ]

    def __init__(self, context: Dict[str, Any]):
        """
        Initialize detector with user context.

        Args:
            context: Full personalization context from profile_extractor
        """
        self.context = context

    def detect_scenario_coverage(self) -> Dict[str, Any]:
        """
        Detect if user's scenario is covered by templates.

        Returns:
            {
                'coverage_score': 0-100 (percentage covered),
                'coverage_tier': 'well_covered' | 'partially_covered' | 'uncovered',
                'background_covered': True/False,
                'field_covered': True/False,
                'is_edge_case': True/False,
                'edge_case_reason': Optional[str],
                'recommendation': 'templates' | 'hybrid' | 'full_llm',
                'reasoning': str (explanation of coverage)
            }
        """
        # Extract key info
        background = self._extract_background()
        field = self.context.get('field', '').lower()

        # Check coverage
        background_covered, background_match = self._is_background_covered(background)
        field_covered = self._is_field_covered(field)
        is_edge_case, edge_reason = self._is_edge_case(background, field)

        # Calculate coverage score
        coverage_score = self._calculate_coverage_score(
            background_covered, field_covered, is_edge_case
        )

        # Determine tier
        if coverage_score >= 80:
            tier = 'well_covered'
            recommendation = 'templates'
        elif coverage_score >= 40:
            tier = 'partially_covered'
            recommendation = 'hybrid'
        else:
            tier = 'uncovered'
            recommendation = 'full_llm'

        # Build reasoning
        reasoning = self._build_reasoning(
            background, field, background_covered, field_covered,
            is_edge_case, edge_reason
        )

        result = {
            'coverage_score': coverage_score,
            'coverage_tier': tier,
            'background_covered': background_covered,
            'background_match': background_match,
            'field_covered': field_covered,
            'is_edge_case': is_edge_case,
            'edge_case_reason': edge_reason,
            'recommendation': recommendation,
            'reasoning': reasoning
        }

        return result

    def _extract_background(self) -> str:
        """Extract user's background type from context."""
        # Check flags first
        if self.context.get('has_startup_background'):
            return 'founder'

        if self.context.get('has_professional_experience'):
            work_history = self.context.get('work_history', '').lower()
            if any(kw in work_history for kw in ['engineer', 'developer', 'software']):
                return 'engineer'
            if any(kw in work_history for kw in ['designer', 'ux', 'ui']):
                return 'designer'
            if any(kw in work_history for kw in ['nurse', 'doctor', 'physician', 'healthcare']):
                return 'healthcare professional'
            if any(kw in work_history for kw in ['teacher', 'educator', 'professor']):
                return 'teacher'
            return 'professional'

        if self.context.get('has_research_experience'):
            return 'researcher'

        return 'student'

    def _is_background_covered(self, background: str) -> Tuple[bool, str]:
        """
        Check if background type is covered by templates.

        Returns:
            (is_covered: bool, match_type: str)
        """
        background_lower = background.lower()

        for bg_type, keywords in self.COVERED_BACKGROUNDS.items():
            if any(kw in background_lower for kw in keywords):
                return True, bg_type

        return False, 'uncovered'

    def _is_field_covered(self, field: str) -> bool:
        """Check if target field is covered by templates."""
        field_lower = field.lower()

        return any(covered_field in field_lower for covered_field in self.COVERED_FIELDS)

    def _is_edge_case(self, background: str, field: str) -> Tuple[bool, str]:
        """
        Check if background+field combination is an edge case.

        Edge cases are scenarios that theoretically match templates but
        actually need specialized treatment.
        """
        background_lower = background.lower()
        field_lower = field.lower()

        for bg_keyword, field_keyword, reason in self.EDGE_CASE_COMBINATIONS:
            # Check if background and field contain the keywords
            bg_match = bg_keyword in background_lower
            field_match = field_keyword in field_lower

            # For healthcare professionals applying to AI, check for various AI-related fields
            if bg_keyword in ['nurse', 'doctor'] and field_keyword == 'ai':
                field_match = any(ai_term in field_lower for ai_term in ['ai', 'artificial intelligence', 'medical ai', 'health tech'])

            if bg_match and field_match:
                return True, reason

        return False, ""

    def _calculate_coverage_score(
        self,
        background_covered: bool,
        field_covered: bool,
        is_edge_case: bool
    ) -> int:
        """
        Calculate coverage score (0-100).

        Scoring:
        - Background covered: +50 points
        - Field covered: +40 points
        - Has startup/founder flag: +10 points (extra templates)
        - Edge case detected: -30 points (needs special handling)
        """
        score = 0

        if background_covered:
            score += 50

        if field_covered:
            score += 40

        # Bonus for founder (lots of custom tasks available)
        if self.context.get('has_startup_background'):
            score += 10

        # Penalty for edge cases
        if is_edge_case:
            score -= 30

        return max(0, min(100, score))

    def _build_reasoning(
        self,
        background: str,
        field: str,
        background_covered: bool,
        field_covered: bool,
        is_edge_case: bool,
        edge_reason: str
    ) -> str:
        """Build human-readable reasoning for coverage decision."""
        parts = []

        # Background
        if background_covered:
            parts.append(f"✅ Background '{background}' is covered by templates")
        else:
            parts.append(f"❌ Background '{background}' NOT covered by templates")

        # Field
        if field_covered:
            parts.append(f"✅ Field '{field}' is covered by templates")
        else:
            parts.append(f"❌ Field '{field}' NOT covered by templates")

        # Edge case
        if is_edge_case:
            parts.append(f"⚠️  Edge case detected: {edge_reason}")

        return " | ".join(parts)

    def should_use_full_llm(self) -> bool:
        """
        Convenience method: Should we use full LLM generation?

        Returns:
            True if coverage_score < 40% (uncovered scenario)
        """
        result = self.detect_scenario_coverage()
        return result['recommendation'] == 'full_llm'

    def should_use_hybrid(self) -> bool:
        """
        Convenience method: Should we use hybrid approach?

        Returns:
            True if 40% <= coverage_score < 80% (partially covered)
        """
        result = self.detect_scenario_coverage()
        return result['recommendation'] == 'hybrid'


def create_scenario_detector(context: Dict[str, Any]) -> ScenarioDetector:
    """
    Factory function to create ScenarioDetector.

    Args:
        context: Full personalization context from profile_extractor

    Returns:
        ScenarioDetector instance
    """
    return ScenarioDetector(context)


def detect_coverage(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to detect scenario coverage.

    Args:
        context: Full personalization context

    Returns:
        Coverage detection result dictionary
    """
    detector = create_scenario_detector(context)
    return detector.detect_scenario_coverage()
