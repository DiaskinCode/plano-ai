"""
Plan Generation Service

Single source of truth for generating admission tasks.
Pipeline: shortlist → ingest requirements → compose tasks → cleanup old tasks
"""

import logging
import time
import uuid
from django.db import transaction
from django.utils import timezone

from university_recommender.models import UniversityShortlist
from requirements.services import ingest_user_requirements
from todos.task_composer import TaskComposer
from requirements.models import RequirementInstance
from todos.models import Todo

logger = logging.getLogger(__name__)


class PlanGenerationService:
    """
    Generate admission plan from shortlist.

    Pipeline:
    1. Get user's shortlist
    2. Ingest requirements (creates RequirementInstance)
    3. Compose tasks (creates Todo with dedupe_keys)
    4. Cleanup old tasks (using returned dedupe_keys)
    5. Calculate coverage
    """

    def __init__(self, user):
        self.user = user

    @transaction.atomic
    def generate_plan(self, track='direct', intake='', degree_level='', citizenship=''):
        """
        Generate admission plan.

        Returns:
            dict: {status, requirements_stats, tasks_stats, coverage, deadlines, trace}
        """
        # Generate trace ID for this run
        trace_id = str(uuid.uuid4())[:8]
        timings = {}
        logger.info(f"[{trace_id}] Starting plan generation for user {self.user.id}")

        # Count before
        instances_before = RequirementInstance.objects.filter(user=self.user).count()
        todos_before = Todo.objects.filter(user=self.user, is_auto_generated=True).count()
        logger.info(f"[{trace_id}] Before: {instances_before} instances, {todos_before} todos")

        # Get user profile fields used
        profile_fields = self._get_profile_fields()

        # Step 1: Get shortlist
        start = time.time()
        shortlist = UniversityShortlist.objects.filter(
            user=self.user
        ).select_related('university')
        timings['get_shortlist'] = int((time.time() - start) * 1000)

        if shortlist.count() == 0:
            return {
                'status': 'error',
                'error': 'No universities in shortlist',
                'coverage': {
                    'verified_percent': 0,
                    'assumed_percent': 0,
                    'plan_status': 'not_generated'
                }
            }

        logger.info(f"[{trace_id}] Shortlist: {shortlist.count()} universities")

        # Step 2: Ingest requirements
        start = time.time()
        logger.info(f"[{trace_id}] Step 1: Ingesting requirements...")
        requirements_stats = ingest_user_requirements(
            user=self.user,
            shortlist=shortlist
        )
        timings['ingest'] = int((time.time() - start) * 1000)
        logger.info(f"[{trace_id}] Ingested: {requirements_stats}")

        # Step 2.5: ✅ NEW: Evaluate requirements
        start = time.time()
        logger.info(f"[{trace_id}] Step 1.5: Evaluating requirement satisfaction...")
        requirement_instances = RequirementInstance.objects.filter(user=self.user)

        from requirements.services import evaluate_user_requirements
        evaluation_stats = evaluate_user_requirements(self.user, requirement_instances)
        logger.info(f"[{trace_id}] Evaluation: {evaluation_stats}")
        timings['evaluation'] = int((time.time() - start) * 1000)

        # Step 3: Verify instances created
        requirement_instances = RequirementInstance.objects.filter(user=self.user)
        instances_after = requirement_instances.count()

        logger.info(f"[{trace_id}] RequirementInstance: {instances_before} → {instances_after} (+{instances_after - instances_before})")

        if instances_after == 0:
            logger.error(f"[{trace_id}] No RequirementInstance created!")
            return {
                'status': 'error',
                'error': 'Requirement ingestion failed',
                'coverage': {
                    'verified_percent': 0,
                    'assumed_percent': 0,
                    'plan_status': 'not_generated'
                }
            }

        # Step 4: Compose tasks
        start = time.time()
        logger.info(f"[{trace_id}] Step 2: Composing tasks...")
        composer = TaskComposer(self.user)
        tasks_stats = composer.compose_tasks(requirement_instances, shortlist)
        timings['compose'] = int((time.time() - start) * 1000)
        logger.info(f"[{trace_id}] Composed: {tasks_stats}")

        # Count todos after compose
        todos_after_compose = Todo.objects.filter(user=self.user, is_auto_generated=True).count()
        logger.info(f"[{trace_id}] Todos after compose: {todos_before} → {todos_after_compose}")

        # Step 4.5: ✅ NEW - Apply AI enhancement to Todo records
        ai_task_enhancement_stats = None
        try:
            start = time.time()
            logger.info(f"[{trace_id}] Step 2.5: Applying AI task enhancement...")

            from todos.services.ai_task_enhancer import AITaskEnhancer
            ai_enhancer = AITaskEnhancer(self.user)

            # Get newly created/updated todos for enhancement
            new_todos = list(Todo.objects.filter(
                user=self.user,
                is_auto_generated=True
            ))

            ai_task_enhancement_stats = ai_enhancer.enhance_todos(
                todos=new_todos,
                shortlist=shortlist,
                requirement_instances=requirement_instances
            )

            logger.info(
                f"[{trace_id}] AI task enhancement: "
                f"{ai_task_enhancement_stats.get('enhanced', 0)} enhanced, "
                f"{ai_task_enhancement_stats.get('cached', 0)} cached, "
                f"cost: ${ai_task_enhancement_stats.get('cost', 0):.4f}"
            )
            timings['ai_task_enhancement'] = int((time.time() - start) * 1000)

        except Exception as e:
            logger.warning(f"[{trace_id}] AI task enhancement skipped: {e}")
            ai_task_enhancement_stats = None

        # Step 5: ✅ NEW - LLM Plan Enhancement (always runs)
        llm_enhancement = None
        try:
            from university_profile.models import UniversitySeekerProfile
            profile = UniversitySeekerProfile.objects.filter(user=self.user).first()

            # ✅ FIX: Always run AI enhancement, not just when additional_context exists
            start = time.time()
            logger.info(f"[{trace_id}] Step 2.5: LLM plan enhancement...")

            from ai.admission_plan_enhancer import AdmissionPlanEnhancer
            enhancer = AdmissionPlanEnhancer(self.user)

            # Build eligibility report from evaluation_stats
            eligibility_report = {
                'overall_status': 'eligible' if evaluation_stats.get('missing', 0) == 0 else 'partially_eligible',
                'critical_gaps': self._get_critical_gaps(requirement_instances)
            }

            llm_enhancement = enhancer.enhance_plan(
                shortlist=shortlist,
                eligibility_report=eligibility_report,
                requirement_instances=requirement_instances
            )

            logger.info(
                f"[{trace_id}] LLM enhancement: "
                f"{len(llm_enhancement.get('personalized_tasks', []))} tasks, "
                f"{len(llm_enhancement.get('alternative_paths', []))} paths, "
                f"cost: ${llm_enhancement.get('cost', 0):.4f}"
            )
            timings['llm_enhancement'] = int((time.time() - start) * 1000)

        except Exception as e:
            logger.warning(f"[{trace_id}] LLM enhancement skipped: {e}")
            llm_enhancement = None

        # Step 5: Cleanup using returned dedupe_keys
        start = time.time()
        dedupe_keys = tasks_stats.get('dedupe_keys', set())
        logger.info(f"[{trace_id}] Step 3: Cleaning up old tasks (keeping {len(dedupe_keys)})...")
        deleted_count = self._cleanup_old_tasks(dedupe_keys)
        timings['cleanup'] = int((time.time() - start) * 1000)
        logger.info(f"[{trace_id}] Deleted {deleted_count} old tasks")

        # Count todos after cleanup
        todos_final = Todo.objects.filter(user=self.user, is_auto_generated=True).count()
        logger.info(f"[{trace_id}] Todos final: {todos_final}")

        # Step 6: Calculate coverage
        start = time.time()
        coverage = self._calculate_coverage()
        timings['coverage'] = int((time.time() - start) * 1000)

        # Step 7: Get deadlines
        deadlines = self._get_deadlines()
        timings['total'] = sum(timings.values())

        logger.info(f"[{trace_id}] Complete. Timings: {timings}ms")

        return {
            'status': 'success',
            'trace_id': trace_id,
            'timings_ms': timings,
            'counts': {
                'instances_before': instances_before,
                'instances_after': instances_after,
                'todos_before': todos_before,
                'todos_after': todos_final,
                'deleted': deleted_count,
            },
            'profile_fields_used': profile_fields,
            'requirements_stats': requirements_stats,
            'evaluation_stats': evaluation_stats,
            'ai_task_enhancement': ai_task_enhancement_stats,  # ✅ NEW: AI task details enhancement
            'llm_enhancement': llm_enhancement,  # ✅ LLM-powered personalization
            'tasks_stats': {
                'created': tasks_stats['created'],
                'updated': tasks_stats['updated'],
                'deleted': deleted_count,
                'total': tasks_stats['total']
            },
            'coverage': coverage,
            'deadlines': deadlines
        }

    def _cleanup_old_tasks(self, current_dedupe_keys):
        """
        Delete old auto-generated tasks not in current plan.

        ✅ FIX: Uses dedupe_keys returned by TaskComposer, not DB query.

        Args:
            current_dedupe_keys: Set of dedupe_keys in current plan

        Returns:
            int: Number of deleted tasks
        """
        old_tasks = Todo.objects.filter(
            user=self.user,
            is_auto_generated=True
        ).exclude(
            dedupe_key__in=current_dedupe_keys  # ✅ Only keep current tasks
        )

        count = old_tasks.count()
        old_tasks.delete()
        return count

    def _calculate_coverage(self):
        """Calculate coverage from RequirementInstance."""
        instances = RequirementInstance.objects.filter(user=self.user)
        total = instances.count()

        if total == 0:
            return {
                'verified_percent': 0,
                'assumed_percent': 0,
                'plan_status': 'not_generated',
                'missing_count': 0
            }

        verified = instances.filter(
            verification_level__in=['official', 'vendor']
        ).count()

        assumed = instances.filter(
            verification_level='assumed'
        ).count()

        verified_percent = int((verified / total) * 100)
        assumed_percent = int(((verified + assumed) / total) * 100)
        plan_status = 'verified' if verified_percent >= 95 else 'draft'
        missing = instances.filter(status='unknown').count()

        return {
            'verified_percent': verified_percent,
            'assumed_percent': assumed_percent,
            'plan_status': plan_status,
            'missing_count': missing
        }

    def _get_deadlines(self):
        """Get upcoming deadlines from shortlist."""
        from datetime import datetime

        shortlist = UniversityShortlist.objects.filter(
            user=self.user
        ).select_related('university')

        upcoming = []

        for item in shortlist:
            uni = item.university

            if uni.early_decision_deadline:
                upcoming.append({
                    'date': uni.early_decision_deadline.strftime('%Y-%m-%d'),
                    'university': uni.short_name,
                    'university_name': uni.name,
                    'type': 'early_decision'
                })

            if uni.early_action_deadline:
                upcoming.append({
                    'date': uni.early_action_deadline.strftime('%Y-%m-%d'),
                    'university': uni.short_name,
                    'university_name': uni.name,
                    'type': 'early_action'
                })

            if uni.regular_decision_deadline:
                upcoming.append({
                    'date': uni.regular_decision_deadline.strftime('%Y-%m-%d'),
                    'university': uni.short_name,
                    'university_name': uni.name,
                    'type': 'regular'
                })

        # Filter upcoming deadlines
        upcoming = [
            d for d in upcoming
            if d['date'] >= datetime.now().strftime('%Y-%m-%d')
        ]
        upcoming.sort(key=lambda x: x['date'])

        if upcoming:
            return {
                'next_deadline': upcoming[0]['date'],
                'next_deadline_university': upcoming[0]['university_name']
            }

        return {
            'next_deadline': None,
            'next_deadline_university': None
        }

    def _get_profile_fields(self):
        """
        Get list of profile fields that are used in requirement checking.
        This helps with debugging - shows what data is actually being used.
        """
        fields = []

        try:
            from university_profile.models import UniversitySeekerProfile
            profile = UniversitySeekerProfile.objects.filter(user=self.user).first()

            if profile:
                # Check which test fields have values
                if hasattr(profile, 'ielts_score') and profile.ielts_score:
                    fields.append('ielts_score')
                if hasattr(profile, 'toefl_score') and profile.toefl_score:
                    fields.append('toefl_score')
                if hasattr(profile, 'sat_score') and profile.sat_score:
                    fields.append('sat_score')
                if hasattr(profile, 'act_score') and profile.act_score:
                    fields.append('act_score')
                if hasattr(profile, 'gpa') and profile.gpa:
                    fields.append('gpa')
                if hasattr(profile, 'education_path_strategy'):
                    fields.append('education_path_strategy')
                if hasattr(profile, 'citizenship') and profile.citizenship:
                    fields.append('citizenship')
                if hasattr(profile, 'date_of_birth'):
                    fields.append('date_of_birth')

        except Exception as e:
            logger.warning(f"Could not get profile fields: {e}")

        return fields

    def _get_critical_gaps(self, requirement_instances):
        """
        Get list of critical gaps from requirement instances.

        Used for LLM enhancement to understand what's blocking the user.

        Args:
            requirement_instances: QuerySet of RequirementInstance

        Returns:
            List of dicts with gap information
        """
        gaps = []

        for instance in requirement_instances:
            if instance.status == 'missing':
                gap = {
                    'gap': instance.requirement_key,
                    'solution': instance.notes or f"Complete {instance.requirement_key}"
                }
                if instance.university:
                    gap['university'] = instance.university.name
                gaps.append(gap)

        return gaps


def generate_admission_plan(user, track='direct', intake='', degree_level='', citizenship=''):
    """Generate admission plan for user."""
    service = PlanGenerationService(user)
    return service.generate_plan(track, intake, degree_level, citizenship)
