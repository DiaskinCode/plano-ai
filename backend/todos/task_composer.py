"""
Task Composer - Generates Todo tasks from RequirementInstance

Key principles:
1. GLOBAL tasks by TYPE (passport_validity, ielts_score, transcripts)
   - One task per type, NOT based on count
2. COUNTRY tasks grouped by country (visa, medical, finance)
3. UNIVERSITY tasks one per university (portal, essays)
4. Dependencies tracked by dedupe_key (stable IDs)
5. Stage mapped via STAGE_MAP
"""

from django.db import transaction
from django.utils import timezone
from requirements.models import RequirementInstance, RequirementTemplate
from todos.models import Todo


class TaskComposer:
    """
    Compose tasks from RequirementInstance with proper scoping and dependencies
    """

    # Task type classifications (CRITICAL - by type, not by count)
    GLOBAL_TASK_TYPES = {
        'passport_validity',
        'passport_valid',  # ✅ Added
        'ielts_score',
        'ielts_academic',  # ✅ Added
        'toefl_score',
        'toefl_ibit',  # ✅ Added
        'transcripts',
        'academic_transcripts',  # ✅ Added
        'recommendation_letters',
        'cv_resume',  # ✅ Added (can be global or uni-specific)
    }

    COUNTRY_TASK_TYPES = {
        'visa_application',
        'medical_exam',
        'finance_proof',
        'translation_requirements',
    }

    UNIVERSITY_TASK_TYPES = {
        'application_portal',
        'university_specific_essay',
        'complete_application_form',
        'submit_application',
        'personal_statement',  # ✅ Added
        'portfolio',  # ✅ Added
        'cv_resume',  # ✅ Added (can be uni-specific too)
        'motivation_letter',  # ✅ Added
    }

    # Stage mapping
    STAGE_MAP = {
        'visa': 'visa',
        'medical': 'docs',
        'docs': 'docs',
        'finance': 'docs',
        'apply': 'apply',
        'offer': 'arrival',  # Post-offer tasks
        'scholarship': 'docs',
    }

    def __init__(self, user):
        self.user = user
        self.created_tasks = []
        self.updated_tasks = []

    @transaction.atomic
    def compose_tasks(self, requirement_instances, shortlist):
        """
        Generate tasks from RequirementInstance

        ✅ CRITICAL FIX: Only create tasks for missing/unknown/not_required
        Skip satisfied requirements

        Args:
            requirement_instances: QuerySet of RequirementInstance
            shortlist: QuerySet or list of shortlist items

        Returns:
            dict: Statistics about task composition
        """
        self.created_tasks = []
        self.updated_tasks = []

        # ✅ Filter out satisfied and not_required requirements
        actionable_instances = requirement_instances.exclude(
            status__in=['satisfied', 'completed', 'not_required']
        )

        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"TaskComposer: {requirement_instances.count()} total instances, {actionable_instances.count()} actionable (excluding satisfied, completed, not_required)")

        # Group instances by scope level
        global_instances = actionable_instances.filter(scope_level='global')
        country_instances = actionable_instances.filter(scope_level='country')
        university_instances = actionable_instances.filter(scope_level='university')
        scholarship_instances = actionable_instances.filter(scope_level='scholarship')
        post_offer_instances = actionable_instances.filter(requirement_key__in=[
            'offer_letter',
            'enrollment_deposit',
            'visa_sponsor_cas',
            'visa_sponsor_i20',
        ])

        # === 1. GLOBAL TASKS (one per type) ===
        for instance in global_instances:
            self._create_global_task(instance, shortlist)

        # === 2. COUNTRY TASKS (grouped by country) ===
        countries = country_instances.values_list('country', flat=True).distinct()
        for country in countries:
            country_reqs = country_instances.filter(country=country)
            for instance in country_reqs:
                self._create_country_task(instance, shortlist)

        # === 3. UNIVERSITY TASKS (one per university) ===
        for instance in university_instances:
            self._create_university_task(instance)

        # === 4. SCHOLARSHIP TASKS ===
        for instance in scholarship_instances:
            self._create_scholarship_task(instance)

        # === 5. POST-OFFER TASKS ===
        for instance in post_offer_instances:
            if instance.scope_level == 'university':
                self._create_post_offer_task(instance)

        # === 6. ADD DEPENDENCIES ===
        self._add_dependencies()

        # ✅ CRITICAL: Collect dedupe_keys for cleanup
        dedupe_keys = set()
        for task in self.created_tasks + self.updated_tasks:
            if task.dedupe_key:
                dedupe_keys.add(task.dedupe_key)

        return {
            'created': len(self.created_tasks),
            'updated': len(self.updated_tasks),
            'total': len(self.created_tasks) + len(self.updated_tasks),
            'dedupe_keys': dedupe_keys  # ✅ Return for proper cleanup
        }

    def _create_global_task(self, instance, shortlist):
        """
        Create a global task (one per type)

        Builds checklist with ALL universities
        """
        # Get template with error handling
        try:
            template = RequirementTemplate.objects.get(key=instance.requirement_key)
            title = template.title
            description = template.description
            link_url = template.default_link_url or ''
            category = template.category
        except RequirementTemplate.DoesNotExist:
            # Fallback for missing templates
            title = instance.requirement_key.replace('_', ' ').title()
            description = f"Complete {title}"
            link_url = ''
            category = 'docs'

        # Build checklist with PER-UNIVERSITY status
        checklist = {}
        for shortlist_item in shortlist:
            uni = shortlist_item.university
            uni_id = str(uni.id)

            # ✅ CRITICAL: Check status for THIS university
            # Option 1: Check if uni-specific RequirementInstance exists
            uni_instance = RequirementInstance.objects.filter(
                user=self.user,
                university=uni,
                requirement_key=instance.requirement_key
            ).first()

            # Option 2: Check user evidence (DocumentVaultItem) if no uni instance
            if uni_instance:
                status = uni_instance.status  # 'required' | 'satisfied' | 'missing'
            else:
                # Default to pending if no uni-specific instance
                status = 'pending'

            checklist[uni_id] = {
                'required': True,
                'status': status,
                'university_name': uni.name,
                'university_short_name': uni.short_name,
            }

        # Generate dedupe_key
        dedupe_key = f"{instance.requirement_key}_global"

        task, created = Todo.objects.update_or_create(
            user=self.user,
            dedupe_key=dedupe_key,
            defaults={
                'title': title,
                'requirement_key': instance.requirement_key,
                'scope': 'global',
                'university': None,  # ✅ Global tasks have no university
                'country': '',
                'stage': self._map_stage(category),
                'reason': description,
                'university_checklist': checklist,
                'link_url': link_url,
                'link_type': 'requirement_page',
                'evidence_fields': instance.evidence_fields or [],
                'evidence_status': 'missing',
                'dedupe_key': dedupe_key,
                'task_type': 'manual',
                'is_auto_generated': True,
                'source': instance.source or 'country_rule',
                'scheduled_date': timezone.now().date(),
                'priority': 2,
                'status': 'ready',
            }
        )

        if created:
            self.created_tasks.append(task)
        else:
            self.updated_tasks.append(task)

    def _create_country_task(self, instance, shortlist):
        """
        Create a country-level task

        Groups universities in this country
        """
        template = RequirementTemplate.objects.get(key=instance.requirement_key)

        # Build checklist with universities in this country
        checklist = {}
        for shortlist_item in shortlist:
            uni = shortlist_item.university
            if uni.location_country == instance.country:
                uni_id = str(uni.id)
                checklist[uni_id] = {
                    'required': True,
                    'status': instance.status,
                    'university_name': uni.name,
                    'university_short_name': uni.short_name,
                }

        # Generate dedupe_key
        dedupe_key = f"{instance.requirement_key}_country_{instance.country}"

        task, created = Todo.objects.update_or_create(
            user=self.user,
            dedupe_key=dedupe_key,
            defaults={
                'title': f"{template.title} ({instance.country})",
                'requirement_key': instance.requirement_key,
                'scope': 'country',
                'university': None,
                'stage': self._map_stage(template.category),
                'reason': f"Required for {instance.country}",
                'university_checklist': checklist,
                'link_url': template.default_link_url or '',
                'link_type': 'visa' if template.category == 'visa' else 'requirement_page',
                'evidence_fields': instance.evidence_fields or [],
                'evidence_status': 'missing',
                'country': instance.country,
                'dedupe_key': dedupe_key,
                'task_type': 'manual',
                'is_auto_generated': True,
                'source': instance.source or 'country_rule',
                'scheduled_date': timezone.now().date(),
                'priority': 2,
                'status': 'ready',
            }
        )

        if created:
            self.created_tasks.append(task)
        else:
            self.updated_tasks.append(task)

    def _create_university_task(self, instance):
        """
        Create a university-specific task

        ✅ ENHANCED: Check for RequirementRule overrides for title, link, etc.
        """
        from requirements.models import RequirementRule

        # Get template
        try:
            template = RequirementTemplate.objects.get(key=instance.requirement_key)
        except RequirementTemplate.DoesNotExist:
            # Fallback if template doesn't exist
            template = None

        # ✅ CRITICAL: Check for RequirementRule overrides
        title = template.title if template else instance.requirement_key.replace('_', ' ').title()
        link_url = instance.university.application_portal or ''
        link_type = 'portal'

        # Look for university-specific rule with overrides
        rule = RequirementRule.objects.filter(
            university=instance.university,
            template__key=instance.requirement_key,
            is_active=True
        ).first()

        if rule and rule.overrides:
            # Apply overrides
            if 'title' in rule.overrides:
                title = rule.overrides['title']
            if rule.link_url:
                link_url = rule.link_url
                link_type = 'requirement_page'

        # ✅ IMPROVED dedupe_key format: include track to prevent duplicates
        # Format: {requirement_key}_uni_{university_id}_track_{track}
        track = self._get_user_track()
        dedupe_key = f"{instance.requirement_key}_uni_{instance.university.id}_track_{track}"

        # Determine stage
        if template:
            stage = self._map_stage(template.category)
        else:
            # Default stage based on requirement key
            if 'portfolio' in instance.requirement_key:
                stage = 'apply'
            elif 'essay' in instance.requirement_key or 'statement' in instance.requirement_key:
                stage = 'apply'
            else:
                stage = 'docs'

        task, created = Todo.objects.update_or_create(
            user=self.user,
            dedupe_key=dedupe_key,
            defaults={
                'title': title,  # ✅ Use overridden title
                'requirement_key': instance.requirement_key,
                'scope': 'university',
                'university': instance.university,
                'country': '',
                'stage': stage,
                'reason': f"Required by {instance.university.name}",
                'link_url': link_url,
                'link_type': link_type,
                'evidence_fields': instance.evidence_fields or [],
                'evidence_status': 'missing',
                'dedupe_key': dedupe_key,
                'task_type': 'manual',
                'is_auto_generated': True,
                'source': instance.source or 'university_rule',
                'scheduled_date': self._calculate_task_deadline(instance.university, instance.requirement_key),  # ✅ Real deadline
                'priority': self._calculate_priority(instance),  # ✅ Dynamic priority
                'status': 'ready',
            }
        )

        if created:
            self.created_tasks.append(task)
        else:
            self.updated_tasks.append(task)

    def _create_scholarship_task(self, instance):
        """
        Create a scholarship requirement task
        """
        template = RequirementTemplate.objects.get(key=instance.requirement_key)

        # Generate dedupe_key
        dedupe_key = f"{instance.requirement_key}_scholarship"

        task, created = Todo.objects.update_or_create(
            user=self.user,
            dedupe_key=dedupe_key,
            defaults={
                'title': template.title,
                'requirement_key': instance.requirement_key,
                'scope': 'global',  # Scholarship tasks are global
                'university': None,
                'stage': 'docs',  # Scholarship tasks are docs stage
                'reason': template.description,
                'link_url': template.default_link_url or '',
                'link_type': 'scholarship',
                'evidence_fields': instance.evidence_fields or [],
                'evidence_status': 'missing',
                'country': '',
                'dedupe_key': dedupe_key,
                'task_type': 'manual',
                'is_auto_generated': True,
                'source': instance.source or 'scholarship_rule',
                'scheduled_date': timezone.now().date(),
                'priority': 2,
                'status': 'ready',
            }
        )

        if created:
            self.created_tasks.append(task)
        else:
            self.updated_tasks.append(task)

    def _create_post_offer_task(self, instance):
        """
        Create a post-offer task (arrival stage)
        """
        template = RequirementTemplate.objects.get(key=instance.requirement_key)

        # Generate dedupe_key
        dedupe_key = f"{instance.requirement_key}_uni_{instance.university.id}_offer"

        task, created = Todo.objects.update_or_create(
            user=self.user,
            dedupe_key=dedupe_key,
            defaults={
                'title': template.title,
                'requirement_key': instance.requirement_key,
                'scope': 'university',
                'university': instance.university,
                'country': '',
                'stage': 'arrival',  # Post-offer is arrival stage
                'reason': f"Post-admission requirement for {instance.university.name}",
                'link_url': template.default_link_url or '',
                'link_type': 'upload',
                'evidence_fields': instance.evidence_fields or [],
                'evidence_status': 'missing',
                'dedupe_key': dedupe_key,
                'task_type': 'manual',
                'is_auto_generated': True,
                'source': instance.source or 'university_rule',
                'scheduled_date': timezone.now().date(),
                'priority': 2,
                'status': 'ready',
            }
        )

        if created:
            self.created_tasks.append(task)
        else:
            self.updated_tasks.append(task)

    def _add_dependencies(self):
        """
        Add critical dependencies using dedupe_keys

        Dependencies:
        - visa_application depends on: offer_letter + passport_validity + finance_proof
        - enrollment_deposit depends on: offer_letter
        - visa_sponsor_cas/i20 depends on: offer_letter + enrollment_deposit
        """
        # Get all tasks for this user
        tasks = Todo.objects.filter(user=self.user)
        task_map = {task.dedupe_key: task for task in tasks}

        # Visa application dependencies
        visa_keys = [k for k in task_map.keys() if 'visa_application' in k]
        for visa_key in visa_keys:
            country = visa_key.split('_')[-1]  # Extract country from dedupe_key

            dependencies = []

            # Depends on offer
            offer_keys = [k for k in task_map.keys() if 'offer_letter' in k]
            dependencies.extend(offer_keys)

            # Depends on passport
            if 'passport_validity_global' in task_map:
                dependencies.append('passport_validity_global')

            # Depends on finance for same country
            finance_key = f'finance_proof_country_{country}'
            if finance_key in task_map:
                dependencies.append(finance_key)

            if dependencies:
                task = task_map[visa_key]
                task.depends_on = dependencies
                task.save()

        # Enrollment deposit dependencies
        deposit_keys = [k for k in task_map.keys() if 'enrollment_deposit' in k]
        for deposit_key in deposit_keys:
            dependencies = []

            # Depends on offer
            offer_keys = [k for k in task_map.keys() if 'offer_letter' in k]
            dependencies.extend(offer_keys)

            if dependencies:
                task = task_map[deposit_key]
                task.depends_on = dependencies
                task.save()

        # Visa sponsor (CAS/I-20) dependencies
        sponsor_keys = [k for k in task_map.keys() if 'visa_sponsor' in k]
        for sponsor_key in sponsor_keys:
            dependencies = []

            # Depends on offer
            offer_keys = [k for k in task_map.keys() if 'offer_letter' in k]
            dependencies.extend(offer_keys)

            # Depends on enrollment deposit
            deposit_keys = [k for k in task_map.keys() if 'enrollment_deposit' in k]
            dependencies.extend(deposit_keys)

            if dependencies:
                task = task_map[sponsor_key]
                task.depends_on = dependencies
                task.save()

    def _map_stage(self, category):
        """
        Map requirement category to task stage
        """
        return self.STAGE_MAP.get(category, 'docs')

    def _get_user_track(self):
        """
        Get user's academic track (direct vs foundation)

        Returns:
            str: Track type ('direct' or 'foundation')
        """
        try:
            from university_profile.models import UniversitySeekerProfile
            profile = UniversitySeekerProfile.objects.filter(user=self.user).first()
            if profile:
                return getattr(profile, 'track', 'direct')
        except Exception as e:
            logger.warning(f"Could not get user track: {e}")

        return 'direct'  # Default fallback

    def _calculate_task_deadline(self, university, requirement_key):
        """
        Calculate appropriate deadline based on university calendar and task type.

        Strategy:
        - Application tasks: Use actual university deadline
        - Document prep: Deadline - 30 days (buffer)
        - Test prep: Deadline - 60 days
        - Visa/arrival: Deadline + 60 days (post-admission)

        Args:
            university: University object
            requirement_key: Task requirement key

        Returns:
            date: Calculated deadline
        """
        from datetime import timedelta

        now = timezone.now().date()

        # Get university deadline
        if university.early_decision_deadline and university.early_decision_deadline > now:
            uni_deadline = university.early_decision_deadline
        elif university.regular_decision_deadline:
            uni_deadline = university.regular_decision_deadline
        else:
            # No deadline found, use default 60 days
            return now + timedelta(days=60)

        # Apply buffer based on task type
        if requirement_key in ['application_portal', 'submit_application', 'complete_application_form']:
            # No buffer for application tasks - use actual deadline
            return uni_deadline

        elif requirement_key in ['ielts_score', 'ielts_academic', 'toefl_score', 'toefl_ibit', 'sat_score', 'act_score']:
            # Test prep needs 60-day buffer
            deadline = uni_deadline - timedelta(days=60)
            return deadline if deadline > now else now + timedelta(days=7)

        elif requirement_key in ['transcripts', 'academic_transcripts', 'recommendation_letters', 'cv_resume']:
            # Documents need 30-day buffer
            deadline = uni_deadline - timedelta(days=30)
            return deadline if deadline > now else now + timedelta(days=7)

        elif requirement_key in ['visa_application', 'medical_exam', 'finance_proof', 'translation_requirements']:
            # Post-admission tasks - after acceptance
            return uni_deadline + timedelta(days=60)

        else:
            # Default: 14-day buffer
            deadline = uni_deadline - timedelta(days=14)
            return deadline if deadline > now else now + timedelta(days=7)

    def _calculate_priority(self, instance):
        """
        Calculate priority based on urgency and importance.

        Returns:
            int: 1 (low), 2 (medium), 3 (high)
        """
        from datetime import timedelta

        # Check if deadline is soon
        if hasattr(instance, 'university') and instance.university:
            uni = instance.university
            now = timezone.now().date()

            # Get deadline
            if uni.early_decision_deadline and uni.early_decision_deadline > now:
                deadline = uni.early_decision_deadline
            elif uni.regular_decision_deadline:
                deadline = uni.regular_decision_deadline
            else:
                deadline = None

            # High priority: deadline within 30 days
            if deadline and (deadline - now) <= timedelta(days=30):
                return 3

            # Medium priority: deadline within 60 days
            if deadline and (deadline - now) <= timedelta(days=60):
                return 2

        # Check if it's a blocker (missing critical requirement)
        if instance.status == 'missing':
            return 3

        return 2  # Default medium


def compose_tasks_from_requirements(user, requirement_instances, shortlist):
    """
    Convenience function to compose tasks from requirements

    Args:
        user: User instance
        requirement_instances: QuerySet of RequirementInstance
        shortlist: QuerySet or list of shortlist items

    Returns:
        dict: Statistics about task composition
    """
    composer = TaskComposer(user)
    return composer.compose_tasks(requirement_instances, shortlist)
