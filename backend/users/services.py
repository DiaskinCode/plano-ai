"""
Progress Calculation Service - College Application Platform

Automatically calculates and updates user progress based on completed tasks.
Tracks:
- Application progress (documents, essays, submissions)
- Essay progress (word count, completed essays)
- Test prep progress (practice tests, study tasks)
- Overall completion percentage
"""

from django.db.models import Count, Q, F, Sum, Case, When, IntegerField, ExpressionWrapper
from django.db.models.functions import Coalesce
from django.utils import timezone
from datetime import timedelta
from typing import Dict, Any, List
from .models import User, UserProfile


class ProgressCalculationService:
    """Service for calculating and updating user progress stats"""

    def __init__(self, user: User):
        self.user = user
        self.profile = user.profile

    def calculate_all_progress(self) -> Dict[str, Any]:
        """
        Calculate all progress metrics for the user.
        Returns a dictionary with all progress stats.
        """
        from todos.models import Todo

        # Get all tasks for the user
        all_tasks = Todo.objects.filter(user=self.user)

        # Calculate overall progress
        total_tasks = all_tasks.count()
        completed_tasks = all_tasks.filter(status='completed').count()
        overall_progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

        # Calculate category-specific progress
        category_progress = self._calculate_category_progress(all_tasks)

        # Calculate application-specific progress
        application_progress = self._calculate_application_progress(all_tasks)

        # Calculate essay progress
        essay_progress = self._calculate_essay_progress(all_tasks)

        # Calculate test prep progress
        test_prep_progress = self._calculate_test_prep_progress(all_tasks)

        # Calculate streak data
        streak_data = self._calculate_streak(all_tasks)

        # Calculate completion timeline
        timeline_stats = self._calculate_timeline_stats(all_tasks)

        return {
            'overall': {
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks,
                'remaining_tasks': total_tasks - completed_tasks,
                'progress_percentage': round(overall_progress, 1),
            },
            'by_category': category_progress,
            'applications': application_progress,
            'essays': essay_progress,
            'test_prep': test_prep_progress,
            'streak': streak_data,
            'timeline': timeline_stats,
        }

    def _calculate_category_progress(self, all_tasks) -> List[Dict[str, Any]]:
        """Calculate progress breakdown by category"""
        from todos.models import TaskCategory

        categories = TaskCategory.objects.filter(
            tasks__user=self.user
        ).distinct()

        progress_data = []

        for category in categories:
            category_tasks = all_tasks.filter(category=category)
            total = category_tasks.count()
            completed = category_tasks.filter(status='completed').count()
            progress_pct = (completed / total * 100) if total > 0 else 0

            progress_data.append({
                'category_id': category.id,
                'category_name': category.name,
                'category_icon': category.icon,
                'category_color': category.color,
                'total_tasks': total,
                'completed_tasks': completed,
                'progress_percentage': round(progress_pct, 1),
            })

        # Sort by progress percentage (descending)
        progress_data.sort(key=lambda x: x['progress_percentage'], reverse=True)

        return progress_data

    def _calculate_application_progress(self, all_tasks) -> Dict[str, Any]:
        """Calculate application-related progress"""
        # Application categories (from Phase 1)
        app_categories = ['Documents', 'Essays', 'Applications']

        app_tasks = all_tasks.filter(category__name__in=app_categories)

        total_apps = app_tasks.count()
        completed_apps = app_tasks.filter(status='completed').count()
        app_progress = (completed_apps / total_apps * 100) if total_apps > 0 else 0

        # Count by specific application task types
        document_tasks = app_tasks.filter(category__name='Documents')
        essay_tasks = app_tasks.filter(category__name='Essays')
        submission_tasks = app_tasks.filter(category__name='Applications')

        return {
            'total_application_tasks': total_apps,
            'completed_application_tasks': completed_apps,
            'progress_percentage': round(app_progress, 1),
            'breakdown': {
                'documents': {
                    'total': document_tasks.count(),
                    'completed': document_tasks.filter(status='completed').count(),
                },
                'essays': {
                    'total': essay_tasks.count(),
                    'completed': essay_tasks.filter(status='completed').count(),
                },
                'submissions': {
                    'total': submission_tasks.count(),
                    'completed': submission_tasks.filter(status='completed').count(),
                },
            },
        }

    def _calculate_essay_progress(self, all_tasks) -> Dict[str, Any]:
        """Calculate essay-specific progress"""
        essay_tasks = all_tasks.filter(category__name='Essays')

        total_essays = essay_tasks.count()
        completed_essays = essay_tasks.filter(status='completed').count()

        # Calculate total word count from completed essays
        # (Assuming essays have a completion_log with word_count field)
        total_words = 0
        for task in essay_tasks.filter(status='completed'):
            if task.completion_log and isinstance(task.completion_log, dict):
                word_count = task.completion_log.get('word_count', 0)
                if isinstance(word_count, (int, float)):
                    total_words += int(word_count)

        # Average words per essay
        avg_words = (total_words / completed_essays) if completed_essays > 0 else 0

        return {
            'total_essays': total_essays,
            'completed_essays': completed_essays,
            'remaining_essays': total_essays - completed_essays,
            'total_words_written': total_words,
            'average_words_per_essay': round(avg_words),
            'progress_percentage': round(
                (completed_essays / total_essays * 100) if total_essays > 0 else 0,
                1
            ),
        }

    def _calculate_test_prep_progress(self, all_tasks) -> Dict[str, Any]:
        """Calculate test preparation progress"""
        test_categories = ['SAT Prep', 'IELTS Prep']

        test_tasks = all_tasks.filter(category__name__in=test_categories)

        total_tests = test_tasks.count()
        completed_tests = test_tasks.filter(status='completed').count()
        test_progress = (completed_tests / total_tests * 100) if total_tests > 0 else 0

        # Count practice tests completed
        practice_test_count = 0
        for task in test_tasks.filter(status='completed'):
            if 'practice test' in task.title.lower() or 'mock' in task.title.lower():
                practice_test_count += 1

        # Calculate scores from completion logs
        scores = []
        for task in test_tasks.filter(status='completed'):
            if task.completion_log and isinstance(task.completion_log, dict):
                score = task.completion_log.get('score')
                if score and isinstance(score, (int, float)):
                    scores.append(float(score))

        avg_score = (sum(scores) / len(scores)) if scores else None

        return {
            'total_test_tasks': total_tests,
            'completed_test_tasks': completed_tests,
            'practice_tests_completed': practice_test_count,
            'average_score': round(avg_score) if avg_score else None,
            'score_history': scores[-10:] if scores else [],  # Last 10 scores
            'progress_percentage': round(test_progress, 1),
        }

    def _calculate_streak(self, all_tasks) -> Dict[str, Any]:
        """Calculate task completion streak"""
        # Get completed tasks with completion dates
        completed_tasks = all_tasks.filter(
            status='completed',
            completed_at__isnull=False
        ).order_by('-completed_at')

        if not completed_tasks.exists():
            return {
                'current_streak': 0,
                'longest_streak': 0,
                'total_days_active': 0,
            }

        # Calculate current streak
        current_streak = 0
        check_date = timezone.now().date()

        while True:
            # Check if any task was completed on check_date
            if completed_tasks.filter(
                completed_at__date=check_date
            ).exists():
                current_streak += 1
                check_date -= timedelta(days=1)
            else:
                break

        # Calculate longest streak
        longest_streak = 0
        temp_streak = 0
        dates_seen = set()

        for task in completed_tasks:
            task_date = task.completed_at.date()

            if task_date not in dates_seen:
                dates_seen.add(task_date)

                # Check consecutive
                if temp_streak == 0:
                    temp_streak = 1
                else:
                    # Check if this date is consecutive with previous
                    prev_date = task_date + timedelta(days=1)
                    if completed_tasks.filter(completed_at__date=prev_date).exists():
                        temp_streak += 1
                    else:
                        temp_streak = 1

                longest_streak = max(longest_streak, temp_streak)

        # Count unique days with completed tasks
        total_days_active = completed_tasks.dates('completed_at', 'day').count()

        return {
            'current_streak': current_streak,
            'longest_streak': longest_streak,
            'total_days_active': total_days_active,
        }

    def _calculate_timeline_stats(self, all_tasks) -> Dict[str, Any]:
        """Calculate timeline-based statistics"""
        now = timezone.now()

        # Tasks completed this week
        week_ago = now - timedelta(days=7)
        completed_this_week = all_tasks.filter(
            status='completed',
            completed_at__gte=week_ago
        ).count()

        # Tasks completed this month
        month_ago = now - timedelta(days=30)
        completed_this_month = all_tasks.filter(
            status='completed',
            completed_at__gte=month_ago
        ).count()

        # Upcoming tasks (not completed, scheduled in future)
        upcoming_tasks = all_tasks.filter(
            status__in=['pending', 'in_progress'],
            scheduled_date__gte=now.date()
        ).count()

        # Overdue tasks
        overdue_tasks = all_tasks.filter(
            status__in=['pending', 'in_progress'],
            scheduled_date__lt=now.date()
        ).count()

        return {
            'completed_this_week': completed_this_week,
            'completed_this_month': completed_this_month,
            'upcoming_tasks': upcoming_tasks,
            'overdue_tasks': overdue_tasks,
        }

    def update_profile_stats(self):
        """
        Update user profile with calculated stats.
        This should be called when tasks are completed.
        """
        progress = self.calculate_all_progress()

        # Update post count (posts = completed tasks for activity feed)
        # This is a simplification - in production you'd have actual posts
        self.profile.post_count = progress['overall']['completed_tasks']

        # Save the profile
        self.profile.save(update_fields=['post_count'])

        return progress


def update_user_progress(user_id: int) -> Dict[str, Any]:
    """
    Convenience function to update progress for a user.
    Can be called from signals or other services.
    """
    try:
        user = User.objects.get(id=user_id)
        service = ProgressCalculationService(user)
        return service.update_profile_stats()
    except User.DoesNotExist:
        return {}
