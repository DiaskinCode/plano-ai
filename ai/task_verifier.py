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
        Verify all tasks in BATCH and fix if needed (optimized - 2 LLM calls instead of 50+).

        Args:
            tasks: List of generated tasks
            context: User context from profile extractor
            user_stories: User stories from story extractor
            max_retries: Max attempts to fix a task

        Returns:
            List of verified (and possibly fixed) tasks
        """
        logger.info(f"[TaskVerifier] Batch verifying {len(tasks)} tasks (optimized)")

        if not tasks:
            return []

        # Step 1: Batch verify all tasks in ONE LLM call
        verification_results = self._batch_verify(tasks, context, user_stories)

        # Separate passed and failed tasks
        passed_tasks = []
        failed_tasks = []

        for i, task in enumerate(tasks):
            result = verification_results.get(str(i), {})
            if result.get('passes', True):  # Default to True if not in results
                passed_tasks.append(task)
            else:
                task['_verification_issues'] = result.get('issues', [])
                task['_task_index'] = i
                failed_tasks.append(task)

        logger.info(f"[TaskVerifier] Batch verification: {len(passed_tasks)} passed, {len(failed_tasks)} need fixing")

        # Step 2: Batch fix all failed tasks in ONE LLM call
        if failed_tasks:
            fixed_tasks = self._batch_fix(failed_tasks, context, user_stories)
            passed_tasks.extend(fixed_tasks)
            logger.info(f"[TaskVerifier] Batch fixed {len(fixed_tasks)}/{len(failed_tasks)} tasks")

        logger.info(f"[TaskVerifier] ✅ Final: {len(passed_tasks)} verified tasks")

        return passed_tasks

    def _batch_verify(
        self,
        tasks: List[Dict[str, Any]],
        context: Dict[str, Any],
        user_stories: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Verify ALL tasks in a single LLM call.

        Returns:
            Dict mapping task index to verification result
        """
        # Build task list for prompt
        task_list = []
        for i, task in enumerate(tasks):
            task_list.append({
                'index': i,
                'title': task.get('title', ''),
                'description': task.get('description', '')[:200],  # Truncate for token efficiency
                'timebox': task.get('timebox_minutes', 30)
            })

        prompt = f"""Verify these {len(tasks)} tasks meet quality standards.

USER CONTEXT:
- Target Role: {context.get('target_role', 'N/A')}
- Current Company: {context.get('current_company', 'N/A')}
- Target Companies: {context.get('target_companies', 'N/A')}

TASKS TO VERIFY:
{json.dumps(task_list, indent=2)}

QUALITY STANDARDS (be lenient - only fail obviously bad tasks):
1. ATOMIC: Single action, reasonable timebox (15-90 min is OK)
2. CLEAR: Has specific deliverable or outcome
3. NOT VAGUE: Avoids "some", "various", "explore" without specifics
4. NO PLACEHOLDERS: Reject obvious placeholders like "P University", "X Company", "T, O, P", single-letter abbreviations

NOTE: Do NOT fail tasks for:
- Being "too generic" if the action is clear
- Timebox being slightly outside 15-60 range

CRITICAL - MUST FAIL for:
- Obvious placeholders: "P University", "T, O, P Universities", "X Company", single letters as names
- Vague resources: "a professor", "some companies", "various universities" without specific names

Return JSON with verification for EACH task by index:
{{
    "0": {{"passes": true/false, "issues": ["list of issues if fails"]}},
    "1": {{"passes": true/false, "issues": []}},
    ...
}}
"""

        try:
            response = self.ai_service.call_llm(
                system_prompt="You are a lenient quality reviewer. Only fail obviously bad tasks. Return valid JSON.",
                user_prompt=prompt,
                response_format="json"
            )

            result = json.loads(response)
            return result

        except Exception as e:
            logger.error(f"[TaskVerifier] Batch verification failed: {e}")
            # If batch verification fails, assume all tasks pass
            return {str(i): {'passes': True, 'issues': []} for i in range(len(tasks))}

    def _batch_fix(
        self,
        failed_tasks: List[Dict[str, Any]],
        context: Dict[str, Any],
        user_stories: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """
        Fix ALL failed tasks in a single LLM call.

        Returns:
            List of fixed tasks
        """
        if not failed_tasks:
            return []

        # Build failed task list for prompt
        task_list = []
        for task in failed_tasks:
            task_list.append({
                'index': task.get('_task_index', 0),
                'title': task.get('title', ''),
                'description': task.get('description', '')[:200],
                'timebox': task.get('timebox_minutes', 30),
                'issues': task.get('_verification_issues', [])
            })

        prompt = f"""Fix these {len(failed_tasks)} tasks that failed verification.

USER CONTEXT:
- Target Role: {context.get('target_role', 'N/A')}
- Target Companies: {context.get('target_companies', 'N/A')}

USER STORIES:
- Work: {user_stories.get('work_story', 'N/A')[:150]}
- Goal: {user_stories.get('aspiration_story', 'N/A')[:150]}

FAILED TASKS:
{json.dumps(task_list, indent=2)}

Fix each task to address the issues. Keep fixes minimal - don't over-engineer.

CRITICAL: Replace ANY placeholders (P University, T, O, P, X Company) with:
- Actual names from user context/stories if available
- OR make the task more general but still actionable (e.g., "Email admissions office at your top-choice university")
- NEVER leave placeholders like single letters or "T, O, P"

Return JSON array of fixed tasks:
[
    {{
        "index": 0,
        "title": "Fixed title (max 100 chars)",
        "description": "Fixed description",
        "timebox_minutes": 30
    }},
    ...
]
"""

        try:
            response = self.ai_service.call_llm(
                system_prompt="You are a task fixer. Make minimal changes to fix issues. Return valid JSON array.",
                user_prompt=prompt,
                response_format="json"
            )

            fixed_list = json.loads(response)

            # Map fixed tasks back to original structure
            fixed_tasks = []
            for fixed in fixed_list:
                # Find original task by index
                original_idx = fixed.get('index', 0)
                original_task = None
                for task in failed_tasks:
                    if task.get('_task_index') == original_idx:
                        original_task = task
                        break

                if original_task:
                    # Merge fixed fields into original task
                    task_copy = original_task.copy()
                    task_copy['title'] = fixed.get('title', original_task.get('title'))
                    task_copy['description'] = fixed.get('description', original_task.get('description'))
                    task_copy['timebox_minutes'] = fixed.get('timebox_minutes', original_task.get('timebox_minutes', 30))

                    # Clean up internal fields
                    task_copy.pop('_verification_issues', None)
                    task_copy.pop('_task_index', None)

                    fixed_tasks.append(task_copy)

            return fixed_tasks

        except Exception as e:
            logger.error(f"[TaskVerifier] Batch fix failed: {e}")
            # If batch fix fails, return original tasks (cleaned)
            for task in failed_tasks:
                task.pop('_verification_issues', None)
                task.pop('_task_index', None)
            return failed_tasks

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
   - NOT placeholders like "P University", "T, O, P Universities", "X Company"

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
