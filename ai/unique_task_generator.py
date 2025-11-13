"""
Unique Task Generator (Week 1 Day 5: Hybrid Task Generation Enhancement)

Generates 2-3 truly unique tasks per user using Claude Sonnet.

These tasks are:
- NOT in templates (templates cover only ~20% of scenarios)
- NOT rule-based (custom_task_generators.py does founder/GPA tasks)
- FULLY personalized to individual user's background, goals, and constraints

Examples:
- Founder applying to AI PhD: "Write research proposal connecting PathAI's 200k users data to bias detection research"
- Designer switching to HCI: "Create portfolio case study showing design research methodology for graduate admissions"
- Nurse → Medical AI PhD: "Document patient care edge cases that could inform clinical AI research questions"

Strategy:
1. Use full user profile context (not just templates variables)
2. Claude Sonnet analyzes gaps in template coverage
3. Generate 2-3 high-value unique tasks
4. Track costs per user
"""

from typing import List, Dict, Any
from decimal import Decimal
import json

from .llm_service import llm_service, generate_with_tracking
from .task_cache import get_cached_tasks, cache_tasks


class UniqueTaskGenerator:
    """
    Generates 2-3 LLM-powered unique tasks per user.

    Week 1 Day 5: Uses Claude Sonnet to find gaps in template coverage
    and generate truly personalized tasks.
    """

    def __init__(self, user, user_profile, context: Dict[str, Any]):
        """
        Initialize with user context.

        Args:
            user: User object for cost tracking
            user_profile: UserProfile object
            context: Full personalization context from profile_extractor
        """
        self.user = user
        self.user_profile = user_profile
        self.context = context

    def generate_unique_tasks(self, goalspec, existing_tasks: List[Dict] = None) -> List[Dict]:
        """
        Generate 2-3 unique tasks using Claude Sonnet.

        Week 3: Now with caching - users with similar profiles get similar unique tasks.

        Args:
            goalspec: GoalSpec object
            existing_tasks: List of already-generated tasks (templates + custom)

        Returns:
            List of 2-3 unique task dictionaries
        """
        existing_tasks = existing_tasks or []

        # Week 3: Check cache first
        # Note: Unique tasks are cached by profile hash, not existing_tasks
        # This works because similar profiles generate similar template tasks,
        # so unique tasks that fill gaps are also similar
        cached_tasks = get_cached_tasks(
            context=self.context,
            goalspec=goalspec,
            generation_type='unique'
        )

        if cached_tasks:
            print(f"[UniqueTaskGenerator] ✅ Using cached unique tasks ({len(cached_tasks)} tasks)")
            print(f"[UniqueTaskGenerator] 💰 Cost saved: ~$0.05-0.10 (cache hit)")
            return cached_tasks

        # Cache miss - generate with LLM
        print(f"[UniqueTaskGenerator] ❌ Cache miss - generating with LLM")

        # Build prompt for Claude Sonnet
        prompt = self._build_unique_task_prompt(goalspec, existing_tasks)

        # Generate using llm_service with cost tracking
        try:
            result = generate_with_tracking(
                user=self.user,
                prompt=prompt,
                operation='unique_task_generation',
                max_tokens=1500,
                temperature=0.7  # Higher temp for creativity
            )

            tasks_json = result['text']
            cost = result['cost']

            # Parse JSON response
            unique_tasks = self._parse_llm_response(tasks_json)

            print(f"[UniqueTaskGenerator] Generated {len(unique_tasks)} unique tasks (cost: ${cost:.4f})")

            # Week 3: Cache tasks for future similar users
            if unique_tasks:
                cache_tasks(
                    tasks=unique_tasks,
                    context=self.context,
                    goalspec=goalspec,
                    generation_type='unique',
                    cost=cost
                )

            return unique_tasks

        except Exception as e:
            print(f"[UniqueTaskGenerator] Failed to generate unique tasks: {e}")
            return []

    def _build_unique_task_prompt(self, goalspec, existing_tasks: List[Dict]) -> str:
        """
        Build prompt for Claude Sonnet to generate unique tasks.

        Strategy: Show Claude the user's full profile and existing tasks,
        ask it to find gaps and generate 2-3 high-value unique tasks.
        """
        # Summarize existing tasks
        existing_titles = [t.get('title', '')[:80] for t in existing_tasks[:15]]
        existing_summary = "\n".join([f"- {title}" for title in existing_titles])

        # Extract key user background
        background = self._extract_key_background()

        prompt = f"""You are a personalized task planning AI. Your job is to generate 2-3 UNIQUE, high-value tasks that are NOT covered by existing templates.

USER PROFILE:
{background}

GOAL:
{goalspec.title}
{goalspec.description if hasattr(goalspec, 'description') else ''}

EXISTING TASKS (from templates):
{existing_summary}

YOUR TASK:
Generate 2-3 UNIQUE tasks that:
1. Are NOT generic (no "Research universities", "Prepare resume" - those are covered by templates)
2. Leverage this user's SPECIFIC background (startup, achievements, unique experiences)
3. Are HIGH-VALUE and differentiate this user from other applicants
4. Connect their unique background to their goal

Examples of GOOD unique tasks:
- "Write research proposal connecting PathAI's scalability challenges (200k users) to distributed systems coursework at MIT"
- "Create portfolio case study: How you debugged production issue affecting 10k users, showing systematic problem-solving"
- "Draft essay: Lessons from failed startup pivot that taught you to embrace ambiguity (connects to research mindset)"

Examples of BAD unique tasks (too generic, covered by templates):
- "Research MIT's Computer Science program" ❌ (template covers this)
- "Update resume with latest achievements" ❌ (template covers this)
- "Practice IELTS speaking" ❌ (template covers this)

Return ONLY valid JSON array (no markdown, no explanation):
[
  {{
    "title": "Task title (specific, actionable, connects user's background to goal)",
    "description": "Why this task matters and what makes it unique to this user",
    "timebox_minutes": 90-180,
    "priority": 4-5,
    "energy_level": "high",
    "definition_of_done": "Clear deliverable (bullet points)",
    "task_type": "essay" | "documentation" | "research" | "portfolio",
    "category": "{self.context.get('category', 'study')}"
  }}
]

Generate 2-3 tasks. Focus on QUALITY over quantity."""

        return prompt

    def _extract_key_background(self) -> str:
        """
        Extract key user background for prompt.

        Shows Claude the most important differentiating factors.
        """
        parts = []

        # Startup/founder background
        if self.context.get('has_startup_background'):
            startup_name = self.context.get('startup_name', 'startup')
            startup_users = self.context.get('startup_users', '0')
            startup_desc = self.context.get('startup_description', '')
            parts.append(f"🚀 Founder: Built {startup_name} ({startup_desc}) to {startup_users} users")

        # Notable achievements
        if self.context.get('has_notable_achievements'):
            achievements = self.context.get('notable_achievements', [])
            if achievements:
                parts.append(f"🏆 Achievements: {', '.join(achievements[:3])}")

        # Academic background
        if self.context.get('gpa_raw'):
            gpa = self.context.get('gpa_raw')
            field = self.context.get('field', 'their field')
            parts.append(f"📚 Academic: {field}, GPA {gpa}")

        # Test scores
        if self.context.get('test_scores'):
            scores = self.context.get('test_scores', {})
            score_str = ', '.join([f"{k}: {v}" for k, v in scores.items()])
            parts.append(f"📝 Tests: {score_str}")

        # Work experience
        if self.context.get('has_work_experience'):
            years = self.context.get('years_experience', 0)
            role = self.context.get('current_role', 'professional')
            parts.append(f"💼 Experience: {years} years as {role}")

        # Target
        target_unis = self.context.get('target_universities', [])
        if target_unis:
            parts.append(f"🎯 Target: {', '.join(target_unis[:3])}")

        return "\n".join(parts) if parts else "No detailed background available"

    def _parse_llm_response(self, response_text: str) -> List[Dict]:
        """
        Parse Claude's JSON response into task dictionaries.

        Handles potential JSON parsing errors gracefully.
        """
        try:
            # Remove markdown code blocks if present
            response_text = response_text.strip()
            if response_text.startswith('```'):
                # Remove ```json and ``` markers
                lines = response_text.split('\n')
                response_text = '\n'.join(lines[1:-1])

            # Parse JSON
            tasks = json.loads(response_text)

            # Validate structure
            if not isinstance(tasks, list):
                print(f"[UniqueTaskGenerator] Invalid response: not a list")
                return []

            # Add metadata to each task
            for task in tasks:
                task['source'] = 'unique_generator'
                task['task_category'] = 'unique'
                task['is_quick_win'] = task.get('timebox_minutes', 120) <= 30
                task['constraints'] = {}
                task['lets_go_inputs'] = []
                task['artifact_template'] = {}
                task['external_url'] = None
                task['notes'] = 'LLM-generated unique task'

            # Limit to 3 tasks max
            return tasks[:3]

        except json.JSONDecodeError as e:
            print(f"[UniqueTaskGenerator] JSON parse error: {e}")
            print(f"[UniqueTaskGenerator] Response was: {response_text[:200]}")
            return []
        except Exception as e:
            print(f"[UniqueTaskGenerator] Error parsing response: {e}")
            return []


def generate_unique_tasks(user, user_profile, context: Dict[str, Any], goalspec, existing_tasks: List[Dict] = None) -> List[Dict]:
    """
    Convenience function to generate unique tasks.

    Args:
        user: User object for cost tracking
        user_profile: UserProfile object
        context: Full personalization context
        goalspec: GoalSpec object
        existing_tasks: Already-generated tasks (templates + custom)

    Returns:
        List of 2-3 unique task dictionaries
    """
    generator = UniqueTaskGenerator(user, user_profile, context)
    return generator.generate_unique_tasks(goalspec, existing_tasks)
