"""
Atomic Task Validator

Validates that tasks are truly atomic (single action, <60min, specific resource).
Rejects meta-tasks and can force breakdown using LLM if needed.

Phase 2, Day 2: Two-Tier Atomic Task Generation
"""

import logging
from typing import Dict, List, Tuple, Any

logger = logging.getLogger(__name__)


class AtomicValidator:
    """
    Validates atomicity of tasks and forces breakdown of meta-tasks.

    Atomic criteria:
    1. Single action (not "Research AND create")
    2. 15-60 minute timebox (max 90min)
    3. Specific resource (person name, URL, tool)
    4. Clear deliverable
    5. No meta-language ("develop strategy", "create plan")
    """

    # Meta-task indicators (reject if found)
    META_INDICATORS = [
        'develop plan',
        'create strategy',
        'build framework',
        'design system',
        'prepare for',  # Too vague
        'research and ',  # Multiple actions
        'write and ',  # Multiple actions
        'create and ',  # Multiple actions
        'develop and ',  # Multiple actions
    ]

    # Atomic indicators (good signs)
    ATOMIC_INDICATORS = [
        'visit',
        'email',
        'connect with',
        'read',
        'watch',
        'attend',
        'complete module',
        'draft',
        'update section',
        'add to calendar',
        'create spreadsheet',
    ]

    def __init__(self):
        """Initialize validator"""
        logger.info("[AtomicValidator] Initialized")

    def validate_task(self, task: Dict[str, Any]) -> Tuple[bool, int, List[str]]:
        """
        Validate if a task is atomic.

        Args:
            task: Task dictionary

        Returns:
            Tuple of (is_valid, score, reasons)
            - is_valid: True if task passes all atomic checks
            - score: 0-100 atomicity score
            - reasons: List of failure reasons (if any)
        """
        reasons = []
        score = 100

        # Check 1: Single action
        is_single_action, action_reasons = self._check_single_action(task)
        if not is_single_action:
            reasons.extend(action_reasons)
            score -= 30

        # Check 2: Reasonable timebox
        is_reasonable_time, time_reasons = self._check_timebox(task)
        if not is_reasonable_time:
            reasons.extend(time_reasons)
            score -= 25

        # Check 3: Specific resource
        has_resource, resource_reasons = self._check_specific_resource(task)
        if not has_resource:
            reasons.extend(resource_reasons)
            score -= 20

        # Check 4: Clear deliverable
        has_deliverable, deliverable_reasons = self._check_deliverable(task)
        if not has_deliverable:
            reasons.extend(deliverable_reasons)
            score -= 15

        # Check 5: No meta-language
        no_meta, meta_reasons = self._check_no_meta(task)
        if not no_meta:
            reasons.extend(meta_reasons)
            score -= 30  # Major penalty for meta-tasks

        is_valid = score >= 60  # Pass threshold
        return is_valid, max(0, score), reasons

    def _check_single_action(self, task: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Check if task represents a single action"""
        title = task.get('title', '').lower()
        description = task.get('description', '').lower()
        reasons = []

        # Multiple action indicators
        multi_action_words = [
            ' and then ',
            'first ... then',
            'step 1:',
            'step 2:',
            ', then ',
        ]

        for indicator in multi_action_words:
            if indicator in title or indicator in description:
                reasons.append(f"Multiple actions detected: '{indicator}'")
                return False, reasons

        return True, reasons

    def _check_timebox(self, task: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Check if timebox is reasonable for atomic task (15-90min)"""
        timebox = task.get('timebox_minutes', 0)
        reasons = []

        if timebox < 10:
            reasons.append(f"Timebox too short: {timebox}min (minimum 10min)")
            return False, reasons

        if timebox > 90:
            reasons.append(f"Timebox too long: {timebox}min (maximum 90min for atomic task)")
            return False, reasons

        return True, reasons

    def _check_specific_resource(self, task: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Check if task mentions specific resource (person, URL, tool)"""
        title = task.get('title', '')
        description = task.get('description', '')
        specific_resource = task.get('specific_resource', '')
        reasons = []

        # Generic placeholders (bad)
        generic_terms = [
            '[university name]',
            '[professor name]',
            '[company]',
            'a professor',
            'an advisor',
            'someone',
        ]

        for term in generic_terms:
            if term in title.lower() or term in description.lower():
                reasons.append(f"Generic placeholder found: '{term}' - needs specific name")
                return False, reasons

        # Check if specific resource is provided
        if specific_resource:
            # Has dedicated field
            return True, reasons

        # Check for URL patterns
        if 'http://' in description or 'https://' in description or '.com' in description or '.edu' in description:
            return True, reasons

        # Check for specific names (proper nouns often have capitals)
        # Simple heuristic: if title/description has words with capital letters mid-sentence
        import re
        if re.search(r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b', title + ' ' + description):
            # Likely a person name (e.g., "John Smith", "Barbara Liskov")
            return True, reasons

        reasons.append("No specific resource identified (need person name, URL, or tool)")
        return False, reasons

    def _check_deliverable(self, task: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Check if task has clear deliverable"""
        deliverable = task.get('deliverable', '')
        definition_of_done = task.get('definition_of_done', [])
        description = task.get('description', '')
        reasons = []

        # Deliverable explicitly provided
        if deliverable and len(deliverable) > 10:
            return True, reasons

        # Definition of done provided
        if definition_of_done and len(definition_of_done) > 0:
            return True, reasons

        # Check description for output indicators
        output_keywords = [
            'output:',
            'result:',
            'deliverable:',
            'you will have',
            'completed',
            'documented',
            'saved to',
        ]

        for keyword in output_keywords:
            if keyword in description.lower():
                return True, reasons

        reasons.append("No clear deliverable specified")
        return False, reasons

    def _check_no_meta(self, task: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Check for meta-task language"""
        title = task.get('title', '').lower()
        description = task.get('description', '').lower()
        reasons = []

        for indicator in self.META_INDICATORS:
            if indicator in title:
                reasons.append(f"Meta-task language in title: '{indicator}'")
                return False, reasons
            if indicator in description:
                reasons.append(f"Meta-task language in description: '{indicator}'")
                return False, reasons

        return True, reasons

    def validate_batch(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate a batch of tasks.

        Args:
            tasks: List of task dictionaries

        Returns:
            Validation results:
            {
                'total': 15,
                'passed': 12,
                'failed': 3,
                'atomicity_score': 85,
                'failed_tasks': [(task, score, reasons), ...]
            }
        """
        total = len(tasks)
        passed = 0
        failed = 0
        total_score = 0
        failed_tasks = []

        for task in tasks:
            is_valid, score, reasons = self.validate_task(task)
            total_score += score

            if is_valid:
                passed += 1
            else:
                failed += 1
                failed_tasks.append((task, score, reasons))

        avg_score = total_score / total if total > 0 else 0

        results = {
            'total': total,
            'passed': passed,
            'failed': failed,
            'atomicity_score': int(avg_score),
            'failed_tasks': failed_tasks
        }

        logger.info(f"[AtomicValidator] Batch validation: {passed}/{total} passed ({avg_score:.0f}% atomicity)")

        return results

    def force_atomic_breakdown(self, meta_task: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Force breakdown of a meta-task into atomic tasks using LLM.

        Args:
            meta_task: Task that failed atomicity validation

        Returns:
            List of 2-4 atomic tasks
        """
        logger.info(f"[AtomicValidator] Forcing atomic breakdown: {meta_task['title'][:60]}...")

        from ai.services import AIService

        ai_service = AIService(provider='openai')

        prompt = f"""This task is TOO HIGH-LEVEL (meta-task). Break it into 2-4 ATOMIC actions.

META-TASK:
{meta_task['title']}
{meta_task.get('description', '')}

TASK: Break this into 2-4 CONCRETE SINGLE ACTIONS.

Each action must:
- Be completable in ONE session (15-60 minutes)
- Be a SINGLE specific action (not a plan)
- Include specific resource (person, URL, tool)
- Have clear deliverable

Example breakdown:
Meta-task: "Develop networking strategy for investment banking"

Atomic tasks:
1. "List 10 people in your network who work in IB (save to spreadsheet)" (20min)
2. "Research 5 upcoming IB networking events in NYC (save dates to calendar)" (30min)
3. "Draft cold email template for IB alumni outreach (150 words)" (25min)
4. "Join 'Investment Banking Professionals' LinkedIn group and introduce yourself" (15min)

Return 2-4 atomic tasks as JSON array:
[
  {{
    "title": "Specific single action (max 100 chars)",
    "description": "Steps: 1. [specific action] 2. Output: [deliverable]",
    "timebox_minutes": 15-60,
    "priority": 3,
    "specific_resource": "Resource name",
    "deliverable": "Clear output"
  }}
]"""

        try:
            response = ai_service.call_llm(
                system_prompt="You are an expert task breakdown specialist that breaks meta-tasks into atomic tasks in JSON format.",
                user_prompt=prompt,
                response_format="json"
            )

            import json
            # Parse response
            response = response.strip()
            if response.startswith('```'):
                response = '\n'.join([line for line in response.split('\n') if not line.startswith('```')])

            atomic_tasks = json.loads(response)

            logger.info(f"[AtomicValidator] ✅ Broke down into {len(atomic_tasks)} atomic tasks")
            return atomic_tasks

        except Exception as e:
            logger.error(f"[AtomicValidator] Failed to force breakdown: {e}")
            return []


def create_atomic_validator() -> AtomicValidator:
    """Factory function to create AtomicValidator instance"""
    return AtomicValidator()
