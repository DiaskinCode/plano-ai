"""
Task Executor - Two-Tier Atomic Task Generation Orchestrator

Coordinates the entire two-tier task generation process:
- Tier 1: Generate 5 milestones
- Tier 2: Break each milestone into 5-6 atomic tasks
- Validation: Ensure all tasks are truly atomic

Phase 2, Day 1-3: Two-Tier Atomic Task Generation
"""

import logging
from typing import Dict, List, Any
from decimal import Decimal

logger = logging.getLogger(__name__)


class TaskExecutor:
    """
    Orchestrates two-tier atomic task generation.

    Flow:
    1. Generate 5 milestones (MilestoneGenerator)
    2. For each milestone, generate 5-6 atomic tasks (AtomicTaskGenerator)
    3. Validate all tasks are atomic (AtomicValidator)
    4. Fix any non-atomic tasks
    5. Return 25-30 validated atomic tasks

    Example:
        executor = TaskExecutor(user, profile, context)
        tasks = executor.execute_with_milestones(goalspec)
        # Returns 25-30 atomic tasks (vs 12-18 meta-tasks before)
    """

    def __init__(self, user, user_profile, context: Dict[str, Any]):
        """
        Initialize TaskExecutor.

        Args:
            user: User instance
            user_profile: UserProfile instance
            context: Personalization context from profile_extractor
        """
        self.user = user
        self.profile = user_profile
        self.context = context

        # Initialize components
        from ai.milestone_generator import create_milestone_generator
        from ai.atomic_task_generator import create_atomic_task_generator
        from ai.atomic_validator import create_atomic_validator
        from ai.task_enricher import create_task_enricher
        from ai.story_extractor import create_story_extractor
        from ai.task_verifier import create_task_verifier

        self.milestone_gen = create_milestone_generator()
        self.atomic_gen = create_atomic_task_generator()
        self.validator = create_atomic_validator()
        self.enricher = create_task_enricher(use_web_research=True)  # Phase 3: Enrichment
        self.story_extractor = create_story_extractor()  # Phase 3: Story extraction
        self.task_verifier = create_task_verifier()  # Phase 3: Quality verification

        logger.info("[TaskExecutor] Initialized with two-tier generation + stories + verification system")

    def execute_with_milestones(
        self,
        goalspec,
        days_ahead: int = 90
    ) -> List[Dict[str, Any]]:
        """
        Execute two-tier atomic task generation.

        Args:
            goalspec: GoalSpec instance
            days_ahead: Days until goal deadline (for timeline calculation)

        Returns:
            List of 25-30 atomic task dictionaries
        """
        logger.info(f"[TaskExecutor] ========== TWO-TIER GENERATION START ==========")
        logger.info(f"[TaskExecutor] Goal: {goalspec.title}")
        logger.info(f"[TaskExecutor] Timeline: {days_ahead} days")

        # Calculate timeline in weeks
        timeline_weeks = max(4, days_ahead // 7)

        # === PHASE 0: EXTRACT USER STORIES ===
        logger.info(f"\n[TaskExecutor] === PHASE 0: STORY EXTRACTION ===")
        self.user_stories = self.story_extractor.extract_stories(self.profile, goalspec)
        logger.info(f"[TaskExecutor] ✅ Extracted {len(self.user_stories)} user stories for personalization")

        # === TIER 1: GENERATE MILESTONES ===
        logger.info(f"\n[TaskExecutor] === TIER 1: MILESTONE GENERATION ===")
        milestones = self.milestone_gen.generate_milestones(
            goalspec=goalspec,
            user_profile=self.profile,
            context=self.context,
            timeline_weeks=timeline_weeks,
            user_stories=self.user_stories
        )

        if not milestones:
            logger.error("[TaskExecutor] Milestone generation failed - falling back to empty list")
            return []

        logger.info(f"[TaskExecutor] ✅ Generated {len(milestones)} milestones")

        # === TIER 2: GENERATE ATOMIC TASKS FOR EACH MILESTONE ===
        logger.info(f"\n[TaskExecutor] === TIER 2: ATOMIC TASK GENERATION ===")
        all_tasks = []
        milestone_count = 0

        for idx, milestone in enumerate(milestones, 1):
            logger.info(f"\n[TaskExecutor] Milestone {idx}/{len(milestones)}: {milestone['title'][:60]}...")

            # Generate atomic tasks for this milestone
            atomic_tasks = self.atomic_gen.generate_atomic_tasks(
                milestone=milestone,
                goalspec=goalspec,
                user_profile=self.profile,
                context=self.context,
                user_stories=self.user_stories
            )

            if atomic_tasks:
                # Add milestone metadata and scheduling to each task
                from datetime import date, timedelta
                today = date.today()

                for task_idx, task in enumerate(atomic_tasks, 1):
                    task['milestone_title'] = milestone['title']
                    task['milestone_index'] = idx

                    # Smart scheduling: spread tasks across days
                    # Each milestone gets ~2 weeks, tasks within milestone spread every 2 days
                    base_offset = (idx - 1) * 14  # 2 weeks per milestone
                    task_offset = (task_idx - 1) * 2  # 2 days between tasks
                    scheduled_date = today + timedelta(days=base_offset + task_offset)
                    task['scheduled_date'] = scheduled_date.strftime('%Y-%m-%d')

                all_tasks.extend(atomic_tasks)
                milestone_count += 1
                logger.info(f"[TaskExecutor] ✅ Milestone {idx}: {len(atomic_tasks)} atomic tasks")
            else:
                logger.warning(f"[TaskExecutor] ⚠️  Milestone {idx}: No tasks generated")

        logger.info(f"\n[TaskExecutor] Generated {len(all_tasks)} tasks from {milestone_count} milestones")

        if not all_tasks:
            logger.error("[TaskExecutor] No tasks generated from any milestone")
            return []

        # === PHASE 3: ENRICH WITH REAL DATA ===
        logger.info(f"\n[TaskExecutor] === PHASE 3: ENRICHMENT WITH REAL DATA ===")
        all_tasks = self.enricher.enrich_tasks(
            tasks=all_tasks,
            goalspec=goalspec,
            user_profile=self.profile,
            context=self.context
        )
        enriched_count = sum(1 for t in all_tasks if t.get('enriched', False))
        logger.info(f"[TaskExecutor] ✅ Enriched {enriched_count}/{len(all_tasks)} tasks with real URLs and data")

        # === PHASE 4: VERIFY & FIX TASKS ===
        logger.info(f"\n[TaskExecutor] === PHASE 4: QUALITY VERIFICATION ===")
        tasks_before_verify = len(all_tasks)
        all_tasks = self.task_verifier.verify_and_fix(
            tasks=all_tasks,
            context=self.context,
            user_stories=self.user_stories
        )
        logger.info(f"[TaskExecutor] ✅ Verified {len(all_tasks)}/{tasks_before_verify} tasks passed quality checks")

        # === VALIDATION: ENSURE ATOMICITY ===
        logger.info(f"\n[TaskExecutor] === VALIDATION: ATOMICITY CHECK ===")
        validation_results = self.validator.validate_batch(all_tasks)

        logger.info(f"[TaskExecutor] Validation results:")
        logger.info(f"   Total tasks: {validation_results['total']}")
        logger.info(f"   Passed: {validation_results['passed']} ({validation_results['passed']/validation_results['total']*100:.0f}%)")
        logger.info(f"   Failed: {validation_results['failed']}")
        logger.info(f"   Atomicity Score: {validation_results['atomicity_score']}%")

        # Fix failed tasks if any
        if validation_results['failed'] > 0:
            logger.info(f"\n[TaskExecutor] === FIXING NON-ATOMIC TASKS ===")
            all_tasks = self._fix_non_atomic_tasks(all_tasks, validation_results)

        # === DEDUPLICATION ===
        logger.info(f"\n[TaskExecutor] === DEDUPLICATION ===")
        tasks_before = len(all_tasks)
        all_tasks = self._deduplicate_tasks(all_tasks)
        if len(all_tasks) < tasks_before:
            logger.info(f"[TaskExecutor] Removed {tasks_before - len(all_tasks)} duplicate tasks")

        # === FINAL RESULTS ===
        logger.info(f"\n[TaskExecutor] ========== TWO-TIER GENERATION COMPLETE ==========")
        logger.info(f"[TaskExecutor] Final task count: {len(all_tasks)} atomic tasks")
        logger.info(f"[TaskExecutor] Atomicity score: {validation_results['atomicity_score']}%")

        return all_tasks

    def _fix_non_atomic_tasks(
        self,
        tasks: List[Dict[str, Any]],
        validation_results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Fix non-atomic tasks by breaking them down or removing them.

        Args:
            tasks: Original task list
            validation_results: Validation results from validator

        Returns:
            Fixed task list with only atomic tasks
        """
        fixed_tasks = []
        failed_tasks = validation_results.get('failed_tasks', [])

        # Create set of failed task titles for quick lookup
        failed_titles = {task['title'] for task, _, _ in failed_tasks}

        for task in tasks:
            if task['title'] in failed_titles:
                # Try to fix this task
                logger.info(f"[TaskExecutor] Attempting to fix non-atomic task: {task['title'][:60]}...")

                # Force breakdown using validator
                atomic_breakdown = self.validator.force_atomic_breakdown(task)

                if atomic_breakdown and len(atomic_breakdown) > 0:
                    logger.info(f"[TaskExecutor] ✅ Broke down into {len(atomic_breakdown)} atomic tasks")
                    fixed_tasks.extend(atomic_breakdown)
                else:
                    logger.warning(f"[TaskExecutor] ⚠️  Could not fix task, skipping: {task['title'][:60]}...")
            else:
                # Task passed validation, keep it
                fixed_tasks.append(task)

        return fixed_tasks

    def _deduplicate_tasks(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicate or very similar tasks.

        Args:
            tasks: Task list

        Returns:
            Deduplicated task list
        """
        if not tasks:
            return tasks

        from difflib import SequenceMatcher

        def similar(a: str, b: str) -> float:
            """Calculate similarity ratio between two strings."""
            return SequenceMatcher(None, a.lower(), b.lower()).ratio()

        deduplicated = []
        seen_titles = []

        for task in tasks:
            title = task.get('title', '')
            is_duplicate = False

            # Check if title is similar to any seen title
            for seen_title in seen_titles:
                if similar(title, seen_title) > 0.85:  # 85% similarity threshold
                    logger.info(f"[TaskExecutor] 🔁 Duplicate detected: {title[:60]}...")
                    is_duplicate = True
                    break

            if not is_duplicate:
                deduplicated.append(task)
                seen_titles.append(title)

        removed_count = len(tasks) - len(deduplicated)
        if removed_count > 0:
            logger.info(f"[TaskExecutor] Removed {removed_count} duplicate tasks")

        return deduplicated


def create_task_executor(user, user_profile, context: Dict[str, Any]) -> TaskExecutor:
    """
    Factory function to create TaskExecutor instance.

    Args:
        user: User instance
        user_profile: UserProfile instance
        context: Personalization context from profile_extractor

    Returns:
        TaskExecutor instance
    """
    return TaskExecutor(user, user_profile, context)


def execute_two_tier_generation(
    user,
    user_profile,
    context: Dict[str, Any],
    goalspec,
    days_ahead: int = 90
) -> List[Dict[str, Any]]:
    """
    Convenience function to execute two-tier atomic task generation.

    Args:
        user: User instance
        user_profile: UserProfile instance
        context: Personalization context
        goalspec: GoalSpec instance
        days_ahead: Days until deadline

    Returns:
        List of 25-30 atomic tasks
    """
    executor = create_task_executor(user, user_profile, context)
    return executor.execute_with_milestones(goalspec, days_ahead)
