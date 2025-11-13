"""
Daily Planner Service
Generates daily task lists based on GoalSpec configurations and cadences

Core Logic:
1. Fetch user's active GoalSpecs
2. Calculate daily time allocation by priority weights
3. Apply goal-type-specific cadences (Study/Career/Sport patterns)
4. Generate balanced daily tasks with dependencies
5. Respect timeboxes and avoid overloading
"""

from datetime import date, timedelta
from typing import List, Dict, Any
from django.db.models import Q
from django.utils import timezone

from .models import Todo
from users.goalspec_models import GoalSpec


class DailyPlanner:
    """
    Generates optimized daily task lists based on user's goals and constraints
    """

    def __init__(self, user):
        self.user = user
        self.today = timezone.now().date()

    def generate_daily_plan(self, target_date: date = None) -> List[Dict[str, Any]]:
        """
        Generate daily plan for a specific date

        Args:
            target_date: Date to plan for (defaults to today)

        Returns:
            List of task data dictionaries ready to create Todo objects
        """
        if target_date is None:
            target_date = self.today

        # 1. Get active goals
        active_goals = GoalSpec.objects.filter(
            user=self.user,
            is_active=True,
            completed=False
        ).order_by('-priority_weight')

        if not active_goals.exists():
            return []

        # 2. Calculate total available time (from user profile or default)
        total_daily_minutes = self._get_total_daily_minutes()

        # 3. Allocate time by goal weights
        goal_allocations = self._allocate_time_by_goals(active_goals, total_daily_minutes)

        # 4. Generate tasks for each goal based on cadence
        daily_tasks = []
        for goal, allocated_minutes in goal_allocations:
            tasks = self._generate_tasks_for_goal(goal, target_date, allocated_minutes)
            daily_tasks.extend(tasks)

        # 5. Balance and optimize (avoid overloading)
        balanced_tasks = self._balance_tasks(daily_tasks, total_daily_minutes)

        return balanced_tasks

    def _get_total_daily_minutes(self) -> int:
        """
        Get user's total available daily minutes
        Could be from UserProfile or a default
        """
        try:
            # Assume 3-4 hours per day as default
            return 180  # 3 hours
        except:
            return 180

    def _allocate_time_by_goals(self, goals, total_minutes: int) -> List[tuple]:
        """
        Allocate daily time across goals by priority weights

        Args:
            goals: QuerySet of GoalSpec objects
            total_minutes: Total available daily minutes

        Returns:
            List of (goal, allocated_minutes) tuples
        """
        total_weight = sum(goal.priority_weight for goal in goals)
        allocations = []

        for goal in goals:
            share = goal.priority_weight / total_weight
            allocated = int(total_minutes * share)
            allocations.append((goal, allocated))

        return allocations

    def _generate_tasks_for_goal(
        self,
        goal: GoalSpec,
        target_date: date,
        allocated_minutes: int
    ) -> List[Dict[str, Any]]:
        """
        Generate tasks for a specific goal based on its cadence rules

        Args:
            goal: GoalSpec object
            target_date: Date to plan for
            allocated_minutes: Time allocated for this goal

        Returns:
            List of task data dictionaries
        """
        goal_type = goal.goal_type
        cadence_rules = goal.cadence_rules

        if goal_type == 'study':
            return self._generate_study_tasks(goal, target_date, allocated_minutes, cadence_rules)
        elif goal_type == 'career':
            return self._generate_career_tasks(goal, target_date, allocated_minutes, cadence_rules)
        elif goal_type == 'sport':
            return self._generate_sport_tasks(goal, target_date, allocated_minutes, cadence_rules)
        else:
            return self._generate_generic_tasks(goal, target_date, allocated_minutes)

    def _generate_study_tasks(
        self,
        goal: GoalSpec,
        target_date: date,
        allocated_minutes: int,
        cadence_rules: Dict
    ) -> List[Dict[str, Any]]:
        """
        Generate study-related tasks following the pattern:
        shortlist → deadlines → essays → lors → submissions

        Pattern logic:
        - Early phase: Research and shortlisting
        - Mid phase: Essays and LORs
        - Late phase: Application submissions
        """
        tasks = []

        # Determine current phase from timeline
        timeline = goal.timeline
        start_date = timeline.get('start_date')
        target_deadline = timeline.get('target_date')

        # For now, create daily research/preparation tasks
        # TODO: Implement phase detection and progression

        # Example task: Daily program research
        tasks.append({
            'title': f'Research programs for {goal.title}',
            'description': f'Find and evaluate programs matching constraints: {goal.constraints}',
            'task_type': 'copilot',
            'timebox_minutes': min(allocated_minutes, 60),
            'deliverable_type': 'shortlist',
            'constraints': goal.constraints,
            'definition_of_done': [
                {'text': 'Find at least 3 programs matching criteria', 'weight': 40, 'completed': False},
                {'text': 'Check application deadlines', 'weight': 30, 'completed': False},
                {'text': 'Note admission requirements', 'weight': 30, 'completed': False},
            ],
            'scheduled_date': target_date,
            'source': 'daily_planner',
            'status': 'ready',
            'priority': 3,
        })

        return tasks

    def _generate_career_tasks(
        self,
        goal: GoalSpec,
        target_date: date,
        allocated_minutes: int,
        cadence_rules: Dict
    ) -> List[Dict[str, Any]]:
        """
        Generate career-related tasks following weekly patterns:
        M/W/F: Apply to 2 jobs
        Tue: Reach out to 3 referrals
        Thu: Mock interviews
        """
        tasks = []
        weekday = target_date.strftime('%A')[:3]  # Mon, Tue, Wed, Thu, Fri, Sat, Sun

        # Default cadence if not specified
        default_cadence = {
            'Mon': 'apply_2',
            'Wed': 'apply_2',
            'Fri': 'apply_2',
            'Tue': 'referrals_3',
            'Thu': 'mocks_1',
        }

        cadence = cadence_rules.get('weekly', default_cadence)
        today_action = cadence.get(weekday)

        if not today_action:
            return []

        # Parse action (e.g., "apply_2" → apply, 2)
        action_parts = today_action.split('_')
        action_type = action_parts[0]
        action_count = int(action_parts[1]) if len(action_parts) > 1 else 1

        if action_type == 'apply':
            # Generate job application tasks
            for i in range(action_count):
                tasks.append({
                    'title': f'Apply to {goal.constraints.get("target_role", "role")} position #{i+1}',
                    'description': f'Find and apply to job matching: {goal.constraints}',
                    'task_type': 'copilot',
                    'timebox_minutes': min(allocated_minutes // action_count, 45),
                    'deliverable_type': 'link',
                    'constraints': goal.constraints,
                    'definition_of_done': [
                        {'text': 'Find suitable job posting', 'weight': 30, 'completed': False},
                        {'text': 'Tailor resume and cover letter', 'weight': 40, 'completed': False},
                        {'text': 'Submit application', 'weight': 30, 'completed': False},
                    ],
                    'scheduled_date': target_date,
                    'source': 'daily_planner',
                    'status': 'ready',
                    'priority': 3,
                })

        elif action_type == 'referrals':
            # Networking outreach
            tasks.append({
                'title': f'Reach out to {action_count} people for referrals',
                'description': f'Connect with professionals in {goal.constraints.get("industry", "target industry")}',
                'task_type': 'copilot',
                'timebox_minutes': min(allocated_minutes, 60),
                'deliverable_type': 'email',
                'constraints': goal.constraints,
                'definition_of_done': [
                    {'text': f'Identify {action_count} people to contact', 'weight': 30, 'completed': False},
                    {'text': 'Draft personalized messages', 'weight': 40, 'completed': False},
                    {'text': 'Send outreach messages', 'weight': 30, 'completed': False},
                ],
                'scheduled_date': target_date,
                'source': 'daily_planner',
                'status': 'ready',
                'priority': 3,
            })

        elif action_type == 'mocks':
            # Mock interview practice
            tasks.append({
                'title': f'Practice {action_count} mock interview(s)',
                'description': f'Prepare for {goal.constraints.get("target_role", "role")} interviews',
                'task_type': 'manual',
                'timebox_minutes': min(allocated_minutes, 60),
                'deliverable_type': 'recording',
                'constraints': goal.constraints,
                'definition_of_done': [
                    {'text': 'Complete mock interview session', 'weight': 60, 'completed': False},
                    {'text': 'Review and note areas for improvement', 'weight': 40, 'completed': False},
                ],
                'scheduled_date': target_date,
                'source': 'daily_planner',
                'status': 'ready',
                'priority': 2,
            })

        return tasks

    def _generate_sport_tasks(
        self,
        goal: GoalSpec,
        target_date: date,
        allocated_minutes: int,
        cadence_rules: Dict
    ) -> List[Dict[str, Any]]:
        """
        Generate sport/fitness tasks following daily patterns:
        Mon: Chest, Tue: Arms, Wed: Legs, etc.
        """
        tasks = []
        weekday = target_date.strftime('%A')[:3]

        # Default gym split if not specified
        default_cadence = {
            'Mon': 'chest',
            'Tue': 'arms',
            'Wed': 'legs',
            'Thu': 'back',
            'Fri': 'shoulders',
            'Sat': 'cardio',
            'Sun': 'rest',
        }

        cadence = cadence_rules.get('daily', default_cadence)
        today_workout = cadence.get(weekday)

        if not today_workout or today_workout == 'rest':
            return []

        sport_type = goal.constraints.get('sport_type', 'Gym')

        tasks.append({
            'title': f'{today_workout.capitalize()} workout - {sport_type}',
            'description': f'{goal.constraints.get("goal", "Training")} - {today_workout} day',
            'task_type': 'manual',
            'timebox_minutes': min(allocated_minutes, 90),
            'deliverable_type': 'note',
            'constraints': goal.constraints,
            'definition_of_done': [
                {'text': f'Complete {today_workout} exercises', 'weight': 70, 'completed': False},
                {'text': 'Log workout in app', 'weight': 30, 'completed': False},
            ],
            'scheduled_date': target_date,
            'source': 'daily_planner',
            'status': 'ready',
            'priority': 2,
        })

        return tasks

    def _generate_generic_tasks(
        self,
        goal: GoalSpec,
        target_date: date,
        allocated_minutes: int
    ) -> List[Dict[str, Any]]:
        """
        Generate generic tasks for unspecified goal types
        """
        return [{
            'title': f'Work on: {goal.title}',
            'description': goal.title,
            'task_type': 'manual',
            'timebox_minutes': allocated_minutes,
            'deliverable_type': 'other',
            'scheduled_date': target_date,
            'source': 'daily_planner',
            'status': 'ready',
            'priority': 2,
        }]

    def _balance_tasks(self, tasks: List[Dict], total_minutes: int) -> List[Dict]:
        """
        Ensure total task timebox doesn't exceed available time

        Args:
            tasks: List of task data dictionaries
            total_minutes: Total available daily minutes

        Returns:
            Balanced list of tasks
        """
        total_timebox = sum(task.get('timebox_minutes', 30) for task in tasks)

        if total_timebox <= total_minutes:
            return tasks

        # Scale down timeboxes proportionally
        scale_factor = total_minutes / total_timebox

        for task in tasks:
            original_timebox = task.get('timebox_minutes', 30)
            task['timebox_minutes'] = int(original_timebox * scale_factor)

        return tasks

    def create_tasks_from_plan(self, plan: List[Dict]) -> List[Todo]:
        """
        Create Todo objects from plan data

        Args:
            plan: List of task data dictionaries

        Returns:
            List of created Todo objects
        """
        created_tasks = []

        for task_data in plan:
            # Add user to task data
            task_data['user'] = self.user

            # Create idempotency key to prevent duplicates
            task_data['idempotency_key'] = f"{self.user.id}_{task_data['scheduled_date']}_{task_data['title'][:50]}"

            # Check if task already exists
            existing = Todo.objects.filter(idempotency_key=task_data['idempotency_key']).first()
            if existing:
                continue

            # Create task
            task = Todo.objects.create(**task_data)
            created_tasks.append(task)

        return created_tasks
