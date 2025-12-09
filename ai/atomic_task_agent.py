"""
Atomic Task Agent
Generates atomic tasks with full structure based on GoalSpec

Follows pattern: Verb + Target + Constraint + Deliverable + Evidence + Timebox
"""
import json
from typing import Dict, List, Any
from datetime import datetime, timedelta

from .services import AIService
from .web_search import web_search_service
from users.goalspec_models import GoalSpec
from .template_selector import template_selector
from .profile_extractor import profile_extractor
from .template_enhancer import template_enhancer, EnhancementConfig
from .custom_task_generators import create_custom_task_generator
from .unique_task_generator import generate_unique_tasks
from .task_validator import create_task_validator
from .scenario_detector import create_scenario_detector
from .full_llm_generator import generate_full_llm_tasks


class AtomicTaskAgent:
    """
    Generates atomic tasks from GoalSpec configurations
    Each task includes: type, timebox, DoD, constraints, deliverable
    """

    def __init__(self, user):
        self.user = user
        self.ai_service = AIService()
        self.search_service = web_search_service
        self.search_results = {}
        # Get user profile for personalization
        self.profile = getattr(user, 'profile', None)

    def _build_profile_context(self, goalspec: GoalSpec) -> str:
        """
        Build personalized profile context for AI task generation.
        This makes Day 1 tasks truly personalized based on user's strengths/weaknesses.
        """
        if not self.profile:
            return "No profile data available."

        context_parts = []
        category = goalspec.category if hasattr(goalspec, 'category') else goalspec.goal_type

        # Study-specific profile data
        if category == 'study':
            if self.profile.gpa:
                context_parts.append(f"GPA: {self.profile.gpa}/4.0")
            if self.profile.test_scores:
                scores_str = ", ".join([f"{k}: {v}" for k, v in self.profile.test_scores.items()])
                context_parts.append(f"Test Scores: {scores_str}")
            if self.profile.field_of_study:
                context_parts.append(f"Field: {self.profile.field_of_study}")
            if self.profile.prior_education:
                context_parts.append(f"Education: {json.dumps(self.profile.prior_education)}")

        # Career-specific profile data
        elif category == 'career':
            if self.profile.years_of_experience:
                context_parts.append(f"Experience: {self.profile.years_of_experience} years")
            if self.profile.current_role:
                context_parts.append(f"Current Role: {self.profile.current_role}")
            if self.profile.companies_worked:
                companies_str = ", ".join(self.profile.companies_worked[:3])  # Top 3
                context_parts.append(f"Companies: {companies_str}")
            if self.profile.skills:
                skills_str = ", ".join(self.profile.skills[:5])  # Top 5
                context_parts.append(f"Skills: {skills_str}")
            if self.profile.referral_network_size:
                context_parts.append(f"Network Size: {self.profile.referral_network_size} people")
            if self.profile.network:
                context_parts.append(f"Network Details: {json.dumps(self.profile.network)}")

        # Fitness-specific profile data
        elif category == 'sport':
            if self.profile.fitness_level:
                context_parts.append(f"Fitness Level: {self.profile.fitness_level}")
            if self.profile.gym_access is not None:
                context_parts.append(f"Gym Access: {'Yes' if self.profile.gym_access else 'No'}")
            if self.profile.injuries_limitations:
                injuries_str = ", ".join(self.profile.injuries_limitations)
                context_parts.append(f"Injuries/Limitations: {injuries_str}")
            if self.profile.workout_history:
                context_parts.append(f"Workout History: {json.dumps(self.profile.workout_history)}")

        # Energy peak (useful for all categories)
        if self.profile.energy_peak:
            context_parts.append(f"Energy Peak: {self.profile.energy_peak}")

        return "\n".join(context_parts) if context_parts else "No detailed profile data available."

    def _generate_from_templates(
        self,
        goalspec: GoalSpec,
        days_ahead: int
    ) -> List[Dict]:
        """
        Generate atomic tasks from templates (Week 1-2 approach).

        Uses deterministic template selection and variable substitution
        to guarantee personalization without LLM hallucinations.

        NOW GENERATES 14-18 TASKS PER GOALSPEC across ALL milestone types
        for comprehensive journey planning (research → prep → apply → visa).

        Week 1 Day 3-4: LLM enhancement is ALWAYS ON (not optional).

        Args:
            goalspec: GoalSpec object with all user constraints
            days_ahead: Number of days to plan ahead

        Returns:
            List of atomic task dictionaries (14-18 tasks) covering all milestone types
        """
        # Extract structured context from profile
        context = profile_extractor.extract_context(self.profile, goalspec)

        # Get ALL relevant milestone types for comprehensive planning
        milestone_types = self._infer_all_milestone_types(goalspec)

        if not milestone_types:
            print("[AtomicTaskAgent] Could not infer any milestone types from goalspec")
            return []

        print(f"[AtomicTaskAgent] Generating tasks across {len(milestone_types)} milestone types: {milestone_types}")

        # Select 2-3 templates per milestone type for comprehensive coverage
        all_templates = []
        for milestone_type in milestone_types:
            templates = template_selector.select_multiple(
                milestone_type=milestone_type,
                user_profile=self.profile,
                goal_spec=goalspec,
                count=2,  # 2 templates per milestone type
                milestone=None
            )

            if templates:
                all_templates.extend(templates)
                print(f"[AtomicTaskAgent] Found {len(templates)} templates for milestone: {milestone_type}")
            else:
                print(f"[AtomicTaskAgent] No templates found for milestone: {milestone_type}")

        if not all_templates:
            print(f"[AtomicTaskAgent] No templates found for any milestone types")
            return []

        print(f"[AtomicTaskAgent] Total templates selected: {len(all_templates)} tasks")

        # Generate tasks from each template
        tasks = []
        today = datetime.now().date()

        for idx, template in enumerate(all_templates):
            try:
                # Render template with context
                task_title = template.render(context)
            except ValueError as e:
                print(f"[AtomicTaskAgent] Template rendering error for '{template.id}': {e}")
                print(f"[AtomicTaskAgent] Available context keys: {list(context.keys())}")
                # Skip this template and continue with others
                continue

            # Stagger scheduled dates (spread tasks over days_ahead period)
            day_offset = min(idx * 2, days_ahead - 1)  # Spread tasks every 2 days
            scheduled_date = today + timedelta(days=day_offset)

            # Build definition of done from template
            dod = self._build_dod_from_template(template, context)

            # Build constraints from template and context
            constraints = self._build_constraints_from_template(template, context)

            # Get milestone information from template
            milestone_type = getattr(template, 'milestone_type', None)
            milestone_title = self._get_milestone_title(milestone_type) if milestone_type else None
            milestone_index = self._get_milestone_index(milestone_type, milestone_types) if milestone_type else None

            # Create task dictionary
            task = {
                'title': task_title,
                'description': f"Generated from template: {template.id}",
                'task_type': 'auto' if template.timebox_minutes <= 60 else 'copilot',
                'timebox_minutes': template.timebox_minutes,
                'priority': template.priority,
                'deliverable_type': self._infer_deliverable_type(template),
                'is_quick_win': template.timebox_minutes <= 30,
                'task_category': 'quick_win' if template.timebox_minutes <= 30 else 'foundation',
                'constraints': constraints,
                'definition_of_done': dod,
                'lets_go_inputs': [],
                'artifact_template': {},
                'scheduled_date': scheduled_date.strftime('%Y-%m-%d'),
                'external_url': None,
                'notes': f"Template: {template.name} ({template.category.value})",
                'source': 'template_agent',
                'milestone_title': milestone_title,
                'milestone_index': milestone_index
            }

            # Validate task quality before adding
            is_valid, validation_error = self._validate_task_quality(task)
            if not is_valid:
                print(f"[AtomicTaskAgent] WARNING: Task #{idx+1} quality issue: {validation_error}")
                print(f"[AtomicTaskAgent] Task title: {task_title[:100]}")
                # Continue anyway but log the issue

            print(f"[AtomicTaskAgent] Generated task #{idx+1} from template '{template.id}': {task_title[:60]}...")

            # Week 1 Day 3-4: ALWAYS apply LLM enhancement with Claude Sonnet
            try:
                enhancement_config = EnhancementConfig(
                    enhance_title=True,
                    enhance_description=True,
                    enhance_dod=False,  # Keep DoD factual
                    tone='professional'
                )
                task = template_enhancer.enhance_task(
                    task=task,
                    user_profile=self.profile,
                    user=self.user,  # Pass user for cost tracking
                    config=enhancement_config
                )
                print(f"[AtomicTaskAgent] Task #{idx+1} enhanced with Claude Sonnet (cost: ${task.get('enhancement_cost', 0):.4f})")
            except Exception as e:
                print(f"[AtomicTaskAgent] Enhancement failed for task #{idx+1}, using original: {e}")

            tasks.append(task)

        # === LAYER 3: GENERATE CUSTOM TASKS (Unique to specific backgrounds) ===
        print(f"[AtomicTaskAgent] Template tasks: {len(tasks)}")
        print(f"[AtomicTaskAgent] Generating custom tasks based on personalization context...")

        # Create custom task generator with full context (includes personalization flags)
        custom_generator = create_custom_task_generator(context)
        custom_tasks_raw = custom_generator.generate_all_custom_tasks()

        # Convert custom tasks to atomic task format
        for idx, custom_task in enumerate(custom_tasks_raw):
            # Schedule custom tasks with offset
            day_offset = len(tasks) + idx  # Schedule after template tasks
            scheduled_date = today + timedelta(days=min(day_offset, days_ahead - 1))

            # Assign custom tasks to first milestone if available
            milestone_title = None
            milestone_index = None
            if milestone_types:
                first_milestone = milestone_types[0]
                milestone_title = self._get_milestone_title(first_milestone)
                milestone_index = 0

            task = {
                'title': custom_task['title'],
                'timebox_minutes': custom_task['timebox_minutes'],
                'energy_level': custom_task['energy_level'],
                'priority': custom_task['priority'],
                'deliverable_type': custom_task.get('task_type', 'note'),
                'is_quick_win': custom_task['timebox_minutes'] <= 30,
                'task_category': 'custom',  # Mark as custom for Layer 4 scoring
                'constraints': {},
                'definition_of_done': custom_task['definition_of_done'],
                'lets_go_inputs': [],
                'artifact_template': {},
                'scheduled_date': scheduled_date.strftime('%Y-%m-%d'),
                'external_url': None,
                'notes': f"Custom task: {custom_task.get('task_type', 'unique')} (personalized)",
                'source': 'custom_generator',
                'milestone_title': milestone_title,
                'milestone_index': milestone_index
            }

            tasks.append(task)
            print(f"[AtomicTaskAgent] Generated custom task #{idx+1}: {custom_task['title'][:60]}...")

        print(f"[AtomicTaskAgent] Successfully generated {len(tasks)} total tasks ({len(custom_tasks_raw)} custom + {len(tasks) - len(custom_tasks_raw)} templates) across {len(milestone_types)} milestone types")

        # === WEEK 1 DAY 5: GENERATE LLM-UNIQUE TASKS (2-3 per user) ===
        print(f"[AtomicTaskAgent] Generating LLM-unique tasks (2-3 per user)...")
        try:
            unique_tasks_raw = generate_unique_tasks(
                user=self.user,
                user_profile=self.profile,
                context=context,
                goalspec=goalspec,
                existing_tasks=tasks  # Pass existing tasks to avoid duplication
            )

            # Convert unique tasks to atomic task format and add to list
            for idx, unique_task in enumerate(unique_tasks_raw):
                # Schedule unique tasks at the end
                day_offset = len(tasks) + idx
                scheduled_date = today + timedelta(days=min(day_offset, days_ahead - 1))

                # Assign unique tasks to first milestone if available
                milestone_title = None
                milestone_index = None
                if milestone_types:
                    first_milestone = milestone_types[0]
                    milestone_title = self._get_milestone_title(first_milestone)
                    milestone_index = 0

                task = {
                    'title': unique_task['title'],
                    'description': unique_task.get('description', ''),
                    'timebox_minutes': unique_task.get('timebox_minutes', 120),
                    'priority': unique_task.get('priority', 5),
                    'energy_level': unique_task.get('energy_level', 'high'),
                    'deliverable_type': unique_task.get('task_type', 'documentation'),
                    'is_quick_win': unique_task.get('timebox_minutes', 120) <= 30,
                    'task_category': 'unique',  # Mark as unique for Layer 4 scoring
                    'constraints': unique_task.get('constraints', {}),
                    'definition_of_done': unique_task.get('definition_of_done', ''),
                    'lets_go_inputs': unique_task.get('lets_go_inputs', []),
                    'artifact_template': unique_task.get('artifact_template', {}),
                    'scheduled_date': scheduled_date.strftime('%Y-%m-%d'),
                    'external_url': unique_task.get('external_url'),
                    'notes': unique_task.get('notes', 'LLM-generated unique task'),
                    'source': 'unique_generator',
                    'task_type': 'copilot',  # Unique tasks are always copilot (high effort)
                    'milestone_title': milestone_title,
                    'milestone_index': milestone_index
                }

                tasks.append(task)
                print(f"[AtomicTaskAgent] Generated unique task #{idx+1}: {unique_task['title'][:60]}...")

            print(f"[AtomicTaskAgent] Generated {len(unique_tasks_raw)} LLM-unique tasks")

        except Exception as e:
            print(f"[AtomicTaskAgent] Failed to generate unique tasks: {e}")
            # Continue without unique tasks - not critical

        # === LAYER 4: SMART FILTERING & TASK SCORING ===
        print(f"[AtomicTaskAgent] Applying smart filters to remove unnecessary tasks...")
        tasks_before_filter = len(tasks)
        tasks = self._smart_filter_tasks(tasks, context)
        tasks_filtered = tasks_before_filter - len(tasks)
        print(f"[AtomicTaskAgent] Filtered out {tasks_filtered} unnecessary tasks")

        print(f"[AtomicTaskAgent] Scoring and ranking tasks (prioritize unique/custom tasks)...")
        tasks = self._score_and_rank_tasks(tasks, context)
        print(f"[AtomicTaskAgent] Task ranking complete")

        # === WEEK 1 DAY 6-7: QUALITY VALIDATION ===
        print(f"[AtomicTaskAgent] Validating task quality (5-check system)...")
        validator = create_task_validator(context)
        validation_results = validator.validate_batch(tasks)

        print(f"[AtomicTaskAgent] Validation results:")
        print(f"   Total: {validation_results['total']} tasks")
        print(f"   Passed: {validation_results['passed']} ({validation_results['passed']/validation_results['total']*100:.0f}%)")
        print(f"   Failed: {validation_results['failed']} ({validation_results['failed']/validation_results['total']*100:.0f}%)")
        print(f"   Average quality score: {validation_results['average_score']:.0f}%")

        # Log warnings for failed tasks
        if validation_results['failed'] > 0:
            print(f"[AtomicTaskAgent] ⚠️  {validation_results['failed']} tasks failed quality checks:")
            for task, score, reasons in validation_results['failed_tasks'][:3]:  # Show first 3
                print(f"   - [{score}%] {task['title'][:60]}...")
                for reason in reasons:
                    print(f"     • {reason}")

        # Filter out tasks with score < 60% (auto-reject threshold)
        if validation_results['needs_regeneration'] > 0:
            print(f"[AtomicTaskAgent] 🚫 Removing {validation_results['needs_regeneration']} tasks with score < 60%")
            validated_tasks = []
            for task in tasks:
                is_valid, score, reasons = validator.validate_task(task)
                if score >= 60:  # Keep tasks with score >= 60%
                    validated_tasks.append(task)
                else:
                    print(f"[AtomicTaskAgent] Rejected: [{score}%] {task['title'][:60]}...")
            tasks = validated_tasks

        print(f"[AtomicTaskAgent] Final task count: {len(tasks)} tasks (after validation)")

        # === FIX: DEDUPLICATE TASKS ===
        print(f"[AtomicTaskAgent] Deduplicating tasks to remove any duplicates...")
        tasks_before_dedup = len(tasks)
        tasks = self._deduplicate_tasks(tasks)
        if len(tasks) < tasks_before_dedup:
            print(f"[AtomicTaskAgent] Removed {tasks_before_dedup - len(tasks)} duplicate tasks")

        return tasks

    def _infer_milestone_type(self, goalspec: GoalSpec) -> str:
        """
        Infer milestone type from goalspec.

        Maps goalspec category and title to MilestoneType enum values.

        ENHANCED: Checks GoalSpec.specifications first for better accuracy.
        """
        title = getattr(goalspec, 'title', '').lower()
        description = getattr(goalspec, 'description', '').lower()
        category = getattr(goalspec, 'category', getattr(goalspec, 'goal_type', '')).lower()
        specs = getattr(goalspec, 'specifications', {}) or {}

        combined = f"{title} {description}"

        # Study milestones
        if category == 'study':
            # ENHANCEMENT: Check specifications first (more reliable than keywords)
            # If user has selected target universities, start with research phase
            if specs.get('target_universities'):
                # User has specific universities in mind → start with research
                return 'university_research'

            # Keyword-based inference (reordered for better priority)
            if 'ielts' in combined or 'toefl' in combined or 'exam' in combined:
                return 'exam_prep'
            elif 'sop' in combined or 'statement of purpose' in combined or 'personal statement' in combined:
                return 'sop_drafting'
            elif 'recommendation' in combined or 'lor' in combined:
                return 'recommendations'
            elif 'visa' in combined:
                return 'visa_process'
            elif 'scholarship' in combined or 'funding' in combined:
                return 'scholarships'
            elif 'research' in combined or 'university' in combined or 'program' in combined:
                return 'university_research'
            elif 'application' in combined or 'apply' in combined:
                # 'apply' keyword is ambiguous - check if it's early stage
                # If no universities specified, assume they need research first
                return 'applications' if specs.get('target_universities') else 'university_research'
            else:
                return 'university_research'  # Default for study (research comes first)

        # Career milestones
        elif category == 'career':
            if 'resume' in combined or 'cv' in combined:
                return 'resume_update'
            elif 'linkedin' in combined:
                return 'linkedin_optimization'
            elif 'apply' in combined or 'application' in combined or 'job' in combined:
                return 'job_applications'
            elif 'network' in combined or 'connect' in combined or 'reach out' in combined:
                return 'networking'
            elif 'skill' in combined or 'learn' in combined or 'course' in combined:
                return 'skill_building'
            elif 'interview' in combined:
                return 'interview_prep'
            else:
                return 'job_search'  # Default for career

        # Fitness milestones (not implemented yet)
        elif category == 'sport' or category == 'fitness':
            return None  # No fitness templates yet

        return None

    def _infer_all_milestone_types(self, goalspec: GoalSpec) -> List[str]:
        """
        Infer ALL relevant milestone types for comprehensive task generation.

        Instead of returning ONE milestone type, this returns ALL milestone types
        needed to create a complete journey (research → prep → apply → visa).

        Returns:
            List of milestone type strings for the given goalspec category
        """
        category = getattr(goalspec, 'category', getattr(goalspec, 'goal_type', '')).lower()

        # Study milestones - full journey from research to visa
        if category == 'study':
            return [
                'university_research',  # Step 1: Research programs and universities
                'exam_prep',           # Step 2: Prepare for IELTS/TOEFL/GRE
                'sop_drafting',        # Step 3: Write compelling SOP
                'recommendations',     # Step 4: Get strong recommendations
                'applications',        # Step 5: Submit applications
                'scholarships',        # Step 6: Find and apply for funding
                'visa_process'         # Step 7: Visa preparation and documents
            ]

        # Career milestones - full journey from profile to interview
        elif category == 'career':
            return [
                'linkedin_optimization',  # Step 1: Optimize online presence
                'resume_update',          # Step 2: Polish resume/CV
                'job_search',             # Step 3: Find target companies
                'networking',             # Step 4: Connect with people
                'job_applications',       # Step 5: Apply to positions
                'interview_prep'          # Step 6: Prepare for interviews
            ]

        # For other categories, fall back to single milestone type
        else:
            single_type = self._infer_milestone_type(goalspec)
            return [single_type] if single_type else []

    def _build_dod_from_template(self, template: Any, context: Dict[str, Any]) -> List[Dict]:
        """
        Build definition of done checklist from template.

        Creates 2-4 weighted checklist items based on template type.
        """
        # Default DoD based on template category
        if template.category.value == 'study':
            if 'research' in template.id:
                return [
                    {'text': f"Find {context.get('num_schools', 5)} programs matching criteria", 'weight': 40, 'completed': False},
                    {'text': 'Check application deadlines', 'weight': 30, 'completed': False},
                    {'text': 'Note requirements (GPA, test scores)', 'weight': 30, 'completed': False}
                ]
            elif 'ielts' in template.id or 'exam' in template.id:
                return [
                    {'text': 'Complete practice test', 'weight': 50, 'completed': False},
                    {'text': 'Score above target', 'weight': 50, 'completed': False}
                ]
            elif 'sop' in template.id:
                return [
                    {'text': 'Draft introduction paragraph', 'weight': 35, 'completed': False},
                    {'text': 'Write academic background section', 'weight': 35, 'completed': False},
                    {'text': 'Add career goals section', 'weight': 30, 'completed': False}
                ]

        elif template.category.value == 'career':
            if 'resume' in template.id:
                return [
                    {'text': 'Update work experience with quantified achievements', 'weight': 40, 'completed': False},
                    {'text': 'Add relevant skills for target role', 'weight': 30, 'completed': False},
                    {'text': 'Proofread and format consistently', 'weight': 30, 'completed': False}
                ]
            elif 'linkedin' in template.id:
                return [
                    {'text': 'Update headline with target role', 'weight': 35, 'completed': False},
                    {'text': 'Revise about section', 'weight': 35, 'completed': False},
                    {'text': 'Add relevant skills and endorsements', 'weight': 30, 'completed': False}
                ]
            elif 'job' in template.id or 'application' in template.id:
                return [
                    {'text': 'Identify 5-10 relevant job postings', 'weight': 40, 'completed': False},
                    {'text': 'Save postings for later', 'weight': 30, 'completed': False},
                    {'text': 'Note application requirements', 'weight': 30, 'completed': False}
                ]

        # Generic fallback
        return [
            {'text': 'Complete main task objective', 'weight': 100, 'completed': False}
        ]

    def _build_constraints_from_template(self, template: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build constraints dictionary from template and context.
        """
        constraints = {}

        # Add budget if available
        if context.get('budget'):
            constraints['budget'] = context['budget']

        # Add category-specific constraints
        if template.category.value == 'study':
            if context.get('target_countries'):
                constraints['location'] = context['target_countries']
            if context.get('field'):
                constraints['field'] = context['field']
            if context.get('degree_level'):
                constraints['degree'] = context['degree_level']

        elif template.category.value == 'career':
            if context.get('target_role'):
                constraints['role'] = context['target_role']
            if context.get('target_industry'):
                constraints['industry'] = context['target_industry']
            if context.get('experience_level'):
                constraints['experience'] = context['experience_level']

        return constraints

    def _infer_deliverable_type(self, template: Any) -> str:
        """
        Infer deliverable type from template.
        """
        if 'research' in template.id:
            return 'spreadsheet'
        elif 'sop' in template.id or 'resume' in template.id:
            return 'doc'
        elif 'email' in template.id or 'network' in template.id:
            return 'email'
        elif 'linkedin' in template.id:
            return 'link'
        elif 'application' in template.id:
            return 'shortlist'
        else:
            return 'note'

    def _smart_filter_tasks(self, tasks: List[Dict], context: Dict[str, Any]) -> List[Dict]:
        """
        Layer 4: Smart filtering - Remove unnecessary tasks.

        Examples:
        - Skip IELTS prep if current score >= target score
        - Skip test prep tasks if test scores already meet requirements
        - Skip generic tasks if custom task covers the same area

        Args:
            tasks: List of generated tasks
            context: Full personalization context (with test_prep_needed flags)

        Returns:
            Filtered list of tasks
        """
        filtered_tasks = []
        test_prep_needed = context.get('test_prep_needed', {})

        for task in tasks:
            title_lower = task['title'].lower()
            should_skip = False

            # Skip test prep if not needed
            if 'ielts' in title_lower and 'prep' in title_lower:
                if not test_prep_needed.get('ielts', True):
                    print(f"[SmartFilter] Skipping IELTS prep - score already meets target")
                    should_skip = True

            if 'toefl' in title_lower and 'prep' in title_lower:
                if not test_prep_needed.get('toefl', True):
                    print(f"[SmartFilter] Skipping TOEFL prep - score already meets target")
                    should_skip = True

            if 'gre' in title_lower and 'prep' in title_lower:
                if not test_prep_needed.get('gre', True):
                    print(f"[SmartFilter] Skipping GRE prep - score already meets target")
                    should_skip = True

            # Skip generic LinkedIn tasks if custom founder LinkedIn task exists
            if 'linkedin' in title_lower and task.get('task_category') != 'custom':
                # Check if there's a custom LinkedIn task (founder-specific)
                has_custom_linkedin = any(
                    'linkedin' in t['title'].lower() and t.get('task_category') == 'custom'
                    for t in tasks
                )
                if has_custom_linkedin and context.get('has_startup_background'):
                    print(f"[SmartFilter] Skipping generic LinkedIn task - custom founder task exists")
                    should_skip = True

            if not should_skip:
                filtered_tasks.append(task)

        return filtered_tasks

    def _score_and_rank_tasks(self, tasks: List[Dict], context: Dict[str, Any]) -> List[Dict]:
        """
        Layer 4: Task scoring and ranking.

        Scoring system (Week 1 Day 5: Added unique tasks):
        - Unique LLM tasks (fully personalized): +25 points (HIGHEST priority)
        - Custom tasks (rule-based unique): +20 points
        - Tasks leveraging unique background (founder, GPA compensation): +15 points
        - High-impact template tasks: +10 points
        - Standard template tasks: +5 points
        - Generic tasks: +0 points

        Args:
            tasks: List of filtered tasks
            context: Full personalization context

        Returns:
            Sorted list of tasks (highest score first)
        """
        for task in tasks:
            score = 0
            title_lower = task['title'].lower()

            # Week 1 Day 5: Unique LLM tasks get HIGHEST priority
            if task.get('task_category') == 'unique' or task.get('source') == 'unique_generator':
                score += 25  # LLM-generated unique tasks (truly personalized)
            # Base score from task category
            elif task.get('task_category') == 'custom':
                score += 20  # Rule-based custom tasks
            elif task.get('source') == 'custom_generator':
                score += 20

            # Bonus for founder-specific tasks
            if context.get('has_startup_background'):
                if any(keyword in title_lower for keyword in ['startup', 'founder', 'built', 'users']):
                    score += 15

            # Bonus for GPA compensation tasks
            if context.get('gpa_needs_compensation'):
                if any(keyword in title_lower for keyword in ['gpa', 'optional essay', 'academic context']):
                    score += 15

            # Bonus for high-priority templates
            if task.get('priority', 2) >= 4:
                score += 10

            # Bonus for unique essays/personal statements
            if any(keyword in title_lower for keyword in ['essay', 'sop', 'statement', 'personal']):
                score += 10

            # Standard template bonus
            if task.get('source') == 'template_agent':
                score += 5

            task['personalization_score'] = score

        # Sort by score (descending), then by priority (descending), then by scheduled_date
        tasks.sort(key=lambda t: (
            -t.get('personalization_score', 0),
            -t.get('priority', 2),
            t.get('scheduled_date', '2025-01-01')
        ))

        # Log top 5 tasks
        print(f"[TaskScoring] Top 5 tasks by personalization score:")
        for idx, task in enumerate(tasks[:5]):
            score = task.get('personalization_score', 0)
            print(f"  {idx+1}. Score {score}: {task['title'][:60]}...")

        return tasks

    def generate_atomic_tasks(
        self,
        goalspec: GoalSpec,
        days_ahead: int = 7
    ) -> List[Dict]:
        """
        Generate atomic tasks using two-tier LLM system (100% LLM, 0% templates).

        Flow:
        1. Extract user context from profile + goalspec
        2. Generate 5 milestones (MilestoneGenerator)
        3. Break each milestone into 5-6 atomic tasks (AtomicTaskGenerator)
        4. Enrich tasks with real URLs/data (TaskEnricher)
        5. Pre-validate tasks (TaskValidator - rule-based)
        6. Batch verify and fix tasks (TaskVerifier - AI-powered)

        Args:
            goalspec: GoalSpec object with user's goal details
            days_ahead: Number of days to plan ahead (default: 7)

        Returns:
            List of 25-30 atomic task dictionaries with full personalization
        """
        print(f"[AtomicTaskAgent] ========== TASK GENERATION START ==========")
        print(f"[AtomicTaskAgent] Goal: {goalspec.title}")
        print(f"[AtomicTaskAgent] Category: {getattr(goalspec, 'category', 'unknown')}")
        print(f"[AtomicTaskAgent] Strategy: 100% LLM-based (two-tier milestone→atomic)")

        # Extract context (includes goalspec.specifications + user profile)
        print(f"\n[AtomicTaskAgent] === CONTEXT EXTRACTION ===")
        context = profile_extractor.extract_context(self.profile, goalspec)
        print(f"[AtomicTaskAgent] Extracted context keys: {list(context.keys())[:10]}...")

        # Log key personalization data
        if 'target_role' in context:
            print(f"[AtomicTaskAgent]   target_role = {context['target_role']}")
        if 'target_companies_string' in context:
            print(f"[AtomicTaskAgent]   target_companies = {context['target_companies_string']}")
        if 'current_company' in context:
            print(f"[AtomicTaskAgent]   current_company = {context['current_company']}")

        # Use two-tier LLM generation for ALL goals
        print(f"\n[AtomicTaskAgent] === TWO-TIER LLM GENERATION ===")
        print(f"[AtomicTaskAgent] Using GPT-4o for milestone→atomic→enrichment pipeline")

        from ai.task_executor import execute_two_tier_generation

        tasks = execute_two_tier_generation(
            user=self.user,
            user_profile=self.profile,
            context=context,
            goalspec=goalspec,
            days_ahead=days_ahead
        )

        if not tasks:
            print(f"[AtomicTaskAgent] ⚠️  WARNING: Two-tier generation returned no tasks!")
            print(f"[AtomicTaskAgent] This may indicate a problem with milestone generation or context extraction")
            return []

        print(f"\n[AtomicTaskAgent] === GENERATION COMPLETE ===")
        print(f"[AtomicTaskAgent] Successfully generated {len(tasks)} atomic tasks")
        print(f"[AtomicTaskAgent] Tasks are personalized to: {goalspec.title}")
        print(f"[AtomicTaskAgent] ========== TASK GENERATION COMPLETE ==========")

        return tasks

        # PHASE 2: Execute searches if needed
        if searches_needed and self.search_service.is_available():
            print(f"[AtomicTaskAgent] Executing {len(searches_needed)} searches...")
            for search in searches_needed:
                self._execute_search(search, goalspec)

        # PHASE 3: Generate atomic tasks with search results AND profile context
        print("[AtomicTaskAgent] Generating personalized atomic tasks...")
        atomic_tasks = self._generate_atomic_tasks_with_dod(goalspec, days_ahead, profile_context)

        print(f"[AtomicTaskAgent] ========== TASK GENERATION COMPLETE ==========")
        return atomic_tasks

    def _plan_searches(self, goalspec: GoalSpec) -> List[Dict]:
        """
        Determine what web searches are needed based on goal type and specifications
        """
        # Get specifications from new onboarding or fall back to legacy constraints
        specs = goalspec.specifications if hasattr(goalspec, 'specifications') and goalspec.specifications else goalspec.constraints
        category = goalspec.category if hasattr(goalspec, 'category') else goalspec.goal_type
        goal_type = goalspec.goal_type
        constraints = goalspec.constraints
        preferences = goalspec.preferences

        planning_prompt = f"""You are analyzing a user's goal to determine what specific web searches are needed to create CONCRETE tasks.

GOAL CATEGORY: {category}
GOAL TITLE: {goalspec.title}
GOAL DESCRIPTION: {goalspec.description if hasattr(goalspec, 'description') else ''}
SPECIFICATIONS: {json.dumps(specs)}
LEGACY CONSTRAINTS: {json.dumps(constraints)}
PREFERENCES: {json.dumps(preferences)}

Based on specifications, determine what searches would help create CONCRETE, SPECIFIC tasks with real data:

For STUDY goals (use exact country, degree, budget from specs):
- Search for specific programs: "MSc Computer Science UK universities under 30000 pounds"
- Find exact deadlines: "MSc CS UK September 2026 intake application deadlines"
- Locate test resources: "IELTS preparation materials Cambridge"
- Find real scholarships: "international scholarships MSc CS UK 2026"

For CAREER goals (use exact role, industry, experience from specs):
- Search for real job postings: "Product Manager fintech startup remote 3 years experience"
- Find specific people: "Product Managers at Stripe VP Product"
- Locate upcoming events: "fintech product management conference 2025"
- Find courses: "PM certification course fintech"

For SPORT goals (use exact sport type, goal from specs):
- Find specific programs: "muscle building workout program 6 hours per week"
- Locate facilities: "gyms near me with free weights"
- Find coaches: "personal trainer muscle building [city]"
- Discover resources: "meal prep 2500 calories high protein"

Return JSON:
{{
  "searches": [
    {{
      "type": "general|linkedin|events|courses",
      "query": "specific search query",
      "reason": "why this search is needed"
    }}
  ]
}}

If no searches needed, return: {{"searches": []}}
"""

        try:
            system_prompt = "You are a strategic research planner."
            response = self.ai_service.call_llm(
                system_prompt,
                planning_prompt,
                response_format='json'
            )

            plan = json.loads(response)
            searches = plan.get('searches', [])
            print(f"[AtomicTaskAgent] Planned {len(searches)} searches")
            return searches

        except Exception as e:
            print(f"[AtomicTaskAgent] Planning error: {e}")
            return []

    def _execute_search(self, search_config: Dict, goalspec: GoalSpec):
        """
        Execute a single search and store results
        """
        search_type = search_config['type']
        query = search_config['query']

        try:
            if search_type == 'linkedin':
                results = self.search_service.search_linkedin_profiles(
                    query=query,
                    industry=goalspec.constraints.get('industry', ''),
                    location=goalspec.constraints.get('country', ''),
                    max_results=5
                )

            elif search_type == 'events':
                results = self.search_service.search_events(
                    industry=query,
                    location=goalspec.constraints.get('country', ''),
                    timeframe="2025",
                    max_results=5
                )

            elif search_type == 'courses':
                results = self.search_service.search_courses(
                    topic=query,
                    level="intermediate",
                    max_results=5
                )

            else:  # general
                results = self.search_service.search_general(
                    query=query,
                    max_results=5
                )

            # Store results
            if search_type not in self.search_results:
                self.search_results[search_type] = []
            self.search_results[search_type].extend(results)

            print(f"[AtomicTaskAgent] Search '{search_type}' found {len(results)} results")

        except Exception as e:
            print(f"[AtomicTaskAgent] Search error ({search_type}): {e}")

    def _generate_atomic_tasks_with_dod(
        self,
        goalspec: GoalSpec,
        days_ahead: int,
        profile_context: str = ""
    ) -> List[Dict]:
        """
        Generate atomic tasks with full structure: DoD, constraints, deliverable, etc.
        NOW WITH PERSONALIZATION: Uses profile data to create Day 1 magic.
        """
        today = datetime.now().date()

        # Get specifications from new onboarding or fall back to legacy constraints
        specs = goalspec.specifications if hasattr(goalspec, 'specifications') and goalspec.specifications else goalspec.constraints
        category = goalspec.category if hasattr(goalspec, 'category') else goalspec.goal_type
        quick_wins = goalspec.quick_wins if hasattr(goalspec, 'quick_wins') else []

        generation_prompt = f"""You are creating CONCRETE, SPECIFIC ATOMIC TASKS following this pattern:
Verb + Target + Constraint + Deliverable + Evidence + Timebox

GOAL CONTEXT:
- Category: {category}

USER PROFILE (Use this to personalize tasks):
{profile_context}

PERSONALIZATION INSTRUCTIONS:
For Day 1 tasks, create 3 types:
1. QUICK WIN (< 30 min, high confidence) - Something they can complete immediately to build momentum
   Study Example: "Take 10-minute career assessment quiz → identify top 3 interests"
   Career Example: "Update LinkedIn headline with target role → new headline live"
   Fitness Example: "Log current measurements (weight, waist) → baseline data"

2. LEARNING TASK (1-2 hours) - Educational content to get oriented
   Study Example: "Watch 'How to write SOP' by AdmitEdge (45 min) → 3 key takeaways"
   Career Example: "Read '10 mistakes in PM resumes' by Lenny Rachitsky → checklist"
   Fitness Example: "Watch 'Compound lifts for beginners' by Jeff Nippard → form checklist"

3. FOUNDATION TASK (research/planning) - Sets up future tasks
   Study Example: "Research 5 MSc CS programs in UK under £30k → comparison spreadsheet"
   Career Example: "Identify 10 PM roles on LinkedIn (save for later) → job list"
   Fitness Example: "Plan 4-day workout split based on available hours → weekly schedule"

Use profile data to make tasks realistic:
- If IELTS score is 6.0, don't suggest programs requiring 7.5+ (use feasibility data)
- If user has 2 years experience, don't target senior roles
- If user has knee injury, avoid running-heavy workouts
- If user worked at Google, leverage that for warm intros
- If user's energy peak is "evening", schedule deep work for evening
- Title: {goalspec.title}
- Description: {goalspec.description if hasattr(goalspec, 'description') else ''}
- Specifications: {json.dumps(specs)}
- Legacy Constraints: {json.dumps(goalspec.constraints)}
- Preferences: {json.dumps(goalspec.preferences)}
- Timeline: {json.dumps(goalspec.timeline)}
- Quick Wins Selected: {json.dumps(quick_wins)}

SEARCH RESULTS:
{json.dumps(self.search_results, indent=2) if self.search_results else "No search results available"}

INSTRUCTIONS:
Create 5-10 CONCRETE, SPECIFIC atomic tasks for the next {days_ahead} days.

CRITICAL RULES FOR CONCRETE TASKS:
✅ DO: "Research 3 MSc CS programs in UK under £30k → spreadsheet"
✅ DO: "Draft email to Prof. John Smith at MIT about research → email"
✅ DO: "Complete 2 practice IELTS reading tests (Cambridge Book 14) → score sheet"
❌ DON'T: "Research universities" (too vague)
❌ DON'T: "Work on application" (not atomic)
❌ DON'T: "Improve skills" (not measurable)

USE SPECIFICATIONS DATA:
- For Study: Use exact country, degree, budget, intake date from specs
- For Career: Use exact targetRole, industry, experience level from specs
- For Sport: Use exact sportType, sportGoal, weeklyHours from specs
- Include Quick Wins if user selected any

Each task must include:

1. **Atomic Structure**: Verb + Specific Target + Clear Constraint + Deliverable
   Study Example: "Research [3 MSc CS programs] in [UK] under [£30k/year] → [comparison spreadsheet]"
   Career Example: "Apply to [2 PM roles] at [fintech startups] with [<5 employees] → [application confirmations]"
   Sport Example: "Complete [chest workout: 4x bench press, 3x flies] in [45 min] → [workout log]"

2. **Task Type**: Choose one:
   - "auto": AI can fully complete (research, shortlist creation, data collection)
   - "copilot": Needs user input during execution (applications, emails, documents)
   - "manual": Human-only (interviews, exams, workouts, calls)

3. **Timebox**: Realistic time estimate in minutes (15-120 minutes)
   - Research tasks: 30-60 min
   - Application tasks: 45-90 min
   - Email drafts: 20-30 min
   - Workout tasks: 30-60 min

4. **Definition of Done**: 2-4 weighted, SPECIFIC checklist items (total weight = 100)
   Study Example: [
     {{"text": "Find 3 MSc CS programs in UK under £30k/year", "weight": 40, "completed": false}},
     {{"text": "Check Sept 2026 application deadlines", "weight": 30, "completed": false}},
     {{"text": "Note IELTS requirements for each program", "weight": 30, "completed": false}}
   ]

5. **Deliverable Type**: spreadsheet | doc | email | recording | link | shortlist | file | note | other

6. **Constraints**: Specific, measurable constraints as JSON
   Study Example: {{"budget": "£10-30k", "location": "UK", "degree": "MSc CS", "intake": "Sep 2026"}}
   Career Example: {{"role": "Product Manager", "industry": "Fintech", "experience": "3-5 years", "location": "Remote"}}
   Sport Example: {{"workout_type": "Chest", "duration_min": 45, "exercises": ["bench press", "flies", "pushups"]}}

7. **Let's Go Inputs**: Questions needed ONLY if task_type is "copilot"
   Example: [{{"type": "text", "question": "Which university interests you most and why?"}}]

8. **External URL**: If available from search results (specific program page, job posting, course link)

Return JSON:
{{
  "tasks": [
    {{
      "title": "Verb + Target + Constraint example",
      "description": "Detailed description with context",
      "task_type": "auto|copilot|manual",
      "timebox_minutes": 30-120,
      "priority": 1-3,
      "deliverable_type": "spreadsheet|doc|email|recording|link|shortlist|file|note|other",
      "is_quick_win": true,  // Mark Day 1 quick wins as true (< 30 min, high confidence)
      "task_category": "quick_win|learning|foundation|regular",  // Helps frontend categorize
      "constraints": {{"key": "value"}},
      "definition_of_done": [
        {{"text": "...", "weight": 40, "completed": false}},
        {{"text": "...", "weight": 30, "completed": false}},
        {{"text": "...", "weight": 30, "completed": false}}
      ],
      "lets_go_inputs": [
        {{"type": "text", "question": "..."}}
      ],
      "artifact_template": {{}},
      "scheduled_date": "2025-10-{today.day + 1}",
      "external_url": "https://... (if applicable)",
      "notes": "Additional context from search results",
      "source": "ai_agent"
    }}
  ]
}}

DAY 1 TASK ORDERING:
1. First 1-2 tasks: QUICK WINS (is_quick_win: true, task_category: "quick_win", <30 min)
2. Next 2-3 tasks: LEARNING TASKS (task_category: "learning", 1-2 hours)
3. Remaining tasks: FOUNDATION/REGULAR (task_category: "foundation" or "regular")

CRITICAL REQUIREMENTS:
- scheduled_date format: YYYY-MM-DD (start from today: {today})
- All DoD weights must sum to 100
- Be CONCRETE & SPECIFIC using specifications data (exact countries, programs, roles, numbers)
- Use search results for real names, dates, links when available
- Match deliverable_type to the actual task output
- Add lets_go_inputs only for copilot tasks
- Include Quick Wins from onboarding as first tasks if user selected any
- Every task MUST have numbers (e.g., "3 programs", "2 applications", "45 minutes")
- Every task MUST reference specific constraints from specifications (e.g., "UK", "MSc CS", "£30k")

EXAMPLES OF GOOD vs BAD TASKS:

Study Goal (MSc CS in UK, £30k budget, Sep 2026):
✅ GOOD: "Research 3 MSc CS programs in UK under £30k for Sep 2026 intake → comparison spreadsheet"
❌ BAD: "Research universities"

✅ GOOD: "Complete IELTS practice reading test (Cambridge 14, Test 1) → score 7.0+ → result sheet"
❌ BAD: "Prepare for IELTS"

Career Goal (PM in Fintech, 3 years exp):
✅ GOOD: "Apply to 2 PM roles at fintech startups on LinkedIn (saved jobs) → application confirmations"
❌ BAD: "Apply to jobs"

✅ GOOD: "Draft cold email to Sarah Johnson (VP Product at Stripe) → personalized email draft"
❌ BAD: "Network with people"

Sport Goal (Gym, build muscle, 6hrs/week):
✅ GOOD: "Complete chest workout: 4x8 bench press, 3x12 cable flies, 3x15 pushups → workout log"
❌ BAD: "Go to gym"

✅ GOOD: "Plan meal prep for week: 150g protein/day, 2500 cal → grocery list + meal schedule"
❌ BAD: "Improve nutrition"
"""

        try:
            system_prompt = "You are an expert at creating atomic tasks with clear definitions of done."
            response = self.ai_service.call_llm(
                system_prompt,
                generation_prompt,
                response_format='json'
            )

            result = json.loads(response)
            tasks = result.get('tasks', [])

            print(f"[AtomicTaskAgent] Generated {len(tasks)} atomic tasks")

            # Validate and clean tasks
            validated_tasks = []
            for task in tasks:
                if self._validate_atomic_task(task):
                    validated_tasks.append(task)
                else:
                    print(f"[AtomicTaskAgent] Invalid task skipped: {task.get('title', 'N/A')}")

            return validated_tasks

        except Exception as e:
            print(f"[AtomicTaskAgent] Generation error: {e}")
            return []

    def _validate_task_quality(self, task: Dict) -> tuple:
        """
        Validate task quality - check for common placeholder and formatting issues.

        Returns:
            tuple: (is_valid: bool, error_message: str)
                   Returns (True, "") if task passes all quality checks
                   Returns (False, "reason") if task has quality issues
        """
        title = task.get('title', '')
        description = task.get('description', '')
        combined_text = f"{title} {description}".lower()

        # Check for common placeholder patterns
        bad_patterns = [
            ("your field", "Generic field placeholder found"),
            ("your key skills", "Generic skills placeholder found"),
            ("[mutual connection name]", "Unfilled connection placeholder found"),
            ("the company", "Generic company reference found"),
            ("o years", "Zero years formatting error (should be 'early-career')"),
            ("your target", "Generic target placeholder found"),
            ("£10/year", "Budget parsing error (missing amount)"),
            ("$10/year", "Budget parsing error (missing amount)"),
            ("{", "Unclosed template variable found"),
            ("}", "Unclosed template variable found"),
            ("your role", "Generic role placeholder found"),
            ("your industry", "Generic industry placeholder found"),
            ("your university", "Generic university placeholder found"),
        ]

        for pattern, error_msg in bad_patterns:
            if pattern in combined_text:
                return (False, f"{error_msg}: '{pattern}' found in task")

        # Check minimum length (tasks should be descriptive)
        if len(title) < 10:
            return (False, f"Task title too short: '{title}' ({len(title)} chars)")

        if len(combined_text) < 50:
            return (False, f"Task content too short: {len(combined_text)} chars")

        # Check for multiple consecutive spaces (formatting issue)
        if "  " in title or "  " in description:
            return (False, "Multiple consecutive spaces found (formatting issue)")

        # Check for missing key fields that should be specific
        if task.get('task_type') == 'copilot':
            # Copilot tasks should have specific instructions
            if len(description) < 30:
                return (False, f"Copilot task needs more detailed description ({len(description)} chars)")

        # All checks passed
        return (True, "")

    def _validate_atomic_task(self, task: Dict) -> bool:
        """
        Validate atomic task has all required fields
        """
        required_fields = [
            'title',
            'task_type',
            'timebox_minutes',
            'deliverable_type',
            'definition_of_done',
            'scheduled_date',
            'priority',
        ]

        # Check all required fields exist
        if not all(field in task for field in required_fields):
            missing = [f for f in required_fields if f not in task]
            print(f"[AtomicTaskAgent] Missing fields: {missing}")
            return False

        # Validate task_type
        if task['task_type'] not in ['auto', 'copilot', 'manual']:
            print(f"[AtomicTaskAgent] Invalid task_type: {task['task_type']}")
            return False

        # Validate definition_of_done
        dod = task.get('definition_of_done', [])
        if not dod or not isinstance(dod, list):
            print("[AtomicTaskAgent] Invalid definition_of_done")
            return False

        # Validate DoD weights sum to ~100 (allow ±5 tolerance)
        total_weight = sum(item.get('weight', 0) for item in dod)
        if not (95 <= total_weight <= 105):
            print(f"[AtomicTaskAgent] DoD weights sum to {total_weight}, expected ~100")
            return False

        # Validate deliverable_type
        valid_deliverables = [
            'spreadsheet', 'doc', 'email', 'recording', 'link',
            'shortlist', 'file', 'note', 'other'
        ]
        if task['deliverable_type'] not in valid_deliverables:
            print(f"[AtomicTaskAgent] Invalid deliverable_type: {task['deliverable_type']}")
            return False

        return True

    def _log_validation_results(self, validation_results: Dict[str, Any]) -> None:
        """
        Log validation results in a readable format.

        Week 2: Helper method for logging validation results.
        """
        print(f"[AtomicTaskAgent] Validation results:")
        print(f"   Total: {validation_results['total']} tasks")
        print(f"   Passed: {validation_results['passed']} ({validation_results['passed']/validation_results['total']*100:.0f}%)")
        print(f"   Failed: {validation_results['failed']} ({validation_results['failed']/validation_results['total']*100:.0f}%)")
        print(f"   Average quality score: {validation_results['average_score']:.0f}%")

        # Log warnings for failed tasks
        if validation_results['failed'] > 0:
            print(f"[AtomicTaskAgent] ⚠️  {validation_results['failed']} tasks failed quality checks:")
            for task, score, reasons in validation_results['failed_tasks'][:3]:  # Show first 3
                print(f"   - [{score}%] {task['title'][:60]}...")
                for reason in reasons:
                    print(f"     • {reason}")

    def _filter_failed_tasks(self, tasks: List[Dict], validator) -> List[Dict]:
        """
        Filter out tasks with score < 60% (auto-reject threshold).

        Week 2: Helper method for filtering failed tasks.
        """
        validated_tasks = []
        rejected_count = 0

        for task in tasks:
            is_valid, score, reasons = validator.validate_task(task)
            if score >= 60:  # Keep tasks with score >= 60%
                validated_tasks.append(task)
            else:
                rejected_count += 1
                print(f"[AtomicTaskAgent] 🚫 Rejected [{score}%]: {task['title'][:60]}...")
                for reason in reasons:
                    print(f"     • {reason}")

        if rejected_count > 0:
            print(f"[AtomicTaskAgent] Removed {rejected_count} tasks with score < 60%")

        return validated_tasks

    def _deduplicate_tasks(self, tasks: List[Dict]) -> List[Dict]:
        """
        Remove duplicate or very similar tasks.

        Week 2: Helper method for hybrid generation (templates + LLM).
        Deduplicates tasks based on title similarity.
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
                if similar(title, seen_title) > 0.8:  # 80% similarity threshold
                    print(f"[AtomicTaskAgent] 🔁 Duplicate task detected (skipping): {title[:60]}...")
                    is_duplicate = True
                    break

            if not is_duplicate:
                deduplicated.append(task)
                seen_titles.append(title)

        removed_count = len(tasks) - len(deduplicated)
        if removed_count > 0:
            print(f"[AtomicTaskAgent] Removed {removed_count} duplicate tasks")

        return deduplicated

    def create_tasks_from_atomic_plan(self, tasks: List[Dict]) -> List:
        """
        Create Todo objects from atomic task plan

        Args:
            tasks: List of validated atomic task dictionaries

        Returns:
            List of created Todo objects
        """
        from todos.models import Todo

        created_tasks = []

        for task_data in tasks:
            # Add user to task data
            task_data['user'] = self.user

            # Set status based on dependencies
            task_data['status'] = 'ready'  # Default status

            # Generate idempotency key
            task_data['idempotency_key'] = (
                f"{self.user.id}_{task_data['scheduled_date']}_{task_data['title'][:50]}"
            )

            # Check if task already exists
            existing = Todo.objects.filter(
                idempotency_key=task_data['idempotency_key']
            ).first()

            if existing:
                print(f"[AtomicTaskAgent] Task already exists: {task_data['title']}")
                continue

            # Create task
            try:
                task = Todo.objects.create(**task_data)
                created_tasks.append(task)
                print(f"[AtomicTaskAgent] Created task: {task.title}")
            except Exception as e:
                print(f"[AtomicTaskAgent] Error creating task: {e}")
                continue

        return created_tasks

    def _get_milestone_title(self, milestone_type) -> str:
        """
        Convert milestone_type enum to human-readable title.

        Args:
            milestone_type: MilestoneType enum value

        Returns:
            Human-readable milestone title
        """
        milestone_titles = {
            'university_research': 'Research and shortlist programs',
            'exam_prep': 'Prepare for standardized tests',
            'sop_drafting': 'Write statement of purpose',
            'recommendations': 'Secure recommendation letters',
            'applications': 'Submit applications',
            'scholarships': 'Find and apply for scholarships',
            'visa_process': 'Prepare visa documents',
            'linkedin_optimization': 'Optimize LinkedIn profile',
            'resume_update': 'Update resume and CV',
            'job_search': 'Search for target companies',
            'networking': 'Build professional network',
            'skill_building': 'Develop required skills',
            'interview_prep': 'Prepare for interviews',
            'job_applications': 'Submit job applications',
            'workout_plan': 'Create workout plan',
            'nutrition': 'Plan nutrition strategy',
            'progress_tracking': 'Track fitness progress'
        }

        # Convert enum to string if needed
        milestone_str = str(milestone_type.value) if hasattr(milestone_type, 'value') else str(milestone_type)
        return milestone_titles.get(milestone_str, milestone_str.replace('_', ' ').title())

    def _get_milestone_index(self, milestone_type, milestone_types: List[str]) -> int:
        """
        Get the index of milestone within the list of all milestone types.

        Args:
            milestone_type: MilestoneType enum value
            milestone_types: List of milestone types for this goal

        Returns:
            0-based index of milestone in the list
        """
        # Convert enum to string if needed
        milestone_str = str(milestone_type.value) if hasattr(milestone_type, 'value') else str(milestone_type)

        try:
            return milestone_types.index(milestone_str)
        except (ValueError, AttributeError):
            return 0
