"""
Task Intelligence Module
AI logic for determining task properties: energy level, cognitive load, hierarchy
"""


def determine_energy_and_cognitive_load(task_type: str, task_title: str, task_description: str = '') -> dict:
    """
    Determine energy_level and cognitive_load based on task characteristics

    Returns:
        {
            'energy_level': 'high' | 'medium' | 'low',
            'cognitive_load': 1-5,
            'task_level': 'action' | 'sub_goal' | 'goal',
            'estimated_energy_cost': int,
            'contribution_weight': float
        }
    """
    # Normalize inputs
    task_type_lower = task_type.lower()
    title_lower = task_title.lower()
    desc_lower = task_description.lower()

    # Initialize defaults
    energy_level = 'medium'
    cognitive_load = 3
    task_level = 'action'
    contribution_weight = 1.0

    # HIGH ENERGY tasks (morning, deep work, complex thinking)
    high_energy_keywords = [
        'write', 'draft', 'research', 'analyze', 'design', 'create', 'develop',
        'plan', 'strategy', 'statement', 'essay', 'coding', 'algorithm',
        'study', 'learn', 'prepare', 'document', 'report'
    ]

    # LOW ENERGY tasks (evening, admin, simple actions)
    low_energy_keywords = [
        'review', 'check', 'update', 'upload', 'submit', 'send', 'email',
        'schedule', 'book', 'register', 'confirm', 'track', 'log',
        'watch', 'listen', 'read', 'browse', 'scan'
    ]

    # COMPLEX tasks (high cognitive load)
    complex_keywords = [
        'personal statement', 'research paper', 'algorithm', 'complex',
        'analyze', 'strategy', 'architecture', 'design system',
        'solve', 'debug', 'optimize'
    ]

    # SIMPLE tasks (low cognitive load)
    simple_keywords = [
        'confirm', 'check', 'verify', 'track', 'log', 'update profile',
        'send email', 'register', 'book', 'watch', 'listen'
    ]

    # SUB-GOAL indicators (milestone-level tasks)
    sub_goal_keywords = [
        'prepare documents', 'gather', 'compile', 'collect all',
        'complete application', 'finish', 'submit application'
    ]

    # Determine ENERGY LEVEL
    if any(keyword in title_lower or keyword in desc_lower for keyword in high_energy_keywords):
        energy_level = 'high'
    elif any(keyword in title_lower or keyword in desc_lower for keyword in low_energy_keywords):
        energy_level = 'low'

    # Task type overrides
    if task_type_lower in ['research', 'writing', 'preparation', 'form', 'practice']:
        energy_level = 'high'
    elif task_type_lower in ['submission', 'upload', 'follow-up', 'tracking', 'media']:
        energy_level = 'low'
    elif task_type_lower in ['communication', 'outreach', 'application', 'event']:
        energy_level = 'medium'

    # Determine COGNITIVE LOAD
    if any(keyword in title_lower or keyword in desc_lower for keyword in complex_keywords):
        cognitive_load = 5
    elif any(keyword in title_lower or keyword in desc_lower for keyword in simple_keywords):
        cognitive_load = 1
    elif energy_level == 'high':
        cognitive_load = 4
    elif energy_level == 'low':
        cognitive_load = 2
    else:
        cognitive_load = 3

    # Task type-specific cognitive loads
    cognitive_load_by_type = {
        'research': 5,
        'writing': 5,
        'form': 4,
        'preparation': 4,
        'application': 4,
        'practice': 3,
        'vocabulary': 3,
        'speaking': 3,
        'workout': 2,
        'tracking': 2,
        'media': 1,
        'submission': 2,
        'upload': 2,
        'follow-up': 1,
        'communication': 3,
        'outreach': 3,
        'event': 2,
        'mentorship': 3,
        'community': 2,
    }
    if task_type_lower in cognitive_load_by_type:
        cognitive_load = cognitive_load_by_type[task_type_lower]

    # Determine TASK LEVEL
    if any(keyword in title_lower for keyword in sub_goal_keywords):
        task_level = 'sub_goal'
        contribution_weight = 0.3  # Sub-goals contribute 30%
    elif 'review' in title_lower and 'progress' in title_lower:
        task_level = 'sub_goal'
        contribution_weight = 0.2  # Review tasks contribute 20%
    else:
        task_level = 'action'
        contribution_weight = 1.0  # Actions are full weight

    # Calculate ESTIMATED ENERGY COST (timebox_minutes * cognitive_load)
    # We'll use default timebox of 30-60 minutes depending on type
    default_timeboxes = {
        'research': 60,
        'writing': 90,
        'form': 45,
        'preparation': 60,
        'application': 45,
        'practice': 30,
        'vocabulary': 20,
        'speaking': 30,
        'workout': 45,
        'tracking': 15,
        'media': 30,
        'submission': 20,
        'upload': 15,
        'follow-up': 10,
        'communication': 30,
        'outreach': 30,
        'event': 120,
        'mentorship': 60,
        'community': 20,
    }
    timebox = default_timeboxes.get(task_type_lower, 30)
    estimated_energy_cost = timebox * cognitive_load

    return {
        'energy_level': energy_level,
        'cognitive_load': cognitive_load,
        'task_level': task_level,
        'contribution_weight': contribution_weight,
        'estimated_energy_cost': estimated_energy_cost,
        'timebox_minutes': timebox,
    }


