"""
Task Verifier

Verifies task quality (atomicity, personalization) and fixes failed tasks.
This is the final quality gate before tasks are saved to the database.

Phase 3: Quality Improvements
"""

import json
import logging
from typing import Dict, List, Any, Tuple

logger = logging.getLogger(__name__)


class TaskVerifier:
    """
    Verify task quality and fix issues before saving to database.

    Checks each task for:
    1. Atomicity - Single action, 15-60 min timebox
    2. Personalization - Uses user's actual context/stories
    3. Specific resource - Names actual person/company/URL

    If a task fails verification, attempts to fix it using LLM.
    """

    def __init__(self):
        """Initialize with OpenAI service"""
        from ai.services import AIService

        self.ai_service = AIService(provider='openai')
        logger.info("[TaskVerifier] Initialized")

    def verify_and_fix(
        self,
        tasks: List[Dict[str, Any]],
        context: Dict[str, Any],
        user_stories: Dict[str, str],
        max_retries: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Verify each task and fix if needed.

        Args:
            tasks: List of generated tasks
            context: User context from profile extractor
            user_stories: User stories from story extractor
            max_retries: Max attempts to fix a task

        Returns:
            List of verified (and possibly fixed) tasks
        """
        logger.info(f"[TaskVerifier] Verifying {len(tasks)} tasks")

        verified_tasks = []
        fixed_count = 0
        rejected_count = 0

        for i, task in enumerate(tasks):
            task_title = task.get('title', 'Unknown')[:50]
            logger.debug(f"[TaskVerifier] Checking task {i+1}: {task_title}...")

            # Verify task
            is_valid, issues = self._verify_task(task, context, user_stories)

            if is_valid:
                verified_tasks.append(task)
                continue

            # Task failed - try to fix
            logger.warning(f"[TaskVerifier] Task failed verification: {issues}")

            fixed_task = self._fix_task(task, issues, context, user_stories)

            # Verify again
            is_valid_now, _ = self._verify_task(fixed_task, context, user_stories)

            if is_valid_now:
                verified_tasks.append(fixed_task)
                fixed_count += 1
                logger.info(f"[TaskVerifier] ✅ Fixed task: {task_title}")
            else:
                # Give up on this task
                rejected_count += 1
                logger.error(f"[TaskVerifier] ❌ Could not fix task, skipping: {task_title}")

        logger.info(f"[TaskVerifier] Results: {len(verified_tasks)} passed, {fixed_count} fixed, {rejected_count} rejected")

        return verified_tasks

    def _verify_task(
        self,
        task: Dict[str, Any],
        context: Dict[str, Any],
        user_stories: Dict[str, str]
    ) -> Tuple[bool, List[str]]:
        """
        Verify task meets quality standards.

        Returns:
            Tuple of (passes: bool, issues: list of problems)
        """
        prompt = f"""Verify this task meets quality standards.

TASK:
=====
Title: {task.get('title', '')}
Description: {task.get('description', '')}
Timebox: {task.get('timebox_minutes', 30)} minutes

USER STORIES (context to reference):
====================================
Work: {user_stories.get('work_story', 'N/A')}
Achievement: {user_stories.get('achievement_story', 'N/A')}
Network: {user_stories.get('network_story', 'N/A')}
Challenge: {user_stories.get('challenge_story', 'N/A')}
Goal: {user_stories.get('aspiration_story', 'N/A')}

USER CONTEXT:
=============
Current Company: {context.get('current_company', 'N/A')}
Current Role: {context.get('current_role', 'N/A')}
Target Role: {context.get('target_role', 'N/A')}
Target Companies: {context.get('target_companies', 'N/A')}

VERIFICATION CHECKLIST:
=======================

1. ✓ ATOMIC?
   - Single action only (not "do X AND Y")
   - 15-60 minute timebox (not 2+ hours)
   - Clear when it's done

2. ✓ PERSONALIZED?
   - References user's actual background/experience
   - Uses specific companies/projects they mentioned
   - NOT generic advice anyone could follow

3. ✓ SPECIFIC RESOURCE?
   - Names actual person/company/website/document
   - NOT vague like "some companies" or "a professor"

EXAMPLES:

✅ GOOD (passes all):
"Read KPMG's 2024 Transparency Report (pages 15-30) and create comparison doc: Your Forte Finance reports vs audit methodology"
- Atomic: Single action, ~45 min
- Personalized: Uses "YOUR Forte Finance reports"
- Specific: "KPMG 2024 Transparency Report, pages 15-30"

❌ BAD (fails):
"Research audit methodology and update resume"
- Not atomic: 2 actions
- Not personalized: Generic
- Not specific: "research" is vague

Verify the task above.

Return ONLY valid JSON:
{{
    "is_atomic": true/false,
    "is_personalized": true/false,
    "has_specific_resource": true/false,
    "passes": true/false,
    "issues": ["list of specific problems found"],
    "fix_suggestion": "how to improve if fails"
}}
"""

        try:
            response = self.ai_service.call_llm(
                system_prompt="You are a strict quality assurance expert for task verification. Return only valid JSON.",
                user_prompt=prompt,
                response_format="json"
            )

            result = json.loads(response)

            passes = result.get('passes', False)
            issues = result.get('issues', [])

            return passes, issues

        except Exception as e:
            logger.error(f"[TaskVerifier] Verification call failed: {e}")
            # If verification fails, assume task is OK to avoid blocking
            return True, []

    def _fix_task(
        self,
        task: Dict[str, Any],
        issues: List[str],
        context: Dict[str, Any],
        user_stories: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Fix task based on verification issues.

        Returns:
            Fixed task dictionary
        """
        prompt = f"""Fix this task to meet quality standards.

ORIGINAL TASK:
==============
Title: {task.get('title', '')}
Description: {task.get('description', '')}
Timebox: {task.get('timebox_minutes', 30)} minutes

ISSUES FOUND:
=============
{json.dumps(issues, indent=2)}

USER STORIES (must reference these):
====================================
Work: {user_stories.get('work_story', 'N/A')}
Achievement: {user_stories.get('achievement_story', 'N/A')}
Network: {user_stories.get('network_story', 'N/A')}
Challenge: {user_stories.get('challenge_story', 'N/A')}
Goal: {user_stories.get('aspiration_story', 'N/A')}

USER CONTEXT:
=============
Current Company: {context.get('current_company', 'N/A')}
Current Role: {context.get('current_role', 'N/A')}
Target Role: {context.get('target_role', 'N/A')}
Target Companies: {context.get('target_companies', 'N/A')}

TASK: Rewrite to fix ALL issues.

Requirements:
- ATOMIC: 15-60 min, single action only
- PERSONALIZED: Reference user's actual experience from stories
- SPECIFIC: Name actual person/company/URL

Return ONLY valid JSON:
{{
    "title": "Fixed title (max 100 chars)",
    "description": "Fixed description with specific steps",
    "timebox_minutes": 15-60,
    "specific_resource": "Actual URL/person/company name"
}}
"""

        try:
            response = self.ai_service.call_llm(
                system_prompt="You are an expert at making tasks atomic and personalized. Return only valid JSON.",
                user_prompt=prompt,
                response_format="json"
            )

            fixed = json.loads(response)

            # Merge fixed fields into original task
            task_copy = task.copy()
            task_copy['title'] = fixed.get('title', task.get('title'))
            task_copy['description'] = fixed.get('description', task.get('description'))
            task_copy['timebox_minutes'] = fixed.get('timebox_minutes', task.get('timebox_minutes', 30))

            if 'specific_resource' in fixed:
                task_copy['specific_resource'] = fixed['specific_resource']

            return task_copy

        except Exception as e:
            logger.error(f"[TaskVerifier] Fix task failed: {e}")
            return task


def create_task_verifier() -> TaskVerifier:
    """Factory function to create TaskVerifier instance"""
    return TaskVerifier()
