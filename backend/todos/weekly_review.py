"""
Weekly Review Generator
Analyzes past week's task completion and generates insights

Output format:
- Wins (completed tasks, progress made)
- Blockers (incomplete tasks, issues encountered)
- Streaks (consecutive completion days)
- Next week plan (upcoming tasks, adjusted priorities)
"""

from datetime import date, timedelta
from typing import Dict, List, Any
from django.db.models import Q, Count, Sum
from django.utils import timezone

from .models import Todo
from users.goalspec_models import GoalSpec


class WeeklyReview:
    """
    Generates weekly review summaries for users
    """

    def __init__(self, user):
        self.user = user
        self.today = timezone.now().date()

    def generate_review(self, week_start: date = None) -> Dict[str, Any]:
        """
        Generate weekly review for a specific week

        Args:
            week_start: Monday of the week to review (defaults to last Monday)

        Returns:
            Dictionary containing wins, blockers, stats, and next week plan
        """
        if week_start is None:
            # Default to last Monday
            days_since_monday = self.today.weekday()
            week_start = self.today - timedelta(days=days_since_monday)

        week_end = week_start + timedelta(days=6)

        # Fetch tasks for the week
        week_tasks = Todo.objects.filter(
            user=self.user,
            scheduled_date__gte=week_start,
            scheduled_date__lte=week_end
        )

        # Calculate statistics
        stats = self._calculate_stats(week_tasks)

        # Generate wins
        wins = self._generate_wins(week_tasks, stats)

        # Identify blockers
        blockers = self._identify_blockers(week_tasks)

        # Calculate streaks
        streaks = self._calculate_streaks(week_start, week_end)

        # Generate next week plan
        next_week_plan = self._generate_next_week_plan(week_end + timedelta(days=1))

        return {
            'week_start': week_start.isoformat(),
            'week_end': week_end.isoformat(),
            'stats': stats,
            'wins': wins,
            'blockers': blockers,
            'streaks': streaks,
            'next_week_plan': next_week_plan,
        }

    def _calculate_stats(self, week_tasks) -> Dict[str, Any]:
        """
        Calculate week statistics

        Args:
            week_tasks: QuerySet of tasks for the week

        Returns:
            Dictionary of statistics
        """
        total_tasks = week_tasks.count()
        completed_tasks = week_tasks.filter(status='done').count()
        skipped_tasks = week_tasks.filter(status='skipped').count()
        in_progress_tasks = week_tasks.filter(status='in_progress').count()
        blocked_tasks = week_tasks.filter(status='blocked').count()

        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

        # Calculate total time spent (sum of timeboxes for completed tasks)
        total_minutes = week_tasks.filter(status='done').aggregate(
            total=Sum('timebox_minutes')
        )['total'] or 0

        # Calculate average progress
        avg_progress = week_tasks.aggregate(
            avg=Sum('progress_percentage')
        )['avg'] or 0
        if total_tasks > 0:
            avg_progress = avg_progress / total_tasks

        # Task type breakdown
        task_type_breakdown = {
            'auto': week_tasks.filter(task_type='auto').count(),
            'copilot': week_tasks.filter(task_type='copilot').count(),
            'manual': week_tasks.filter(task_type='manual').count(),
        }

        return {
            'total_tasks': total_tasks,
            'completed': completed_tasks,
            'skipped': skipped_tasks,
            'in_progress': in_progress_tasks,
            'blocked': blocked_tasks,
            'completion_rate': round(completion_rate, 1),
            'total_hours': round(total_minutes / 60, 1),
            'avg_progress': round(avg_progress, 1),
            'task_type_breakdown': task_type_breakdown,
        }

    def _generate_wins(self, week_tasks, stats: Dict) -> List[Dict[str, Any]]:
        """
        Generate list of wins (accomplishments)

        Args:
            week_tasks: QuerySet of tasks for the week
            stats: Statistics dictionary

        Returns:
            List of win dictionaries
        """
        wins = []

        # Completed tasks
        completed_tasks = week_tasks.filter(status='done').order_by('-priority', '-timebox_minutes')

        for task in completed_tasks[:10]:  # Top 10 wins
            wins.append({
                'type': 'task_completed',
                'title': task.title,
                'date': task.completed_at.date().isoformat() if task.completed_at else None,
                'progress': task.progress_percentage,
                'priority': task.priority,
                'deliverable': task.deliverable_type,
            })

        # High completion rate
        if stats['completion_rate'] >= 80:
            wins.append({
                'type': 'high_completion_rate',
                'title': f'{stats["completion_rate"]}% completion rate!',
                'message': 'Outstanding consistency this week',
            })

        # Time invested
        if stats['total_hours'] >= 10:
            wins.append({
                'type': 'time_invested',
                'title': f'{stats["total_hours"]} hours invested',
                'message': 'Great dedication to your goals',
            })

        return wins

    def _identify_blockers(self, week_tasks) -> List[Dict[str, Any]]:
        """
        Identify blockers (incomplete/problematic tasks)

        Args:
            week_tasks: QuerySet of tasks for the week

        Returns:
            List of blocker dictionaries
        """
        blockers = []

        # Blocked tasks
        blocked_tasks = week_tasks.filter(status='blocked')
        for task in blocked_tasks:
            blockers.append({
                'type': 'blocked_task',
                'task_id': task.id,
                'title': task.title,
                'reason': 'Waiting on dependencies',
                'blocked_by': task.blocked_by,
            })

        # Overdue tasks (scheduled but not done)
        overdue_tasks = week_tasks.filter(
            Q(status='ready') | Q(status='in_progress'),
            scheduled_date__lt=self.today
        )
        for task in overdue_tasks[:5]:  # Top 5 overdue
            blockers.append({
                'type': 'overdue_task',
                'task_id': task.id,
                'title': task.title,
                'days_overdue': task.days_overdue,
                'scheduled_date': task.scheduled_date.isoformat(),
            })

        # Low progress tasks (in progress but < 30% progress)
        low_progress_tasks = week_tasks.filter(
            status='in_progress',
            progress_percentage__lt=30
        )
        for task in low_progress_tasks:
            blockers.append({
                'type': 'low_progress',
                'task_id': task.id,
                'title': task.title,
                'progress': task.progress_percentage,
                'message': 'May need more attention or breakdown',
            })

        return blockers

    def _calculate_streaks(self, week_start: date, week_end: date) -> Dict[str, Any]:
        """
        Calculate completion streaks

        Args:
            week_start: Start of week
            week_end: End of week

        Returns:
            Streak statistics
        """
        # Get completion by day
        daily_completion = []
        current_date = week_start

        while current_date <= week_end:
            day_tasks = Todo.objects.filter(
                user=self.user,
                scheduled_date=current_date
            )
            completed = day_tasks.filter(status='done').count()
            total = day_tasks.count()

            has_completion = completed > 0 if total > 0 else False
            daily_completion.append({
                'date': current_date.isoformat(),
                'completed': completed,
                'total': total,
                'has_activity': has_completion,
            })

            current_date += timedelta(days=1)

        # Calculate current streak
        current_streak = 0
        for day in reversed(daily_completion):
            if day['has_activity']:
                current_streak += 1
            else:
                break

        # Find longest streak in week
        longest_streak = 0
        temp_streak = 0
        for day in daily_completion:
            if day['has_activity']:
                temp_streak += 1
                longest_streak = max(longest_streak, temp_streak)
            else:
                temp_streak = 0

        return {
            'current_streak': current_streak,
            'longest_week_streak': longest_streak,
            'daily_completion': daily_completion,
        }

    def _generate_next_week_plan(self, next_week_start: date) -> Dict[str, Any]:
        """
        Generate plan for next week

        Args:
            next_week_start: Monday of next week

        Returns:
            Next week plan dictionary
        """
        next_week_end = next_week_start + timedelta(days=6)

        # Get scheduled tasks for next week
        scheduled_tasks = Todo.objects.filter(
            user=self.user,
            scheduled_date__gte=next_week_start,
            scheduled_date__lte=next_week_end
        ).order_by('scheduled_date', '-priority')

        # Get active goals
        active_goals = GoalSpec.objects.filter(
            user=self.user,
            is_active=True,
            completed=False
        )

        # Calculate expected time commitment
        total_minutes = scheduled_tasks.aggregate(total=Sum('timebox_minutes'))['total'] or 0

        # Group tasks by day
        tasks_by_day = {}
        for task in scheduled_tasks:
            day_key = task.scheduled_date.isoformat()
            if day_key not in tasks_by_day:
                tasks_by_day[day_key] = []

            tasks_by_day[day_key].append({
                'id': task.id,
                'title': task.title,
                'task_type': task.task_type,
                'timebox_minutes': task.timebox_minutes,
                'priority': task.priority,
                'deliverable_type': task.deliverable_type,
            })

        # Identify focus areas (goals with most tasks)
        goal_counts = {}
        for goal in active_goals:
            goal_task_count = scheduled_tasks.filter(
                Q(title__icontains=goal.title) | Q(description__icontains=goal.title)
            ).count()
            if goal_task_count > 0:
                goal_counts[goal.title] = goal_task_count

        focus_areas = sorted(goal_counts.items(), key=lambda x: x[1], reverse=True)[:3]

        return {
            'week_start': next_week_start.isoformat(),
            'week_end': next_week_end.isoformat(),
            'total_tasks': scheduled_tasks.count(),
            'total_hours': round(total_minutes / 60, 1),
            'tasks_by_day': tasks_by_day,
            'focus_areas': [{'goal': goal, 'task_count': count} for goal, count in focus_areas],
            'active_goals': [
                {
                    'title': goal.title,
                    'goal_type': goal.goal_type,
                    'priority_weight': goal.priority_weight,
                }
                for goal in active_goals
            ],
        }

    def generate_formatted_review(self, week_start: date = None) -> str:
        """
        Generate human-readable weekly review text

        Args:
            week_start: Monday of the week to review

        Returns:
            Formatted review string
        """
        review = self.generate_review(week_start)

        output = []
        output.append(f"# Weekly Review: {review['week_start']} to {review['week_end']}")
        output.append("")

        # Stats
        stats = review['stats']
        output.append("## Statistics")
        output.append(f"- Total tasks: {stats['total_tasks']}")
        output.append(f"- Completed: {stats['completed']} ({stats['completion_rate']}%)")
        output.append(f"- In progress: {stats['in_progress']}")
        output.append(f"- Blocked: {stats['blocked']}")
        output.append(f"- Total time: {stats['total_hours']} hours")
        output.append("")

        # Wins
        output.append("## Wins")
        for win in review['wins'][:5]:
            if win['type'] == 'task_completed':
                output.append(f"- Completed: {win['title']}")
            else:
                output.append(f"- {win['title']}: {win.get('message', '')}")
        output.append("")

        # Blockers
        if review['blockers']:
            output.append("## Blockers")
            for blocker in review['blockers'][:5]:
                output.append(f"- {blocker['title']} ({blocker['type']})")
            output.append("")

        # Streaks
        streaks = review['streaks']
        output.append("## Streaks")
        output.append(f"- Current streak: {streaks['current_streak']} days")
        output.append(f"- Longest this week: {streaks['longest_week_streak']} days")
        output.append("")

        # Next week
        next_week = review['next_week_plan']
        output.append("## Next Week Plan")
        output.append(f"- Total tasks: {next_week['total_tasks']}")
        output.append(f"- Expected time: {next_week['total_hours']} hours")
        if next_week['focus_areas']:
            output.append("- Focus areas:")
            for area in next_week['focus_areas']:
                output.append(f"  - {area['goal']} ({area['task_count']} tasks)")

        return "\n".join(output)
