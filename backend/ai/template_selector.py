"""
Template Selector

Smart, rules-based selection of the right task template based on:
1. Milestone type (what user is trying to do)
2. User constraints (budget, timeline, experience)
3. User weaknesses (target specific gaps)
4. User context (current role, target role, etc.)

NO LLM calls - purely deterministic logic for guaranteed quality.
"""

from typing import Optional, List, Dict
from datetime import datetime, timedelta
from .task_templates import (
    TaskTemplate,
    TEMPLATE_REGISTRY,
    TemplateCategory,
    MilestoneType,
    BudgetTier,
    get_templates_by_milestone_type,
    get_templates_by_budget_tier,
)


class TemplateSelector:
    """
    Deterministic template selection based on user context.

    Selection priority:
    1. Milestone type (required)
    2. Budget tier (if applicable)
    3. User weakness (if relevant templates exist)
    4. Timeline urgency (deadline < 30 days)
    5. Experience level (entry vs mid vs senior)
    """

    def select(
        self,
        milestone_type: str,
        user_profile: any,
        goal_spec: any,
        milestone: any = None
    ) -> Optional[TaskTemplate]:
        """
        Select the best template for user's context.

        Args:
            milestone_type: Type of milestone (university_research, exam_prep, etc.)
            user_profile: UserProfile object with profile data
            goal_spec: GoalSpec object with goal constraints
            milestone: Optional Milestone object for deadline info

        Returns:
            TaskTemplate or None if no match
        """
        # Convert string to enum
        try:
            milestone_enum = MilestoneType(milestone_type)
        except ValueError:
            print(f"[TemplateSelector] Unknown milestone type: {milestone_type}")
            return None

        # Step 1: Get all templates for this milestone type
        candidates = get_templates_by_milestone_type(milestone_enum)

        if not candidates:
            print(f"[TemplateSelector] No templates for milestone type: {milestone_type}")
            return None

        print(f"[TemplateSelector] Found {len(candidates)} candidates for {milestone_type}")

        # Step 2: Filter by budget tier (if applicable)
        budget_tier = self._determine_budget_tier(goal_spec)
        budget_filtered = [t for t in candidates if t.budget_tier == budget_tier]

        if budget_filtered:
            candidates = budget_filtered
            print(f"[TemplateSelector] Filtered to {len(candidates)} templates for budget tier: {budget_tier.value}")

        # Step 3: Filter by user weakness (if applicable)
        if hasattr(user_profile, 'weaknesses') and user_profile.weaknesses:
            weakness = user_profile.weaknesses[0] if isinstance(user_profile.weaknesses, list) else user_profile.weaknesses
            weakness_filtered = [t for t in candidates if weakness.lower() in t.name.lower()]

            if weakness_filtered:
                candidates = weakness_filtered
                print(f"[TemplateSelector] Filtered to {len(candidates)} templates targeting weakness: {weakness}")

        # Step 4: Filter by urgency (if deadline < 30 days)
        if milestone and hasattr(milestone, 'target_date'):
            days_until = self._days_until_deadline(milestone.target_date)
            if days_until and days_until < 30:
                urgent_filtered = [t for t in candidates if 'intensive' in t.id or 'urgent' in t.id or 'quick' in t.id]
                if urgent_filtered:
                    candidates = urgent_filtered
                    print(f"[TemplateSelector] Filtered to urgent templates (deadline in {days_until} days)")

        # Step 5: Filter by experience level (for career templates)
        if goal_spec.category == 'career' and hasattr(user_profile, 'years_of_experience'):
            exp_level = self._determine_experience_level(user_profile.years_of_experience)
            exp_filtered = [t for t in candidates if exp_level in t.id or exp_level in t.name.lower()]

            if exp_filtered:
                candidates = exp_filtered
                print(f"[TemplateSelector] Filtered to {exp_level} templates")

        # Step 6: Return first match (or default if multiple)
        selected = candidates[0]
        print(f"[TemplateSelector] Selected template: {selected.id}")
        return selected

    def _determine_budget_tier(self, goal_spec: any) -> BudgetTier:
        """
        Determine budget tier from GoalSpec.

        Budget thresholds:
        - Budget: < $15,000
        - Standard: $15,000 - $30,000
        - Premium: > $30,000
        """
        # Check if budget info exists in specifications or constraints
        specs = getattr(goal_spec, 'specifications', {}) or {}
        constraints = getattr(goal_spec, 'constraints', {}) or {}

        # Extract budget value
        budget_str = specs.get('budget') or constraints.get('budget') or ''

        if not budget_str:
            return BudgetTier.STANDARD  # Default

        # Parse budget string (examples: "$10k", "£20k", "$15000-30000")
        budget_value = self._parse_budget(budget_str)

        if budget_value < 15000:
            return BudgetTier.BUDGET
        elif budget_value <= 30000:
            return BudgetTier.STANDARD
        else:
            return BudgetTier.PREMIUM

    def _parse_budget(self, budget_str: str) -> int:
        """
        Parse budget string to integer value.

        Examples:
        - "$10k" -> 10000
        - "£20k-30k" -> 20000 (take lower bound)
        - "$15000" -> 15000
        """
        # Remove currency symbols and spaces
        clean = budget_str.replace('$', '').replace('£', '').replace('€', '').replace(' ', '').lower()

        # Handle range (take lower bound)
        if '-' in clean:
            clean = clean.split('-')[0]

        # Handle 'k' suffix
        if 'k' in clean:
            clean = clean.replace('k', '000')

        # Convert to int
        try:
            return int(float(clean))
        except ValueError:
            return 20000  # Default to standard tier

    def _days_until_deadline(self, target_date: any) -> Optional[int]:
        """Calculate days until deadline"""
        if not target_date:
            return None

        # Handle different date formats
        if isinstance(target_date, str):
            try:
                target = datetime.strptime(target_date, '%Y-%m-%d').date()
            except ValueError:
                return None
        elif hasattr(target_date, 'date'):
            target = target_date.date()
        else:
            target = target_date

        today = datetime.now().date()
        delta = target - today
        return delta.days

    def _determine_experience_level(self, years_experience: int) -> str:
        """
        Map years of experience to level.

        - Entry: 0-2 years
        - Mid: 3-7 years
        - Senior: 8+ years
        """
        if years_experience is None:
            return 'entry_level'  # Default for new users
        if years_experience <= 2:
            return 'entry_level'
        elif years_experience <= 7:
            return 'mid_level'
        else:
            return 'senior'

    def select_multiple(
        self,
        milestone_type: str,
        user_profile: any,
        goal_spec: any,
        count: int = 5,
        milestone: any = None
    ) -> List[TaskTemplate]:
        """
        Select multiple templates for variety and comprehensive task generation.

        Returns diverse templates to generate 5-10 tasks per goalspec.
        Prioritizes:
        1. Budget-matching templates
        2. Experience level match (for career)
        3. Diversity in task types (quick wins + foundation tasks)

        Args:
            milestone_type: Type of milestone
            user_profile: User profile for filtering
            goal_spec: Goal specification
            count: Number of templates to return (default 5)
            milestone: Optional milestone for urgency filtering

        Returns:
            List of TaskTemplate objects (up to 'count')
        """
        # Convert string to enum
        try:
            milestone_enum = MilestoneType(milestone_type)
        except ValueError:
            print(f"[TemplateSelector] Unknown milestone type: {milestone_type}")
            return []

        # Get all candidates for this milestone type
        candidates = get_templates_by_milestone_type(milestone_enum)

        if not candidates:
            print(f"[TemplateSelector] No templates for milestone type: {milestone_type}")
            return []

        print(f"[TemplateSelector] Found {len(candidates)} candidates for {milestone_type}")

        # Apply budget filter (priority 1)
        budget_tier = self._determine_budget_tier(goal_spec)
        budget_filtered = [t for t in candidates if t.budget_tier == budget_tier]

        if budget_filtered:
            candidates = budget_filtered
            print(f"[TemplateSelector] Filtered to {len(candidates)} templates for budget tier: {budget_tier.value}")

        # Apply experience level filter for career templates (priority 2)
        if goal_spec.category == 'career' and hasattr(user_profile, 'years_of_experience'):
            exp_level = self._determine_experience_level(user_profile.years_of_experience)
            # Don't strictly filter - just prioritize matching templates
            exp_matched = [t for t in candidates if exp_level in t.id or exp_level in t.name.lower()]
            exp_unmatched = [t for t in candidates if t not in exp_matched]

            # Prioritize matched, but keep unmatched as fallback
            candidates = exp_matched + exp_unmatched
            print(f"[TemplateSelector] Prioritized {len(exp_matched)} {exp_level} templates")

        # Ensure diversity: include both quick wins and foundation tasks
        quick_wins = [t for t in candidates if t.timebox_minutes <= 30]
        foundation = [t for t in candidates if t.timebox_minutes > 30]

        # Mix: 40% quick wins, 60% foundation tasks
        quick_count = min(len(quick_wins), max(1, int(count * 0.4)))
        foundation_count = min(len(foundation), count - quick_count)

        selected = quick_wins[:quick_count] + foundation[:foundation_count]

        # If we still need more templates, add remaining candidates
        if len(selected) < count:
            remaining = [t for t in candidates if t not in selected]
            selected.extend(remaining[:count - len(selected)])

        print(f"[TemplateSelector] Selected {len(selected)} diverse templates ({quick_count} quick wins, {len(selected) - quick_count} foundation)")
        return selected[:count]

    def get_template_for_quick_win(
        self,
        category: str,
        user_profile: any,
        goal_spec: any
    ) -> Optional[TaskTemplate]:
        """
        Select a template specifically for Day 1 quick win tasks.

        Quick win criteria:
        - Low energy requirement
        - Short timebox (< 60 minutes)
        - Clear, simple deliverable
        """
        # Map category to suitable quick win milestone types
        quick_win_milestones = {
            'study': [MilestoneType.EXAM_PREP, MilestoneType.UNIVERSITY_RESEARCH],
            'career': [MilestoneType.RESUME_UPDATE, MilestoneType.JOB_SEARCH],
        }

        milestone_types = quick_win_milestones.get(category, [])

        for milestone_type in milestone_types:
            templates = get_templates_by_milestone_type(milestone_type)

            # Filter for quick templates (low energy, short timebox)
            quick_templates = [
                t for t in templates
                if t.timebox_minutes <= 60 and t.energy_level in ['low', 'medium']
            ]

            if quick_templates:
                return quick_templates[0]

        return None


# Singleton instance
template_selector = TemplateSelector()