def suggest_best_time_of_day(energy_level: str, user_energy_peak: str = 'morning') -> str:
    """
    Suggest best time of day for this task based on energy requirements and user's peak

    Args:
        energy_level: 'high' | 'medium' | 'low'
        user_energy_peak: 'morning' | 'afternoon' | 'evening' | 'night'

    Returns:
        Suggested time of day
    """
    # High energy tasks → user's peak time
    if energy_level == 'high':
        return user_energy_peak

    # Medium energy → afternoon (universal good time)
    if energy_level == 'medium':
        return 'afternoon'

    # Low energy → opposite of user's peak (save peak for important stuff)
    if energy_level == 'low':
        if user_energy_peak == 'morning':
            return 'evening'
        elif user_energy_peak == 'evening':
            return 'morning'
        else:
            return 'evening'

    return 'afternoon'  # Default


def calculate_category_progress(user, category: str = None) -> dict:
    """
    Calculate completion percentage for goal categories

    Returns:
        {
            'study': {'completed': 15, 'total': 20, 'percentage': 75, 'on_track': True},
            'language': {'completed': 8, 'total': 12, 'percentage': 67, 'on_track': True},
            ...
        }
    """
    from todos.models import Todo
    from datetime import datetime, timedelta

    # Get all tasks for user
    if category:
        tasks = Todo.objects.filter(
            user=user,
            goalspec__category=category,
            created_at__gte=datetime.now() - timedelta(days=30)  # Last 30 days
        )
    else:
        tasks = Todo.objects.filter(
            user=user,
            created_at__gte=datetime.now() - timedelta(days=30)
        )

    # Group by category
    progress = {}
    categories = tasks.values_list('goalspec__category', flat=True).distinct()

    for cat in categories:
        if not cat:
            continue

        cat_tasks = tasks.filter(goalspec__category=cat)
        total = cat_tasks.count()
        completed = cat_tasks.filter(status='done').count()
        percentage = int((completed / total * 100)) if total > 0 else 0

        # Determine if on track (>60% completion)
        on_track = percentage >= 60

        progress[cat] = {
            'completed': completed,
            'total': total,
            'percentage': percentage,
            'on_track': on_track,
        }

    return progress


def analyze_skip_patterns(user, days_back: int = 14) -> dict:
    """
    Analyze why user skips tasks

    Returns:
        {
            'total_skipped': 12,
            'reasons': {
                'no_time': 7,
                'no_motivation': 3,
                'distracted': 2,
            },
            'top_reason': 'no_time',
            'skip_rate': 0.32,  # 32% of tasks skipped
        }
    """
    from todos.advanced_models import TaskCompletion
    from datetime import datetime, timedelta

    start_date = datetime.now() - timedelta(days=days_back)
    completions = TaskCompletion.objects.filter(
        user=user,
        completed_at__gte=start_date
    )

    total_tasks = completions.count()
    skipped = completions.filter(completion_reason__startswith='skipped_')

    # Count reasons
    reasons = {}
    for completion in skipped:
        reason = completion.completion_reason.replace('skipped_', '')
        reasons[reason] = reasons.get(reason, 0) + 1

    # Find top reason
    top_reason = max(reasons.items(), key=lambda x: x[1])[0] if reasons else None

    # Calculate skip rate
    skip_rate = skipped.count() / total_tasks if total_tasks > 0 else 0

    return {
        'total_skipped': skipped.count(),
        'reasons': reasons,
        'top_reason': top_reason,
        'skip_rate': round(skip_rate, 2),
        'period_days': days_back,
    }
