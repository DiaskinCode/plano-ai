"""
Automatic task generation from vision milestones
Creates daily routine tasks + monthly milestone tasks
"""
from datetime import datetime, timedelta, time
from typing import List, Dict
from .models import Todo
from vision.models import Vision, Milestone
from users.models import User, UserProfile
from ai.task_agent import TaskAgent


class TaskGenerator:
    """Generate tasks from vision milestones"""

    def __init__(self, user: User):
        self.user = user
        self.vision = Vision.objects.filter(user=user, is_active=True).first()

    def generate_tasks_for_current_month(self) -> int:
        """Generate all tasks for current month based on current milestone"""
        if not self.vision:
            print(f"No active vision found for user {self.user.id}")
            return 0

        print(f"Found vision: {self.vision.title}")
        print(f"Monthly milestones: {len(self.vision.monthly_milestones)}")

        today = datetime.now().date()
        current_month = today.strftime('%Y-%m')
        print(f"Current month: {current_month}")

        # Find current month's milestone OR use first available milestone
        current_milestone = None
        current_milestone_obj = None  # DB milestone object

        # Get milestone objects from database
        db_milestones = Milestone.objects.filter(vision=self.vision).order_by('due_date')

        # First, try to find exact month match
        for milestone in self.vision.monthly_milestones:
            milestone_month = milestone.get('month', '')
            print(f"Checking milestone month: {milestone_month}")
            if milestone_month == current_month:
                current_milestone = milestone
                # Find corresponding DB milestone
                milestone_title = milestone.get('title', '')
                current_milestone_obj = db_milestones.filter(title=milestone_title).first()
                print(f"Found exact match for current month: {milestone_title}")
                break

        # If no exact match, use the FIRST milestone (most recent/current one)
        if not current_milestone and self.vision.monthly_milestones:
            current_milestone = self.vision.monthly_milestones[0]
            current_milestone_obj = db_milestones.first()  # Get first DB milestone
            print(f"Using first milestone as fallback")
            print(f"Milestone: {current_milestone.get('goal', 'No goal')}")

        if not current_milestone:
            print("No milestones found in vision")
            return 0

        # Delete existing AI-generated tasks for this month
        Todo.objects.filter(
            user=self.user,
            vision=self.vision,
            source__in=['ai_generated', 'ai_agent'],  # Delete both old AI types
            scheduled_date__year=today.year,
            scheduled_date__month=today.month,
            status='pending'
        ).delete()

        # ⭐ NEW: Try intelligent agent first
        try:
            user_profile = UserProfile.objects.get(user=self.user)
            agent = TaskAgent(self.user.id)

            print("[TaskGenerator] Using intelligent agent with web search...")
            enriched_tasks = agent.plan_and_search(current_milestone, user_profile)

            if enriched_tasks and len(enriched_tasks) > 0:
                tasks_created = self._create_tasks_from_agent(
                    enriched_tasks,
                    current_milestone_obj
                )
                print(f"[TaskGenerator] Agent created {tasks_created} enriched tasks")
                return tasks_created
            else:
                print("[TaskGenerator] Agent returned no tasks, falling back to standard generation")

        except UserProfile.DoesNotExist:
            print("[TaskGenerator] No user profile found, skipping agent")
        except Exception as e:
            print(f"[TaskGenerator] Agent failed: {e}, falling back to standard generation")

        # Fallback to original logic if agent fails
        tasks_created = 0

        # 1. Create DAILY ROUTINE tasks for the entire month
        routine_tasks = self._extract_routine_tasks(current_milestone)
        tasks_created += self._create_daily_routines(routine_tasks, today, current_milestone_obj)

        # 2. Create ONE-TIME milestone tasks distributed throughout month
        one_time_tasks = self._extract_one_time_tasks(current_milestone)
        tasks_created += self._create_monthly_tasks(one_time_tasks, today, current_milestone_obj)

        return tasks_created

    def _create_tasks_from_agent(
        self,
        enriched_tasks: List[Dict],
        milestone_obj
    ) -> int:
        """
        Create database tasks from agent output

        Args:
            enriched_tasks: List of task dicts from TaskAgent
            milestone_obj: Database milestone object to link tasks to

        Returns:
            Number of tasks created
        """
        tasks_created = 0

        for task_data in enriched_tasks:
            try:
                # Parse date (handle both string and date objects)
                scheduled_date = task_data.get('scheduled_date')
                if isinstance(scheduled_date, str):
                    scheduled_date = datetime.strptime(scheduled_date, '%Y-%m-%d').date()

                # Parse time (handle both string and time objects)
                scheduled_time = task_data.get('scheduled_time')
                if isinstance(scheduled_time, str) and scheduled_time:
                    from datetime import time as dt_time
                    hour, minute = scheduled_time.split(':')
                    scheduled_time = dt_time(int(hour), int(minute))

                # Create task
                Todo.objects.create(
                    user=self.user,
                    vision=self.vision,
                    milestone=milestone_obj,
                    title=task_data['title'],
                    scheduled_date=scheduled_date,
                    scheduled_time=scheduled_time,
                    priority=task_data.get('priority', 2),
                    estimated_duration_minutes=task_data.get('duration_minutes', 60),
                    external_url=task_data.get('external_url', ''),
                    notes=task_data.get('notes', ''),
                    source='ai_agent'  # Mark as agent-generated
                )
                tasks_created += 1

            except Exception as e:
                print(f"[TaskGenerator] Error creating task from agent: {e}")
                print(f"Task data: {task_data}")
                continue

        return tasks_created

    def _extract_routine_tasks(self, milestone: Dict) -> List[Dict]:
        """Extract daily routine tasks from milestone"""
        routine_tasks = []
        key_tasks = milestone.get('key_tasks', [])

        # Keywords that indicate daily/routine tasks
        routine_keywords = [
            'daily', 'every day', 'practice', 'study', 'review',
            'prepare', 'min', 'hour', 'read', 'exercise'
        ]

        for task in key_tasks:
            task_lower = task.lower()
            # Check if it's a routine task
            if any(keyword in task_lower for keyword in routine_keywords):
                # Extract duration if mentioned
                duration = 60  # Default 1 hour
                if 'hour' in task_lower:
                    if '2' in task_lower or 'two' in task_lower:
                        duration = 120
                    elif '30 min' in task_lower or 'half' in task_lower:
                        duration = 30
                elif 'min' in task_lower:
                    # Try to extract number
                    words = task_lower.split()
                    for i, word in enumerate(words):
                        if word == 'min' and i > 0:
                            try:
                                duration = int(''.join(c for c in words[i-1] if c.isdigit()))
                            except:
                                pass

                routine_tasks.append({
                    'title': task,
                    'duration': duration,
                    'priority': 3,  # High priority for daily routines
                    'time': time(9, 0) if 'morning' in task_lower else time(19, 0)
                })

        # If no routine tasks found, create one based on goal
        if not routine_tasks:
            goal = milestone.get('goal', '')
            if goal:
                routine_tasks.append({
                    'title': f"Work on: {goal[:50]}",
                    'duration': 60,
                    'priority': 2,
                    'time': time(9, 0)
                })

        return routine_tasks

    def _extract_one_time_tasks(self, milestone: Dict) -> List[str]:
        """Extract one-time milestone tasks"""
        one_time_tasks = []
        key_tasks = milestone.get('key_tasks', [])

        routine_keywords = [
            'daily', 'every day', 'practice', 'study', 'review',
            'prepare', 'min', 'hour', 'read', 'exercise'
        ]

        for task in key_tasks:
            task_lower = task.lower()
            # If it's NOT a routine task, it's a one-time task
            if not any(keyword in task_lower for keyword in routine_keywords):
                one_time_tasks.append(task)

        return one_time_tasks

    def _create_daily_routines(self, routine_tasks: List[Dict], start_date, milestone_obj=None) -> int:
        """Create daily routine tasks for entire month"""
        if not routine_tasks:
            return 0

        # Get last day of current month
        next_month = start_date.replace(day=28) + timedelta(days=4)
        last_day = (next_month - timedelta(days=next_month.day)).day

        tasks_created = 0

        # Create routine tasks for each day of the month
        for day in range(start_date.day, last_day + 1):
            current_date = start_date.replace(day=day)

            # Skip if date is in the past
            if current_date < datetime.now().date():
                continue

            for routine in routine_tasks:
                Todo.objects.create(
                    user=self.user,
                    vision=self.vision,
                    milestone=milestone_obj,  # Link to milestone
                    title=routine['title'],
                    scheduled_date=current_date,
                    scheduled_time=routine.get('time'),
                    priority=routine['priority'],
                    estimated_duration_minutes=routine['duration'],
                    source='ai_generated'
                )
                tasks_created += 1

        return tasks_created

    def _create_monthly_tasks(self, one_time_tasks: List[str], start_date, milestone_obj=None) -> int:
        """Distribute one-time tasks throughout the month"""
        if not one_time_tasks:
            return 0

        # Get last day of current month
        next_month = start_date.replace(day=28) + timedelta(days=4)
        last_day_of_month = next_month - timedelta(days=next_month.day)
        days_remaining = (last_day_of_month - start_date).days + 1

        # Distribute tasks evenly
        tasks_per_week = max(1, len(one_time_tasks) // 4)  # Spread over 4 weeks
        tasks_created = 0

        for i, task in enumerate(one_time_tasks):
            # Distribute throughout the month
            days_offset = (i * days_remaining) // len(one_time_tasks)
            task_date = start_date + timedelta(days=days_offset)

            # Assign priority based on position
            if i < len(one_time_tasks) // 3:
                priority = 3  # First third: High
            elif i < (2 * len(one_time_tasks)) // 3:
                priority = 2  # Middle third: Medium
            else:
                priority = 1  # Last third: Low

            Todo.objects.create(
                user=self.user,
                vision=self.vision,
                milestone=milestone_obj,  # Link to milestone
                title=task,
                scheduled_date=task_date,
                scheduled_time=time(10, 0),  # Default 10 AM
                priority=priority,
                estimated_duration_minutes=90,  # 1.5 hours for one-time tasks
                source='ai_generated'
            )
            tasks_created += 1

        return tasks_created

    def check_and_regenerate_if_month_ended(self) -> int:
        """Check if month ended and regenerate tasks for new month"""
        if not self.vision:
            return 0

        today = datetime.now().date()
        current_month = today.strftime('%Y-%m')

        # Check if we have tasks for current month
        current_month_tasks = Todo.objects.filter(
            user=self.user,
            vision=self.vision,
            scheduled_date__year=today.year,
            scheduled_date__month=today.month,
            source='ai_generated'
        ).count()

        # If no tasks for current month, generate them
        if current_month_tasks == 0:
            return self.generate_tasks_for_current_month()

        return 0


def generate_tasks_for_user(user_id: int) -> Dict:
    """Helper function to generate tasks for a user"""
    try:
        user = User.objects.get(id=user_id)
        generator = TaskGenerator(user)
        tasks_created = generator.generate_tasks_for_current_month()
        return {
            'success': True,
            'tasks_created': tasks_created,
            'message': f'Created {tasks_created} tasks for {user.email}'
        }
    except User.DoesNotExist:
        return {
            'success': False,
            'error': 'User not found'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
