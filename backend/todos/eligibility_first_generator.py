"""
Eligibility-First Task Generator

Generates tasks based on eligibility check results:
1. Missing profile data → Profile completion tasks (blockers)
2. Eligibility gaps → Gap-closure tasks (blockers)
3. No blockers → Application tasks (specific to each university)

CRITICAL: Every auto-generated task MUST have a dedupe_key for idempotency.
API validation: If task lacks dedupe_key, return 500 error.
"""

from datetime import datetime, timedelta, date
from typing import List, Dict, Optional
from django.utils import timezone
from django.db import transaction

from university_database.models import University, CountryRequirement
from university_profile.models import UniversitySeekerProfile
from university_recommender.eligibility_checker_v2 import (
    EligibilityCheckerV2,
    EligibilityGap,
    EligibilityResult,
)
from .models import Todo


class EligibilityFirstGenerator:
    """
    Eligibility-first task generator.

    Layer 1: Missing profile data → Blocker tasks
    Layer 2: Eligibility gaps → Gap-closure tasks
    Layer 3: No blockers → Application tasks
    """

    def __init__(self, user):
        self.user = user
        self.profile = UniversitySeekerProfile.objects.filter(user=user).first()
        self.checker = EligibilityCheckerV2()

        # Build country requirement cache for performance
        self.country_req_cache = {
            req.country: req
            for req in CountryRequirement.objects.all()
        }
        self.checker.country_req_cache = self.country_req_cache

    def generate_for_shortlist(
        self,
        universities: List[University],
        strategy: str = 'direct'
    ) -> Dict:
        """
        Generate tasks for a shortlist of universities.

        Args:
            universities: List of University objects
            strategy: User's chosen path ('direct', 'foundation', 'change_shortlist')

        Returns:
            Dict with results including created/updated/deleted task counts
        """
        if not self.profile:
            return {
                'error': 'Please complete your university profile first',
                'status': 'error'
            }

        # Update user's strategy
        self.profile.education_path_strategy = strategy
        self.profile.eligibility_checked_at = timezone.now()
        self.profile.save(update_fields=['education_path_strategy', 'eligibility_checked_at'])

        # Check eligibility for all universities
        eligibility_results = self.checker.check_eligibility_for_shortlist(
            self.profile, universities, track=strategy
        )

        # Determine overall status
        all_blockers = []
        all_gaps = []
        eligible_unis = []

        for uni_name, result in eligibility_results.items():
            all_blockers.extend(result.blockers)
            all_gaps.extend(result.gaps)
            if not result.blockers:
                eligible_unis.append(uni_name)

        # Set overall eligibility status
        if all_blockers:
            overall_status = 'not_eligible'
        elif any(g.gap_type != 'missing_data' for g in all_gaps):
            overall_status = 'partially_eligible'
        else:
            overall_status = 'eligible'

        self.profile.overall_eligibility_status = overall_status
        self.profile.save(update_fields=['overall_eligibility_status'])

        # Generate tasks based on status
        all_new_tasks = []
        all_new_dedupe_keys = set()

        # Layer 1: Missing data tasks (always first)
        missing_data_tasks = self._generate_missing_data_tasks(all_gaps)
        all_new_tasks.extend(missing_data_tasks)
        all_new_dedupe_keys.update(t['dedupe_key'] for t in missing_data_tasks)

        # Layer 2: Gap tasks (if any blockers exist)
        if all_blockers:
            gap_tasks = self._generate_gap_tasks(all_blockers)
            all_new_tasks.extend(gap_tasks)
            all_new_dedupe_keys.update(t['dedupe_key'] for t in gap_tasks)

        # Layer 3: Application tasks (ONLY if no blockers)
        elif not all_blockers:
            app_tasks = self._generate_application_tasks(eligible_unis, eligibility_results)
            all_new_tasks.extend(app_tasks)
            all_new_dedupe_keys.update(t['dedupe_key'] for t in app_tasks)

        # Validate all tasks have dedupe_key
        for task in all_new_tasks:
            if not task.get('dedupe_key'):
                raise ValueError(f"CRITICAL: Task '{task.get('title')}' missing dedupe_key. This should never happen.")

        # Idempotent update: Delete old auto-generated tasks not in new list
        with transaction.atomic():
            # Get existing auto-generated tasks for this user
            existing_tasks = Todo.objects.filter(
                user=self.user,
                is_auto_generated=True
            )

            # Delete tasks not in our new list
            existing_dedupe_keys = set(
                existing_tasks.filter(
                    dedupe_key__in=all_new_dedupe_keys
                ).values_list('dedupe_key', flat=True)
            )

            # Delete tasks that are no longer relevant
            tasks_to_delete = existing_tasks.exclude(
                dedupe_key__in=all_new_dedupe_keys
            )
            deleted_count = tasks_to_delete.count()
            tasks_to_delete.delete()

            # Create or update tasks
            created_count = 0
            updated_count = 0

            for task_data in all_new_tasks:
                todo, created = Todo.objects.update_or_create(
                    user=self.user,
                    dedupe_key=task_data['dedupe_key'],
                    defaults=task_data
                )
                if created:
                    created_count += 1
                else:
                    updated_count += 1

        return {
            'status': 'success',
            'overall_eligibility': overall_status,
            'eligible_universities': eligible_unis,
            'blockers_count': len(all_blockers),
            'tasks_created': created_count,
            'tasks_updated': updated_count,
            'tasks_deleted': deleted_count,
            'total_tasks': created_count + updated_count,
            'strategy': strategy,
            'eligibility_summary': self._format_eligibility_summary(eligibility_results)
        }

    def _generate_missing_data_tasks(self, gaps: List[EligibilityGap]) -> List[Dict]:
        """Generate tasks for missing profile data"""
        tasks = []
        missing_data_gaps = [g for g in gaps if g.gap_type == 'missing_data']

        for gap in missing_data_gaps:
            for task_title in gap.resolution_tasks:
                dedupe_key = f"missing_data_{task_title.lower().replace(' ', '_')}"

                tasks.append({
                    'user': self.user,
                    'title': task_title,
                    'description': gap.description,
                    'scheduled_date': timezone.now().date(),
                    'priority': 3,  # High priority
                    'status': 'ready',
                    'source': 'user_missing_data',
                    'requirement_type': 'eligibility_gap',
                    'dedupe_key': dedupe_key,
                    'reason': gap.description,
                    'is_blocker': True,
                    'is_auto_generated': True,
                    'task_level': 'action',
                    'university': None,  # Profile tasks aren't uni-specific
                    'university_deadline': None,
                    'due_date': None,
                    'alternative_path': '',
                })

        return tasks

    def _generate_gap_tasks(self, blockers: List[EligibilityGap]) -> List[Dict]:
        """Generate tasks to close eligibility gaps"""
        tasks = []

        for gap in blockers:
            # Skip missing data gaps (handled separately)
            if gap.gap_type == 'missing_data':
                continue

            for task_title in gap.resolution_tasks:
                # Generate dedupe key that's unique per user + gap + task
                dedupe_key = f"gap_{gap.university_related or 'global'}_{gap.gap_type}_{task_title.lower().replace(' ', '_')[:50]}"

                # Get university if gap is uni-specific
                university = None
                uni_deadline = None
                if gap.university_related:
                    try:
                        university = University.objects.get(short_name=gap.university_related)
                        uni_deadline = university.get_primary_deadline()
                    except University.DoesNotExist:
                        pass

                tasks.append({
                    'user': self.user,
                    'title': task_title,
                    'description': gap.description,
                    'scheduled_date': timezone.now().date() + timedelta(days=1),
                    'priority': 3,  # High priority
                    'status': 'ready',
                    'source': 'university_rule',
                    'requirement_type': 'eligibility_gap',
                    'dedupe_key': dedupe_key,
                    'reason': f"{gap.title}: {gap.current_value} vs {gap.required_value}",
                    'is_blocker': gap.is_blocker,
                    'alternative_path': gap.alternative_path,
                    'is_auto_generated': True,
                    'task_level': 'action',
                    'university': university,
                    'university_deadline': uni_deadline,
                    'due_date': None,  # Gap tasks don't have specific deadlines
                })

        return tasks

    def _generate_application_tasks(
        self,
        eligible_unis: List[str],
        eligibility_results: Dict[str, EligibilityResult]
    ) -> List[Dict]:
        """
        Generate application tasks for eligible universities.

        IMPORTANT: Handles both 'direct' and 'foundation' tracks
        - Foundation track: Generates foundation-specific tasks
        - Direct track: Generates standard application tasks

        Only generates tasks if NO blockers exist.
        """
        tasks = []
        today = timezone.now().date()

        for uni_name in eligible_unis:
            try:
                university = University.objects.get(short_name=uni_name)
            except University.DoesNotExist:
                continue

            result = eligibility_results[uni_name]
            deadline = university.get_primary_deadline() or (today + timedelta(days=90))

            # Calculate due date with buffer (2 weeks before deadline)
            due_date = deadline - timedelta(days=14)

            # Get country requirements for defaults
            country_req = self.country_req_cache.get(university.location_country)

            # GENERATE DIFFERENT TASKS BASED ON TRACK
            if result.track == 'foundation':
                # Foundation track: Generate foundation-specific tasks
                task_sequence = self._get_foundation_task_sequence(
                    university, country_req, deadline, due_date
                )
            else:
                # Direct track: Generate standard application tasks
                task_sequence = self._get_application_task_sequence(
                    university, country_req, deadline, due_date
                )

            for i, task_info in enumerate(task_sequence):
                # Calculate scheduled date (stagger tasks)
                days_offset = i * 7  # One task per week
                scheduled_date = today + timedelta(days=days_offset)

                dedupe_key = f"{'foundation' if result.track == 'foundation' else 'app'}_{uni_name}_{task_info['type'].lower().replace(' ', '_')}"

                tasks.append({
                    'user': self.user,
                    'title': f"{university.short_name.title()}: {task_info['title']}",
                    'description': task_info['description'],
                    'scheduled_date': scheduled_date,
                    'priority': 3 if task_info.get('critical') else 2,
                    'status': 'ready',
                    'source': task_info.get('source', 'university_rule'),
                    'requirement_type': task_info.get('requirement_type', 'foundation' if result.track == 'foundation' else 'application'),
                    'dedupe_key': dedupe_key,
                    'reason': task_info.get('reason', ''),
                    'is_blocker': False,
                    'is_auto_generated': True,
                    'task_level': 'action',
                    'university': university,
                    'university_deadline': deadline,
                    'due_date': due_date,
                    'alternative_path': '',
                })

        return tasks

    def _get_foundation_task_sequence(
        self,
        university: University,
        country_req: Optional[CountryRequirement],
        deadline: date,
        due_date: date
    ) -> List[Dict]:
        """
        Get foundation track specific task sequence.

        These tasks prepare user for foundation year program,
        NOT direct bachelor's application.
        """
        foundation_settings = university.get_foundation_settings(self.country_req_cache)
        duration_years = foundation_settings.get('duration', 1.0)

        tasks = []

        # Task 1: Research Foundation Programs
        tasks.append({
            'type': 'foundation_research',
            'title': f'Research Foundation Programs for {university.name}',
            'description': f'Find and compare foundation year programs that lead to {university.name} admission. Duration: {duration_years} year(s)',
            'critical': True,
            'reason': f'Foundation year required for {university.name} admission',
            'source': 'country_rule',
            'requirement_type': 'foundation',
        })

        # Task 2: Check Foundation Application Deadlines
        tasks.append({
            'type': 'foundation_deadline',
            'title': f'Check Foundation Application Deadline',
            'description': f'Foundation programs often have different deadlines than direct admission. Find the deadline for {university.name} foundation program.',
            'critical': True,
            'reason': 'Foundation applications typically close earlier than direct admission',
            'source': 'university_rule',
            'requirement_type': 'foundation',
        })

        # Task 3: Foundation Application Documents
        tasks.append({
            'type': 'foundation_documents',
            'title': f'Prepare Foundation Application Documents',
            'description': f'Gather transcripts, reference letters, and personal statement for foundation program application to {university.name}',
            'critical': True,
            'reason': 'Foundation application requires similar documents to bachelor\'s application',
            'source': 'university_rule',
            'requirement_type': 'foundation',
        })

        # Task 4: Language Test (if needed)
        if university.min_ielts_score:
            tasks.append({
                'type': 'foundation_ielts',
                'title': f'IELTS for Foundation Program',
                'description': f'Ensure IELTS score meets foundation program requirement ({university.min_ielts_score}). Foundation programs may have lower requirements than direct admission.',
                'critical': True,
                'reason': f'Foundation program requires IELTS {university.min_ielts_score}',
                'source': 'university_rule',
                'requirement_type': 'foundation',
            })

        # Task 5: Apply to Foundation Program
        tasks.append({
            'type': 'foundation_apply',
            'title': f'Submit Foundation Program Application',
            'description': f'Complete and submit foundation program application for {university.name}. Deadline: {deadline}',
            'critical': True,
            'reason': f'Foundation application required before bachelor\'s admission',
            'source': 'university_rule',
            'requirement_type': 'foundation',
        })

        return tasks

    def _get_application_task_sequence(
        self,
        university: University,
        country_req: Optional[CountryRequirement],
        deadline: date,
        due_date: date
    ) -> List[Dict]:
        """
        Get the standard application task sequence for a university.

        Returns ordered list of tasks based on:
        - University specific requirements
        - Country defaults (if uni doesn't specify)

        IMPORTANT: Tracks 'source' to distinguish between:
        - 'university_rule': Explicitly specified by university
        - 'country_default': Using country default (assumed)
        """
        tasks = []

        # Task 1: Create Application Portal Account
        portal_type = university.application_portal or (country_req.application_system if country_req else 'Unknown')
        tasks.append({
            'type': 'portal_account',
            'title': f'Create {portal_type} Account',
            'description': f'Create your application account for {university.name}. Portal: {portal_type}',
            'critical': True,
            'source': 'university_rule',
        })

        # Task 2: Prepare Transcripts
        tasks.append({
            'type': 'transcripts',
            'title': 'Request Official Transcripts',
            'description': f'Contact your school to request official transcripts for {university.name}',
            'critical': True,
            'reason': 'Required by all universities',
            'source': 'university_rule',
        })

        # Task 3: Letters of Recommendation
        num_recs = university.num_recommendations
        source = 'university_rule'
        if num_recs is None:
            # Fall back to country default
            num_recs = country_req.default_num_recommendations if country_req else 2
            source = 'country_default'

        if num_recs and num_recs > 0:
            tasks.append({
                'type': 'recommendations',
                'title': f'Secure {num_recs} Recommendation Letter{"s" if num_recs > 1 else ""}',
                'description': f'Request letters from {num_recs} teacher{"s" if num_recs > 1 else ""} who can speak to your academic abilities',
                'critical': True,
                'reason': f'{university.name} requires {num_recs} recommendation{"s" if num_recs > 1 else ""}' + (' (country default)' if source == 'country_default' else ''),
                'source': source,
            })

        # Task 4: Essay (if required)
        essay_required = university.essay_required
        source = 'university_rule'
        if essay_required is None:
            # Fall back to country default
            essay_required = country_req.default_essay_required if country_req else True
            source = 'country_default'

        if essay_required:
            prompt = university.essay_prompt or 'Follow essay prompts in application portal'
            tasks.append({
                'type': 'essay',
                'title': f'Write Essay: {prompt[:50]}...' if len(prompt) > 50 else f'Write Essay: {prompt}',
                'description': f'Write your essay for {university.name}. Prompt: {prompt}',
                'critical': True,
                'reason': f'{university.name} requires an essay' + (' (country default)' if source == 'country_default' else ''),
                'source': source,
            })

        # Task 5: Test Scores (if user has them)
        if self.profile.ielts_score:
            tasks.append({
                'type': 'test_scores',
                'title': 'Submit IELTS Scores',
                'description': f'Submit your IELTS score ({self.profile.ielts_score}) to {university.name}',
                'critical': True,
                'source': 'university_rule',
            })

        # Task 6: Review and Submit
        tasks.append({
            'type': 'submit',
            'title': f'Review and Submit Application (Due: {due_date})',
            'description': f'Review your application and submit before the deadline ({deadline})',
            'critical': True,
            'source': 'university_rule',
        })

        return tasks

        # Task 3: Letters of Recommendation
        num_recs = university.num_recommendations
        if num_recs is None and country_req:
            num_recs = country_req.default_num_recommendations
        num_recs = num_recs or 2

        tasks.append({
            'type': 'recommendations',
            'title': f'Secure {num_recs} Recommendation Letters',
            'description': f'Request letters from {num_recs} teachers who can speak to your academic abilities',
            'critical': True,
            'reason': f'{university.name} requires {num_recs} recommendations',
        })

        # Task 4: Essay (if required)
        essay_required = university.essay_required
        if essay_required is None and country_req:
            essay_required = country_req.default_essay_required

        if essay_required:
            prompt = university.essay_prompt or 'Personal statement'
            tasks.append({
                'type': 'essay',
                'title': f'Write Essay: {prompt[:50]}...' if len(prompt) > 50 else f'Write Essay: {prompt}',
                'description': f'Write your essay for {university.name}. Prompt: {prompt}',
                'critical': True,
                'reason': f'{university.name} requires an essay',
            })

        # Task 5: Test Scores (if not already submitted)
        if self.profile.ielts_score:
            tasks.append({
                'type': 'test_scores',
                'title': 'Submit IELTS Scores',
                'description': f'Submit your IELTS score ({self.profile.ielts_score}) to {university.name}',
                'critical': True,
            })

        # Task 6: Review and Submit
        tasks.append({
            'type': 'submit',
            'title': f'Review and Submit Application (Due: {due_date})',
            'description': f'Review your application and submit before the deadline ({deadline})',
            'critical': True,
        })

        return tasks

    def _format_eligibility_summary(
        self,
        results: Dict[str, EligibilityResult]
    ) -> List[Dict]:
        """Format eligibility results for API response"""
        summary = []
        for uni_name, result in results.items():
            summary.append({
                'university': uni_name,
                'status': result.status,
                'can_apply_direct': result.can_apply_direct,
                'can_apply_foundation': result.can_apply_foundation,
                'foundation_available': result.foundation_available,
                'blockers': [
                    {
                        'type': b.gap_type,
                        'title': b.title,
                        'description': b.description,
                        'is_blocker': b.is_blocker,
                        'alternative_path': b.alternative_path,
                    }
                    for b in result.blockers
                ],
                'gaps_count': len(result.gaps),
            })
        return summary
