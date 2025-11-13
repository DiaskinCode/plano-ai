"""
Script to add milestone metadata to existing tasks that don't have it.
This updates tasks created before the milestone feature was implemented.
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pathaibackend.settings')
django.setup()

from todos.models import Todo
from users.goalspec_models import GoalSpec

# Milestone mappings by category
MILESTONE_MAPPINGS = {
    'study': [
        ('university_research', 'Research and shortlist programs', 0),
        ('exam_prep', 'Prepare for standardized tests', 1),
        ('sop_drafting', 'Write statement of purpose', 2),
        ('recommendations', 'Secure recommendation letters', 3),
        ('applications', 'Submit applications', 4),
        ('scholarships', 'Find and apply for scholarships', 5),
        ('visa_process', 'Prepare visa documents', 6),
    ],
    'career': [
        ('linkedin_optimization', 'Optimize LinkedIn profile', 0),
        ('resume_update', 'Update resume and CV', 1),
        ('job_search', 'Search for target companies', 2),
        ('networking', 'Build professional network', 3),
        ('skill_building', 'Develop required skills', 4),
        ('interview_prep', 'Prepare for interviews', 5),
        ('job_applications', 'Submit job applications', 6),
    ],
    'sport': [
        ('workout_plan', 'Create workout plan', 0),
        ('nutrition', 'Plan nutrition strategy', 1),
        ('progress_tracking', 'Track fitness progress', 2),
    ]
}

def infer_milestone_from_task(task, goal_category):
    """
    Infer which milestone a task belongs to based on its title/description.

    Args:
        task: Todo instance
        goal_category: Category of the goal (study, career, sport)

    Returns:
        Tuple of (milestone_title, milestone_index) or (None, None)
    """
    if goal_category not in MILESTONE_MAPPINGS:
        return None, None

    title_lower = task.title.lower()
    description_lower = task.description.lower() if task.description else ''

    milestones = MILESTONE_MAPPINGS[goal_category]

    # Keywords for each milestone type
    keywords = {
        'university_research': ['research', 'university', 'program', 'shortlist', 'website', 'explore', 'browse'],
        'exam_prep': ['ielts', 'toefl', 'gre', 'gmat', 'test', 'exam', 'score', 'practice'],
        'sop_drafting': ['sop', 'statement', 'purpose', 'essay', 'write', 'draft', 'motivation'],
        'recommendations': ['recommendation', 'reference', 'letter', 'professor', 'mentor', 'lor'],
        'applications': ['application', 'apply', 'submit', 'portal', 'form', 'deadline'],
        'scholarships': ['scholarship', 'funding', 'financial', 'aid', 'grant'],
        'visa_process': ['visa', 'passport', 'document', 'embassy', 'immigration'],
        'linkedin_optimization': ['linkedin', 'profile', 'headline', 'summary', 'connection'],
        'resume_update': ['resume', 'cv', 'curriculum', 'vitae'],
        'job_search': ['job', 'company', 'target', 'employer', 'search'],
        'networking': ['network', 'connect', 'reach out', 'coffee chat', 'informational'],
        'skill_building': ['skill', 'learn', 'course', 'training', 'practice', 'develop'],
        'interview_prep': ['interview', 'behavioral', 'technical', 'mock', 'preparation'],
        'job_applications': ['application', 'apply', 'submit', 'job board', 'referral'],
        'workout_plan': ['workout', 'exercise', 'routine', 'training', 'gym'],
        'nutrition': ['nutrition', 'diet', 'meal', 'calories', 'protein', 'eat'],
        'progress_tracking': ['track', 'progress', 'weight', 'measurement', 'photos'],
    }

    # Try to match task to a milestone
    best_match = None
    best_match_count = 0

    for milestone_type, milestone_title, milestone_index in milestones:
        if milestone_type not in keywords:
            continue

        match_count = 0
        for keyword in keywords[milestone_type]:
            if keyword in title_lower or keyword in description_lower:
                match_count += 1

        if match_count > best_match_count:
            best_match_count = match_count
            best_match = (milestone_title, milestone_index)

    # If we found a good match (at least 1 keyword), return it
    if best_match_count > 0:
        return best_match

    # Default to first milestone if no match
    return milestones[0][1], milestones[0][2]

def update_tasks_with_milestones():
    """
    Update all tasks that don't have milestone metadata.
    """
    print("=" * 80)
    print("ADDING MILESTONE METADATA TO EXISTING TASKS")
    print("=" * 80)

    # Get all tasks with goalspecs that don't have milestone metadata
    tasks_without_milestones = Todo.objects.filter(goalspec__isnull=False)

    updated_count = 0
    skipped_count = 0

    for task in tasks_without_milestones:
        # Check if task already has milestone metadata
        if isinstance(task.notes, dict):
            if 'milestone_title' in task.notes and 'milestone_index' in task.notes:
                skipped_count += 1
                continue

        # Get the goal category
        goal = task.goalspec
        if not goal:
            continue

        # Infer milestone
        milestone_title, milestone_index = infer_milestone_from_task(task, goal.category)

        if milestone_title is None:
            print(f"⚠️  Could not infer milestone for task: {task.title[:60]}...")
            continue

        # Update notes field with milestone metadata
        if not isinstance(task.notes, dict):
            task.notes = {}

        task.notes['milestone_title'] = milestone_title
        task.notes['milestone_index'] = milestone_index
        task.save(update_fields=['notes'])

        updated_count += 1
        print(f"✅ Task: {task.title[:50]}...")
        print(f"   → Milestone: {milestone_title} (index {milestone_index})")

    print("=" * 80)
    print(f"✅ Updated {updated_count} tasks")
    print(f"⏭️  Skipped {skipped_count} tasks (already have milestone metadata)")
    print("=" * 80)

if __name__ == '__main__':
    update_tasks_with_milestones()
