"""
Task Validator (Week 1 Day 6-7: Hybrid Task Generation Enhancement)

Validates quality of generated tasks to ensure they are:
1. Personalized (has user context, not generic)
2. Specific (clear target, not vague)
3. Actionable (clear verb, clear steps)
4. Time-bounded (has timebox estimate)
5. Not using generic template language

Scoring system:
- Each check = 20 points
- Total = 100 points
- Pass threshold: 80% (4/5 checks)
- Auto-reject threshold: 60% (3/5 checks) → regenerate

Use cases:
- Validate template-generated tasks (catch poor templates)
- Validate LLM-generated unique tasks (catch hallucinations)
- Validate custom tasks (catch rule-based errors)

Week 1 Day 6-7: Quality gate before tasks reach user.
"""

from typing import Dict, Tuple, List, Any
import re


class TaskValidator:
    """
    Validates task quality with 5-check system.

    Week 1 Day 6-7: Ensures all tasks (templates + custom + unique)
    meet quality standards before reaching user.
    """

    # Generic phrases that indicate poor personalization
    GENERIC_PHRASES = [
        'your university',
        'your school',
        'your program',
        'your field',
        'your goal',
        'your target',
        'research universities',
        'update your resume',
        'prepare for',
        'get ready for',
        'think about',
        'consider doing',
        '[your',
        '[insert',
        '[add',
        'TODO:',
        'PLACEHOLDER',
    ]

    # Action verbs that indicate clear actionability
    ACTION_VERBS = [
        'write', 'draft', 'create', 'build', 'design', 'develop',
        'research', 'analyze', 'compare', 'evaluate', 'assess',
        'email', 'contact', 'reach out', 'call', 'message',
        'register', 'apply', 'submit', 'upload', 'send',
        'schedule', 'book', 'arrange', 'plan', 'organize',
        'review', 'proofread', 'edit', 'revise', 'update',
        'calculate', 'gather', 'collect', 'prepare', 'compile',
        # Week 1 improvements: Add more action verbs
        'request', 'ask', 'brief', 'inform', 'notify', 'tell',
        'quantify', 'measure', 'track', 'count', 'estimate',
        'find', 'search', 'identify', 'locate', 'discover',
        'complete', 'finish', 'accomplish', 'achieve', 'execute',
        'improve', 'enhance', 'optimize', 'refine', 'polish',
    ]

    def __init__(self, context: Dict[str, Any] = None):
        """
        Initialize validator with user context.

        Args:
            context: Full personalization context from profile_extractor
        """
        self.context = context or {}

    def validate_task(self, task: Dict[str, Any]) -> Tuple[bool, int, List[str]]:
        """
        Validate task quality with 5-check system.

        Args:
            task: Task dictionary to validate

        Returns:
            Tuple of (is_valid, score_percentage, failure_reasons)
            - is_valid: True if score >= 80%
            - score_percentage: 0-100
            - failure_reasons: List of failed checks
        """
        checks = [
            self._check_has_user_context(task),
            self._check_is_specific(task),
            self._check_is_actionable(task),
            self._check_has_time_estimate(task),
            self._check_not_generic(task),
        ]

        # Calculate score
        passed_checks = sum(1 for passed, _ in checks if passed)
        score_percentage = (passed_checks / len(checks)) * 100

        # Collect failure reasons
        failure_reasons = [reason for passed, reason in checks if not passed]

        # Pass threshold: 80% (4/5 checks)
        is_valid = score_percentage >= 80

        return is_valid, int(score_percentage), failure_reasons

    def _check_has_user_context(self, task: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Check 1: Task has user-specific context (not generic).

        Looks for:
        - Specific university names (MIT, Stanford, not "your university")
        - Specific field names (Computer Science, not "your field")
        - Specific numbers (3.3 GPA, 200k users, not generic)
        - User's startup/project names
        """
        title = task.get('title', '').lower()
        description = task.get('description', '').lower()
        combined = f"{title} {description}"

        # Check for specific context markers
        has_specific_uni = any(uni.lower() in combined for uni in self.context.get('target_universities', []))
        has_specific_field = self.context.get('field', '').lower() in combined
        has_startup_name = self.context.get('startup_name', '').lower() in combined
        has_numbers = bool(re.search(r'\d+', combined))  # Any specific numbers

        # Must have at least 2 specific markers OR be a custom/unique task
        if task.get('source') in ['custom_generator', 'unique_generator']:
            # Custom/unique tasks are assumed to have context
            return True, ""

        if has_specific_uni or has_specific_field or has_startup_name or (has_numbers and len(combined) > 50):
            return True, ""

        return False, "Task lacks user-specific context (too generic)"

    def _check_is_specific(self, task: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Check 2: Task is specific (not vague).

        Vague tasks use phrases like:
        - "Research universities" (which universities?)
        - "Prepare for test" (which test? how?)
        - "Update resume" (what specifically?)

        Specific tasks:
        - "Research MIT's Computer Science Master's program admission requirements"
        - "Register for IELTS Academic test in Boston on April 15"
        - "Update resume with PathAI metrics (200k users, 99% uptime)"
        """
        title = task.get('title', '')

        # Check for vague phrases
        vague_phrases = [
            r'research\s+(some|any|a few)',
            r'prepare\s+for',
            r'get\s+ready',
            r'think\s+about',
            r'consider\s+\w+ing',
            r'look\s+into',
            r'explore\s+options',
        ]

        for pattern in vague_phrases:
            if re.search(pattern, title, re.IGNORECASE):
                return False, f"Task is too vague (found: {pattern})"

        # Check title length (specific tasks tend to be longer)
        if len(title) < 20:
            return False, "Task title too short (likely vague)"

        return True, ""

    def _check_is_actionable(self, task: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Check 3: Task is actionable (clear verb, clear steps).

        Actionable tasks:
        - Start with action verb
        - Have clear deliverable
        - Not just "think about" or "consider"
        """
        title = task.get('title', '').lower()

        # Check for action verb at start
        first_word = title.split()[0] if title else ''
        has_action_verb = any(verb in first_word for verb in self.ACTION_VERBS)

        if not has_action_verb:
            # Check if action verb appears in first 3 words
            first_three = ' '.join(title.split()[:3])
            has_action_verb = any(verb in first_three for verb in self.ACTION_VERBS)

        if not has_action_verb:
            return False, "Task lacks clear action verb (not actionable)"

        # Check for weak verbs that aren't really actionable
        weak_verbs = ['think', 'consider', 'explore', 'look into', 'maybe']
        if any(verb in title for verb in weak_verbs):
            return False, f"Task uses weak verb (not actionable)"

        return True, ""

    def _check_has_time_estimate(self, task: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Check 4: Task has time estimate (timebox_minutes).

        All tasks should have realistic time estimates:
        - Quick wins: 15-30 minutes
        - Standard tasks: 60-120 minutes
        - Complex tasks: 180+ minutes
        """
        timebox = task.get('timebox_minutes')

        if not timebox:
            return False, "Task missing timebox_minutes"

        # Check if timebox is realistic (not placeholder)
        if timebox <= 0 or timebox > 600:  # Max 10 hours
            return False, f"Task has unrealistic timebox: {timebox} minutes"

        return True, ""

    def _check_not_generic(self, task: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Check 5: Task doesn't use generic template language.

        Generic phrases to avoid:
        - "your university", "your school"
        - "[insert name]", "TODO:", "PLACEHOLDER"
        - "Research universities" (which universities?)
        """
        title = task.get('title', '').lower()
        description = task.get('description', '').lower()
        combined = f"{title} {description}"

        # Check for generic phrases
        for phrase in self.GENERIC_PHRASES:
            if phrase.lower() in combined:
                return False, f"Task uses generic language: '{phrase}'"

        # Check for placeholder brackets
        if re.search(r'\[.*?\]', combined):
            # Allow some valid brackets like [Part 1], [Week 1], or instructional brackets
            allowed_patterns = [
                r'\[(part|week|day|section)\s*\d+\]',  # [Part 1], [Week 2]
                r'\[.*?(name|email|city|company).*?\]',  # [Professor Name], [your email] - instructional
                r'\[specific\s+\w+\]',  # [specific achievement], [specific value]
            ]
            is_allowed = any(re.search(pattern, combined, re.IGNORECASE) for pattern in allowed_patterns)
            if not is_allowed:
                return False, "Task contains placeholder brackets"

        return True, ""

    def validate_batch(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate multiple tasks and return summary.

        Args:
            tasks: List of task dictionaries

        Returns:
            {
                'total': Total tasks,
                'passed': Tasks that passed (score >= 80%),
                'failed': Tasks that failed,
                'needs_regeneration': Tasks that need regeneration (score < 60%),
                'average_score': Average quality score,
                'failed_tasks': List of (task, score, reasons) for failed tasks
            }
        """
        results = []
        total = len(tasks)
        passed = 0
        failed = 0
        needs_regeneration = 0
        total_score = 0

        failed_tasks = []

        for task in tasks:
            is_valid, score, reasons = self.validate_task(task)
            results.append((task, is_valid, score, reasons))

            total_score += score

            if is_valid:
                passed += 1
            else:
                failed += 1
                failed_tasks.append((task, score, reasons))

                # Auto-reject threshold: 60%
                if score < 60:
                    needs_regeneration += 1

        average_score = total_score / total if total > 0 else 0

        return {
            'total': total,
            'passed': passed,
            'failed': failed,
            'needs_regeneration': needs_regeneration,
            'average_score': average_score,
            'failed_tasks': failed_tasks
        }


# Singleton instance
def create_task_validator(context: Dict[str, Any] = None) -> TaskValidator:
    """
    Factory function to create TaskValidator with context.

    Args:
        context: Full personalization context from profile_extractor

    Returns:
        TaskValidator instance
    """
    return TaskValidator(context)


def validate_task(task: Dict[str, Any], context: Dict[str, Any] = None) -> Tuple[bool, int, List[str]]:
    """
    Convenience function to validate single task.

    Args:
        task: Task dictionary
        context: Optional personalization context

    Returns:
        Tuple of (is_valid, score_percentage, failure_reasons)
    """
    validator = create_task_validator(context)
    return validator.validate_task(task)
