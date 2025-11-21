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
import logging

logger = logging.getLogger(__name__)


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

    # ========== FAST PRE-VALIDATION METHODS (0 LLM calls) ==========

    # Meta-task patterns indicating non-atomic tasks
    META_TASK_PATTERNS = [
        r'\band\b.*\band\b',  # Multiple "and"s
        r'\bthen\b',
        r'\bfollowed by\b',
        r'\bafter that\b',
        r'\bnext\b.*\bthen\b',
        r'\bstep \d+\b',
        r'\bphase \d+\b',
        r'\bfirst\b.*\bthen\b.*\bfinally\b',
    ]

    # Specific indicators - task has concrete details
    SPECIFIC_PATTERNS = [
        r'https?://\S+',  # URLs
        r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b',  # Proper names (First Last)
        r'\b(?:Google|Microsoft|Apple|Amazon|Meta|Netflix|Stanford|MIT|Harvard|NYU)\b',
        r'\bpage(?:s)?\s+\d+',  # Page numbers
        r'\bchapter\s+\d+',  # Chapter numbers
        r'@\w+\.\w+',  # Email addresses
        r'\b\d{4}\s+report\b',  # Year reports (2024 report)
    ]

    def validate_and_fix_batch(
        self,
        tasks: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Fast pre-validation and auto-fix with 0 LLM calls.

        Returns:
            Tuple of (valid_tasks, rejected_tasks)
        """
        valid_tasks = []
        rejected_tasks = []
        fixed_count = 0

        for task in tasks:
            # First try to fix simple issues
            fixed_task = self.fix_simple_issues(task)
            if fixed_task != task:
                fixed_count += 1
                task = fixed_task

            # Then validate with quick check
            is_valid, issues = self.quick_validate(task)

            if is_valid:
                valid_tasks.append(task)
            else:
                task['validation_issues'] = issues
                rejected_tasks.append(task)

        logger.info(f"[TaskValidator] Pre-validation: {len(valid_tasks)} valid, "
                   f"{len(rejected_tasks)} rejected, {fixed_count} auto-fixed")

        return valid_tasks, rejected_tasks

    def quick_validate(self, task: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Quick validation with rule-based checks (0 LLM calls).

        More lenient than full validation - just catches obvious issues.

        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        title = task.get('title', '')
        description = task.get('description', '')
        timebox = task.get('timebox_minutes', 30)
        full_text = f"{title} {description}".lower()

        # Check 1: Title length
        if len(title) < 10:
            issues.append("Title too short (< 10 chars)")
        if len(title) > 150:
            issues.append("Title too long (> 150 chars)")

        # Check 2: Timebox range
        if timebox < 10:
            issues.append(f"Timebox too short ({timebox} min < 10 min)")
        if timebox > 120:
            issues.append(f"Timebox too long ({timebox} min > 120 min)")

        # Check 3: Meta-task patterns (non-atomic)
        for pattern in self.META_TASK_PATTERNS:
            if re.search(pattern, full_text, re.IGNORECASE):
                issues.append(f"Contains meta-task pattern: {pattern}")
                break  # One is enough

        # Check if has specific resource (makes task more likely valid)
        has_specific = any(re.search(p, f"{title} {description}", re.IGNORECASE)
                         for p in self.SPECIFIC_PATTERNS)

        # More lenient - only reject if has multiple issues AND no specifics
        is_valid = len(issues) == 0 or (len(issues) == 1 and has_specific)

        return is_valid, issues

    def fix_simple_issues(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Auto-fix simple issues without LLM.

        Fixes:
        - Timebox capping (15-60 min)
        - Title trimming
        - Remove common filler words
        """
        task = task.copy()

        # Fix timebox
        timebox = task.get('timebox_minutes', 30)
        if timebox < 10:
            task['timebox_minutes'] = 15  # Minimum 15 min
        elif timebox > 90:
            task['timebox_minutes'] = 60  # Cap at 60 min

        # Fix title
        title = task.get('title', '')

        # Trim whitespace
        title = ' '.join(title.split())

        # Remove common filler starts
        filler_starts = [
            'Task: ', 'Action: ', 'TODO: ', 'Do: ',
            'Complete: ', 'Finish: ', 'Work on: '
        ]
        for filler in filler_starts:
            if title.startswith(filler):
                title = title[len(filler):]

        # Capitalize first letter
        if title and title[0].islower():
            title = title[0].upper() + title[1:]

        # Truncate if too long
        if len(title) > 120:
            title = title[:117] + '...'

        task['title'] = title

        return task


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
