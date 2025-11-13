"""
Celery tasks for background task generation
"""
from celery import shared_task
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta
import traceback

from vision.models import Scenario, Vision, Milestone
from vision.serializers import ScenarioSerializer, VisionSerializer
from todos.models import Todo
from todos.task_generator import TaskGenerator
from ai.services import ai_service

User = get_user_model()


@shared_task(bind=True, name='todos.generate_vision')
def generate_vision_task(self, user_id, scenario_id):
    """
    Generate vision and tasks from scenario in background

    Args:
        user_id: User ID
        scenario_id: Scenario ID to generate vision from

    Returns:
        dict with vision_id, tasks_created count, and status
    """
    try:
        # Update task state to track progress
        self.update_state(state='PROGRESS', meta={'stage': 'Loading user and scenario'})

        user = User.objects.get(id=user_id)
        scenario = Scenario.objects.get(id=scenario_id, user=user)
        scenario_data = ScenarioSerializer(scenario).data

        # Generate vision using AI (this is the slow part)
        self.update_state(state='PROGRESS', meta={'stage': 'Generating vision with AI'})
        vision_data = ai_service.generate_vision(user_id, scenario_data)

        # Deactivate old visions
        self.update_state(state='PROGRESS', meta={'stage': 'Saving vision'})
        Vision.objects.filter(user=user).update(is_active=False)

        # Create vision
        vision = Vision.objects.create(
            user=user,
            scenario=scenario,
            title=vision_data.get('title', ''),
            summary=vision_data.get('summary', ''),
            horizon_start=vision_data.get('horizon_start'),
            horizon_end=vision_data.get('horizon_end'),
            monthly_milestones=vision_data.get('monthly_milestones', [])
        )

        # Create milestones from monthly milestones JSON
        self.update_state(state='PROGRESS', meta={'stage': 'Creating milestones'})
        monthly_milestones = vision_data.get('monthly_milestones', [])
        milestone_objects = []

        for idx, monthly in enumerate(monthly_milestones):
            month_str = monthly.get('month')
            if month_str:
                try:
                    due_date = datetime.strptime(f"{month_str}-15", "%Y-%m-%d").date()
                    milestone_title = monthly.get('title') or monthly.get('goal', f'Month {idx + 1}')
                    milestone_obj = Milestone.objects.create(
                        vision=vision,
                        title=milestone_title,
                        description=monthly.get('goal', ''),
                        due_date=due_date
                    )
                    milestone_objects.append(milestone_obj)
                except Exception as e:
                    print(f"Error creating milestone {idx}: {e}")

        # Generate tasks for ALL milestones using BULK INSERT
        self.update_state(state='PROGRESS', meta={'stage': 'Generating tasks'})
        total_tasks_created = 0

        if monthly_milestones and milestone_objects:
            today = datetime.now().date()
            tasks_to_create = []  # Collect all tasks for bulk insert

            for milestone_idx, milestone_obj in enumerate(milestone_objects):
                milestone_data = monthly_milestones[milestone_idx]
                tasks = milestone_data.get('tasks', milestone_data.get('key_tasks', []))

                # Calculate date range for this milestone
                milestone_end = milestone_obj.due_date

                if milestone_idx == 0:
                    milestone_start = today
                else:
                    prev_milestone = milestone_objects[milestone_idx - 1]
                    milestone_start = prev_milestone.due_date + timedelta(days=1)

                days_available = (milestone_end - milestone_start).days
                if days_available <= 0:
                    continue

                task_count = len(tasks)

                if task_count > 0:
                    for task_idx, task in enumerate(tasks):
                        # Distribute tasks evenly across the milestone period
                        day_offset = (task_idx * days_available) // task_count
                        task_date = milestone_start + timedelta(days=day_offset)

                        # Determine priority based on position
                        if task_idx < task_count // 3:
                            priority = 3  # First third: High
                        elif task_idx < (2 * task_count) // 3:
                            priority = 2  # Middle third: Medium
                        else:
                            priority = 1  # Last third: Low

                        # Add to bulk list instead of creating individually
                        tasks_to_create.append(Todo(
                            user=user,
                            vision=vision,
                            milestone=milestone_obj,
                            title=task,
                            scheduled_date=task_date,
                            priority=priority,
                            estimated_duration_minutes=60,
                            source='ai_generated'
                        ))

            # BULK CREATE - much faster than individual creates
            if tasks_to_create:
                Todo.objects.bulk_create(tasks_to_create)
                total_tasks_created = len(tasks_to_create)
                print(f"Bulk created {total_tasks_created} tasks across {len(milestone_objects)} milestones for user {user_id}")

        return {
            'status': 'success',
            'vision_id': vision.id,
            'tasks_created': total_tasks_created,
            'milestones_created': len(milestone_objects)
        }

    except User.DoesNotExist:
        return {'status': 'error', 'error': 'User not found'}
    except Scenario.DoesNotExist:
        return {'status': 'error', 'error': 'Scenario not found'}
    except Exception as e:
        error_msg = f'Failed to generate vision: {str(e)}'
        print(f"ERROR in generate_vision_task: {error_msg}")
        print(traceback.format_exc())
        return {'status': 'error', 'error': error_msg}


@shared_task(bind=True, name='todos.generate_monthly_tasks')
def generate_monthly_tasks_task(self, user_id):
    """
    Generate tasks for current month from vision in background

    Args:
        user_id: User ID

    Returns:
        dict with tasks_created count and status
    """
    try:
        self.update_state(state='PROGRESS', meta={'stage': 'Loading user'})

        user = User.objects.get(id=user_id)

        # Use advanced generator
        self.update_state(state='PROGRESS', meta={'stage': 'Generating tasks with AI'})
        generator = TaskGenerator(user)
        tasks_created = generator.generate_tasks_for_current_month()

        # If that didn't work, use simple fallback
        if tasks_created == 0:
            self.update_state(state='PROGRESS', meta={'stage': 'Using fallback generator'})
            print("Advanced generator created 0 tasks, using simple fallback")
            from todos.views import generate_simple_tasks
            tasks_created = generate_simple_tasks(user)

        return {
            'status': 'success',
            'tasks_created': tasks_created,
            'message': f'Generated {tasks_created} tasks for current month'
        }

    except User.DoesNotExist:
        return {'status': 'error', 'error': 'User not found'}
    except Exception as e:
        error_msg = f'Failed to generate tasks: {str(e)}'
        print(f"ERROR in generate_monthly_tasks_task: {error_msg}")
        print(traceback.format_exc())
        return {'status': 'error', 'error': error_msg}
