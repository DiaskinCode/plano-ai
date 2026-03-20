"""
Simple but SMART task generator
Creates actionable tasks even without perfect vision data
"""
from datetime import datetime, timedelta, time
from .models import Todo
from vision.models import Vision
from users.models import User, UserProfile


def generate_simple_tasks(user: User) -> int:
    """Generate smart default tasks based on user's goals and vision"""

    # Get user's vision and profile
    vision = Vision.objects.filter(user=user).order_by('-created_at').first()  # Get latest even if not active
    profile = UserProfile.objects.filter(user=user).first()

    if not vision and not profile:
        print(f"No vision or profile for user {user.id}")
        return 0

    # Delete old AI-generated tasks
    Todo.objects.filter(
        user=user,
        source='ai_generated',
        status='pending'
    ).delete()

    today = datetime.now().date()
    tasks_created = 0

    # Method 1: Try to extract from vision milestones
    if vision and vision.monthly_milestones and len(vision.monthly_milestones) > 0:
        print(f"Using vision milestones to create tasks")

        # Use first milestone (most current)
        first_milestone = vision.monthly_milestones[0]
        goal = first_milestone.get('goal', '')
        key_tasks = first_milestone.get('key_tasks', [])

        if key_tasks and len(key_tasks) > 0:
            print(f"Found {len(key_tasks)} key tasks in milestone")

            # Categorize tasks into daily routines and one-time tasks
            daily_tasks = []
            one_time_tasks = []

            for task in key_tasks:
                task_lower = task.lower()
                # Check if it's a daily routine
                is_daily = any(word in task_lower for word in
                             ['daily', 'every day', 'practice', 'study', 'review', 'prepare', 'read', 'exercise'])

                if is_daily:
                    daily_tasks.append(task)
                else:
                    one_time_tasks.append(task)

            # Create daily routine tasks for next 30 days
            for task in daily_tasks:
                for day in range(30):
                    Todo.objects.create(
                        user=user,
                        vision=vision,
                        title=task,
                        scheduled_date=today + timedelta(days=day),
                        scheduled_time=time(9, 0),  # Morning
                        priority=3,
                        estimated_duration_minutes=60,
                        source='ai_generated'
                    )
                    tasks_created += 1

            # Distribute one-time tasks throughout the month
            for i, task in enumerate(one_time_tasks):
                days_offset = (i * 30) // max(1, len(one_time_tasks))
                task_date = today + timedelta(days=days_offset)

                Todo.objects.create(
                    user=user,
                    vision=vision,
                    title=task,
                    scheduled_date=task_date,
                    scheduled_time=time(10, 0),
                    priority=2,
                    estimated_duration_minutes=90,
                    source='ai_generated'
                )
                tasks_created += 1

            if tasks_created > 0:
                print(f"Created {tasks_created} tasks from vision milestones")
                return tasks_created

        # If no key_tasks, create weekly milestones based on goal
        if goal:
            print(f"Creating weekly milestones based on goal: {goal}")
            weeks = ['Week 1', 'Week 2', 'Week 3', 'Week 4']

            for week_num, week_name in enumerate(weeks):
                # Create 5 tasks per week (Mon-Fri)
                for day_in_week in range(5):
                    day_offset = (week_num * 7) + day_in_week
                    task_date = today + timedelta(days=day_offset)

                    # Create specific tasks based on week
                    if week_num == 0:
                        task_titles = [
                            f"Research and understand: {goal[:40]}",
                            f"Create action plan for: {goal[:40]}",
                            f"Identify resources needed for {goal[:30]}",
                            f"Set up systems and tools",
                            f"Weekly review: Progress on {goal[:30]}"
                        ]
                    elif week_num == 1:
                        task_titles = [
                            f"Execute step 1 of {goal[:35]}",
                            f"Build foundation for {goal[:35]}",
                            f"Connect with mentors/experts",
                            f"Develop key skills for {goal[:30]}",
                            f"Weekly review: Adjust strategy"
                        ]
                    elif week_num == 2:
                        task_titles = [
                            f"Execute step 2 of {goal[:35]}",
                            f"Expand work on {goal[:40]}",
                            f"Seek feedback and iterate",
                            f"Overcome blockers",
                            f"Weekly review: Measure progress"
                        ]
                    else:  # Week 4
                        task_titles = [
                            f"Final push on {goal[:40]}",
                            f"Complete deliverables",
                            f"Prepare for next month's goals",
                            f"Document learnings and wins",
                            f"Monthly review: Celebrate progress"
                        ]

                    Todo.objects.create(
                        user=user,
                        vision=vision,
                        title=task_titles[day_in_week],
                        scheduled_date=task_date,
                        scheduled_time=time(10, 0),
                        priority=3 if day_in_week < 3 else 2,
                        estimated_duration_minutes=90,
                        source='ai_generated'
                    )
                    tasks_created += 1

            print(f"Created {tasks_created} weekly milestone tasks")
            return tasks_created

    # Method 2: Fallback - Create weekly milestone tasks based on profile goals
    if profile and (profile.future_goals or profile.dream_career):
        print(f"Creating tasks based on profile goals")

        goal = profile.future_goals or profile.dream_career or "Achieve your goals"
        career = profile.dream_career or "your dream career"

        # Create structured weekly plan
        weeks = ['Week 1: Foundation', 'Week 2: Building', 'Week 3: Executing', 'Week 4: Advancing']

        for week_num, week_phase in enumerate(weeks):
            # Create 5 tasks per week (Mon-Fri)
            for day_in_week in range(5):
                day_offset = (week_num * 7) + day_in_week
                task_date = today + timedelta(days=day_offset)

                # Create specific tasks based on week and day
                if week_num == 0:  # Foundation week
                    task_templates = [
                        f"Research: What does success look like in {career}?",
                        f"Create 30-day action plan for {goal[:30]}",
                        f"Identify 3 key resources/tools needed",
                        f"Network: Connect with 2 people in {career[:30]}",
                        f"Weekly review: Set clear next steps"
                    ]
                elif week_num == 1:  # Building week
                    task_templates = [
                        f"Skill development: Learn core skill for {career[:30]}",
                        f"Build project/portfolio piece",
                        f"Apply learnings to real-world task",
                        f"Get feedback from mentor or peer",
                        f"Weekly review: Adjust based on feedback"
                    ]
                elif week_num == 2:  # Executing week
                    task_templates = [
                        f"Execute major milestone toward {goal[:35]}",
                        f"Expand network: Attend event or join community",
                        f"Solve a key challenge or blocker",
                        f"Create tangible output or deliverable",
                        f"Weekly review: Track measurable progress"
                    ]
                else:  # Advancing week
                    task_templates = [
                        f"Advanced work on {goal[:40]}",
                        f"Showcase work or share with others",
                        f"Plan next month's ambitious goals",
                        f"Document wins and lessons learned",
                        f"Monthly review: Celebrate and strategize"
                    ]

                Todo.objects.create(
                    user=user,
                    vision=vision,
                    title=task_templates[day_in_week],
                    scheduled_date=task_date,
                    scheduled_time=time(9, 0) if day_in_week < 3 else time(14, 0),
                    priority=3 if day_in_week < 2 else 2,
                    estimated_duration_minutes=90,
                    source='ai_generated'
                )
                tasks_created += 1

        print(f"Created {tasks_created} structured weekly tasks")
        return tasks_created

    print("Could not create any tasks - no data available")
    return 0
