"""
Atomic Task Generator (Tier 2 of Two-Tier Task Generation)

Breaks down milestones into 5-6 atomic tasks.

ATOMIC = Single action, 15-60 min, specific resource, clear deliverable

Phase 2, Day 1-2: Two-Tier Atomic Task Generation
"""

import json
import logging
from typing import Dict, List, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class AtomicTaskGenerator:
    """
    Generates atomic tasks from milestones using OpenAI GPT-4o-mini.

    Two-tier approach:
    - Tier 1 (milestone_generator): Goal → 5 milestones
    - Tier 2 (this class): Milestone → 5-6 atomic tasks

    Example:
        Milestone: "Research and shortlist 5 CS programs"
        →
        Atomic Tasks:
        1. Visit MIT EECS website, note admission requirements (30min)
        2. Check Stanford CS application deadlines, save to calendar (15min)
        3. Create spreadsheet comparing 5 programs (tuition, deadlines) (45min)
        4. Email Columbia CS advisor asking about research fit (20min)
        5. Read 3 faculty research papers at target schools (60min)
    """

    def __init__(self):
        """Initialize with OpenAI service"""
        from ai.services import AIService

        # Use OpenAI GPT-4o for high-quality personalization
        self.ai_service = AIService(provider='openai')
        logger.info("[AtomicTaskGenerator] Initialized with GPT-4o")

    def generate_atomic_tasks(
        self,
        milestone: Dict[str, Any],
        goalspec,
        user_profile,
        context: Dict[str, Any],
        user_stories: Dict[str, str] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate 5-6 atomic tasks for a milestone.

        Args:
            milestone: Milestone dictionary from MilestoneGenerator
            goalspec: GoalSpec instance
            user_profile: UserProfile instance
            context: Personalization context

        Returns:
            List of 5-6 atomic task dictionaries:
            [
                {
                    "title": "Visit MIT EECS website and note admission requirements",
                    "description": "Go to web.mit.edu/eecs/graduate. Note GPA cutoff...",
                    "timebox_minutes": 30,
                    "priority": 4,
                    "energy_level": "medium",
                    "deliverable": "Admission requirements documented in notes",
                    "specific_resource": "web.mit.edu/eecs/graduate",
                    "task_type": "research"
                },
                ...
            ]
        """
        logger.info(f"[AtomicTaskGenerator] Breaking down milestone: {milestone['title'][:60]}...")

        # Build atomic task prompt
        prompt = self._build_atomic_prompt(milestone, goalspec, user_profile, context, user_stories)

        # Generate with OpenAI
        try:
            response = self.ai_service.call_llm(
                system_prompt="You are an expert task breakdown specialist that generates atomic tasks in JSON format.",
                user_prompt=prompt,
                response_format="json"  # Force JSON output
            )

            # Parse JSON response
            tasks = self._parse_atomic_response(response)

            if not tasks or len(tasks) < 3:
                logger.warning(f"[AtomicTaskGenerator] Generated only {len(tasks)} tasks, expected 5-6")
                return []

            logger.info(f"[AtomicTaskGenerator] ✅ Generated {len(tasks)} atomic tasks")
            for idx, task in enumerate(tasks, 1):
                logger.info(f"  {idx}. {task['title'][:60]}... ({task['timebox_minutes']}min)")

            return tasks

        except Exception as e:
            logger.error(f"[AtomicTaskGenerator] Failed to generate atomic tasks: {e}")
            return []

    def _build_atomic_prompt(
        self,
        milestone: Dict[str, Any],
        goalspec,
        user_profile,
        context: Dict[str, Any],
        user_stories: Dict[str, str] = None
    ) -> str:
        """Build prompt that enforces atomicity"""

        # Extract context
        background = context.get('background', 'student')
        field = context.get('field', goalspec.title)
        target_universities = context.get('target_universities', [])
        target_unis_str = ', '.join(target_universities[:3]) if target_universities else 'target universities'

        # Career-specific context
        target_role = context.get('target_role', 'N/A')
        target_companies = context.get('target_companies_string', context.get('target_companies', 'N/A'))
        current_company = context.get('current_company', 'N/A')
        current_role = context.get('current_role', 'N/A')
        startup_experience = context.get('startup_experience', 'None')
        notable_achievements = context.get('notable_achievements', 'None')

        # Build user stories section if available
        stories_section = ""
        if user_stories:
            stories_section = f"""
USER'S STORY (EVERY TASK MUST BUILD ON THIS):
==============================================
Work Experience: {user_stories.get('work_story', 'N/A')}
Key Achievement: {user_stories.get('achievement_story', 'N/A')}
Network: {user_stories.get('network_story', 'N/A')}
Challenge: {user_stories.get('challenge_story', 'N/A')}
Aspiration: {user_stories.get('aspiration_story', 'N/A')}

CRITICAL: Each task MUST reference specific elements from their story.
Example: If work_story = "Built 21 financial reports at Forte Finance",
Task should be: "Create doc comparing YOUR 21 Forte Finance reports vs KPMG audit work papers"
NOT: "Research audit methodology" (too generic)
"""

        prompt = f"""You are an expert task breakdown specialist. Break this milestone into 5-6 ATOMIC tasks.

MILESTONE TO BREAK DOWN:
========================
Title: {milestone['title']}
Description: {milestone['description']}
Duration: {milestone['duration_weeks']} weeks
Success Criteria: {milestone['success_criteria']}

USER CONTEXT:
=============
Background: {background}
Field: {field}
Goal: {goalspec.title}
Current Company: {current_company}
Current Role: {current_role}
Target Role: {target_role}
Target Companies: {target_companies}
Target Universities: {target_unis_str}
Startup Experience: {startup_experience}
Notable Achievements: {notable_achievements}
{stories_section}

CRITICAL: ATOMIC TASK REQUIREMENTS
===================================
Each task MUST be ATOMIC (indivisible). An atomic task is:

✅ **SINGLE ACTION ONLY**
   - NOT: "Research universities and create spreadsheet" (2 actions)
   - YES: "Visit MIT EECS website and note admission requirements" (1 action)

✅ **15-60 MINUTE TIMEBOX**
   - NOT: "Write complete SOP" (4+ hours)
   - YES: "Draft SOP introduction paragraph (150 words)" (30min)

✅ **SPECIFIC RESOURCE/PERSON/URL**
   - NOT: "Email a professor" (which professor?)
   - YES: "Email Prof. Barbara Liskov at MIT about distributed systems research"

✅ **CLEAR INPUT → OUTPUT**
   - NOT: "Prepare for interview" (vague)
   - YES: "Practice answering 'Why MIT?' with 2-minute response"

✅ **NO META-TASKS**
   - NOT: "Develop networking strategy" (meta-task - requires planning)
   - NOT: "Create study plan" (meta-task)
   - YES: "Connect with John Smith (Goldman VP) on LinkedIn with personalized note"

EXAMPLES OF ATOMIC TASKS:
==========================
For milestone "Research and shortlist 5 CS programs":

GOOD (Atomic):
- "Visit MIT EECS admissions page (web.mit.edu/eecs/graduate) and note GPA requirement" (30min)
- "Check Stanford CS application deadline on website and add to Google Calendar" (15min)
- "Create Google Sheets with columns: University, Tuition, Deadline, GPA requirement" (20min)
- "Email Prof. Barbara Liskov (liskov@mit.edu) asking about distributed systems lab opportunities" (25min)
- "Read Prof. Martin Rinard's latest paper on program analysis (30min)"
- "Compare tuition costs for MIT ($52k), Stanford ($55k), CMU ($50k) in spreadsheet" (20min)

BAD (Not Atomic):
- "Research MIT's CS program" (too broad, multiple actions)
- "Email professors about research" (which professors? how many?)
- "Compare all programs" (vague, no specific output)

TASK FORMAT:
============
Return ONLY valid JSON (no markdown, no explanation):

{{
  "tasks": [
    {{
      "title": "Specific atomic action with resource (max 100 chars)",
      "description": "Detailed steps:\\n1. Go to [specific URL/location]\\n2. Do [specific action]\\n3. Output: [specific deliverable]\\n\\nWhy: [how this helps milestone]",
      "timebox_minutes": 15-60,
      "priority": 3-5,
      "energy_level": "low|medium|high",
      "deliverable": "Concrete output (e.g., 'Requirements documented in notes')",
      "specific_resource": "URL, person name, tool, or location",
      "task_type": "research|communication|writing|administrative"
    }},
    ... (4-5 more tasks)
  ]
}}

VALIDATION CHECKLIST (Every task must pass):
=============================================
1. ✅ Single action (not "Research AND create" - split into 2 tasks)
2. ✅ 15-60 minute timebox (NOT 2+ hours)
3. ✅ Specific resource named (person, URL, tool, document)
4. ✅ Clear deliverable (what you'll have when done)
5. ✅ No meta-language ("develop strategy", "create plan", "prepare for")

USER-SPECIFIC REQUIREMENTS (CRITICAL FOR PERSONALIZATION):
============================================================
MUST use user's actual context in EVERY task:

- Current Company: {current_company} (if not N/A, reference THIS company)
- Current Role: {current_role} (if not N/A, reference THIS role)
- Target Role: {target_role} (if not N/A, EVERY task should relate to THIS role)
- Target Companies: {target_companies} (if not N/A, mention THESE companies, not generic ones)
- Target Universities: {target_unis_str}
- Background: {background}
- Field: {field}

BAD EXAMPLES (TOO GENERIC):
❌ "Research career transition strategies"
❌ "Update LinkedIn profile"
❌ "Network with professionals in your field"
❌ "Research company culture at top firms"

GOOD EXAMPLES (PERSONALIZED TO USER):
✅ "Read KPMG's Transparency Report 2024 and map sections 15-30 to your {current_company} financial reporting work" (uses ACTUAL companies)
✅ "Email your {current_company} manager asking about their experiences with {target_companies} auditors" (uses ACTUAL context)
✅ "LinkedIn search: '{target_companies} {target_role}' + filter 'Past company: Banks' - save 10 profiles" (uses ACTUAL role and company)
✅ "Watch 'Day in Life of {target_companies} {target_role}' on YouTube and note 3 differences from your {current_role} work" (ultra-specific)
- NO placeholders like "[university name]" or "[professor]"

Generate 5-6 atomic tasks for THIS milestone NOW:"""

        return prompt

    def _parse_atomic_response(self, response: str) -> List[Dict[str, Any]]:
        """
        Parse JSON response from OpenAI.

        Args:
            response: Raw response from OpenAI

        Returns:
            List of atomic task dictionaries
        """
        try:
            # Remove markdown code fences if present
            response = response.strip()
            if response.startswith('```'):
                lines = response.split('\n')
                json_lines = []
                in_code = False
                for line in lines:
                    if line.startswith('```'):
                        in_code = not in_code
                        continue
                    if in_code or (not line.startswith('```')):
                        json_lines.append(line)
                response = '\n'.join(json_lines)

            # Parse JSON
            data = json.loads(response)

            # Extract tasks array
            if isinstance(data, dict) and 'tasks' in data:
                tasks = data['tasks']
            elif isinstance(data, list):
                tasks = data
            else:
                logger.error(f"[AtomicTaskGenerator] Unexpected response format: {type(data)}")
                return []

            # Validate and enrich each task
            validated_tasks = []
            for task in tasks:
                if self._validate_atomic_task(task):
                    # Enrich with additional fields for PathAI todo model
                    enriched_task = self._enrich_task(task)
                    validated_tasks.append(enriched_task)
                else:
                    logger.warning(f"[AtomicTaskGenerator] Non-atomic task rejected: {task.get('title', 'Unknown')[:60]}...")

            return validated_tasks

        except json.JSONDecodeError as e:
            logger.error(f"[AtomicTaskGenerator] JSON parsing failed: {e}")
            logger.error(f"[AtomicTaskGenerator] Raw response: {response[:500]}...")
            return []

    def _validate_atomic_task(self, task: Dict[str, Any]) -> bool:
        """
        Validate that task is truly atomic.

        Args:
            task: Task dictionary

        Returns:
            True if atomic, False otherwise
        """
        # Required fields
        required_fields = ['title', 'description', 'timebox_minutes']
        for field in required_fields:
            if field not in task:
                logger.warning(f"[AtomicTaskGenerator] Missing field '{field}'")
                return False

        # Check timebox (atomic tasks should be 15-60min, max 90min)
        timebox = task.get('timebox_minutes', 0)
        if not isinstance(timebox, (int, float)) or timebox < 10 or timebox > 90:
            logger.warning(f"[AtomicTaskGenerator] Invalid timebox: {timebox}min (should be 15-60min)")
            return False

        # Check for meta-task indicators in title/description
        title = task.get('title', '').lower()
        description = task.get('description', '').lower()

        meta_indicators = [
            'develop plan',
            'create strategy',
            'research and',  # "research AND X" = 2 actions
            'build framework',
            'prepare for',  # Too vague
            'design system'
        ]

        for indicator in meta_indicators:
            if indicator in title or indicator in description:
                logger.warning(f"[AtomicTaskGenerator] Meta-task indicator '{indicator}' found in: {title[:60]}")
                return False

        # Title should not be too long (atomic tasks are focused)
        if len(title) > 120:
            logger.warning(f"[AtomicTaskGenerator] Title too long ({len(title)} chars): {title[:60]}...")
            return False

        return True

    def _enrich_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich task with additional fields for PathAI todo model.

        Args:
            task: Basic task dictionary

        Returns:
            Enriched task dictionary
        """
        # Map energy levels
        energy_map = {
            'low': 'low',
            'medium': 'medium',
            'high': 'high'
        }
        energy = task.get('energy_level', 'medium')
        task['energy_level'] = energy_map.get(energy, 'medium')

        # Ensure priority is integer (3-5)
        priority = task.get('priority', 3)
        if isinstance(priority, str):
            priority_map = {'low': 2, 'medium': 3, 'high': 4, 'critical': 5}
            task['priority'] = priority_map.get(priority, 3)
        else:
            task['priority'] = max(2, min(5, int(priority)))

        # Add source metadata
        task['source'] = 'atomic_task_generator'
        task['task_category'] = 'atomic'

        # Add definition_of_done from deliverable
        deliverable = task.get('deliverable', 'Task completed')
        task['definition_of_done'] = [f"✅ {deliverable}"]

        # Add category (default to 'study' for now, can be inferred)
        if 'task_type' not in task:
            task['task_type'] = 'research'

        return task


def create_atomic_task_generator() -> AtomicTaskGenerator:
    """Factory function to create AtomicTaskGenerator instance"""
    return AtomicTaskGenerator()
