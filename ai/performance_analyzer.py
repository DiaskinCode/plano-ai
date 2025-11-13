"""
Performance Analyzer Service

Analyzes user behavior patterns over time to detect:
- Completion rates by time of day
- Task types user avoids
- Blocker patterns (repeatedly skipped tasks)
- Optimal schedule based on energy patterns
- Risk assessment (low completion = need Plan-B)

Used by AdaptiveCoach to trigger Plan-B interventions.
"""

from django.utils import timezone
from django.db.models import Q, Count, Avg
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from collections import defaultdict
import statistics


class PerformanceAnalyzer:
    """
    Analyzes user task completion patterns and behavioral trends.

    Key outputs:
    - Performance insights JSON (stored in UserProfile.performance_insights)
    - Risk level assessment (triggers AdaptiveCoach)
    - Optimal schedule recommendations
    """

    def __init__(self):
        self.analysis_window_days = 30  # Last 30 days
        self.min_tasks_for_pattern = 5  # Need at least 5 tasks to detect patterns

    def analyze_user_performance(self, user) -> Dict:
        """
        Main entry point: Analyze all aspects of user's performance.

        Returns:
            {
                "completion_rate": 0.65,
                "risk_level": "medium",
                "optimal_schedule": {
                    "high_energy_hours": [9, 10, 11],
                    "low_energy_hours": [14, 15, 20, 21],
                    "best_day": "Monday",
                    "worst_day": "Friday"
                },
                "task_type_performance": {
                    "auto": {"completed": 5, "total": 8, "rate": 0.625},
                    "copilot": {"completed": 3, "total": 10, "rate": 0.3},
                    "manual": {"completed": 12, "total": 15, "rate": 0.8}
                },
                "blockers": [
                    {
                        "task_id": 123,
                        "title": "Write SOP",
                        "skipped_count": 4,
                        "pattern": "Skipped every Monday morning"
                    }
                ],
                "strengths": [
                    "Completes 90% of quick wins",
                    "Morning productivity (9-11am) is excellent"
                ],
                "warnings": [
                    "Avoids copilot tasks (30% completion)",
                    "Friday completion rate drops to 40%"
                ],
                "recommended_actions": [
                    "Schedule copilot tasks with AI support reminders",
                    "Move critical tasks away from Fridays"
                ],
                "last_analysis": "2025-11-06T10:30:00Z"
            }
        """
        from todos.models import Todo

        cutoff_date = timezone.now() - timedelta(days=self.analysis_window_days)

        # Get all tasks in analysis window
        tasks = Todo.objects.filter(
            user=user,
            created_at__gte=cutoff_date
        ).order_by('-created_at')

        if tasks.count() < self.min_tasks_for_pattern:
            return self._insufficient_data_response()

        # Analyze different dimensions
        completion_rate = self._calculate_completion_rate(tasks)
        risk_level = self._assess_risk_level(completion_rate, tasks)
        optimal_schedule = self._detect_optimal_schedule(tasks)
        task_type_performance = self._analyze_task_type_performance(tasks)
        blockers = self._detect_blocker_patterns(tasks)
        energy_patterns = self._detect_energy_patterns(tasks)

        # Generate insights
        strengths = self._identify_strengths(
            completion_rate,
            task_type_performance,
            optimal_schedule,
            energy_patterns
        )
        warnings = self._identify_warnings(
            completion_rate,
            task_type_performance,
            optimal_schedule,
            blockers
        )
        recommended_actions = self._generate_recommendations(
            risk_level,
            task_type_performance,
            blockers,
            optimal_schedule
        )

        return {
            "completion_rate": completion_rate,
            "risk_level": risk_level,
            "optimal_schedule": optimal_schedule,
            "task_type_performance": task_type_performance,
            "energy_patterns": energy_patterns,
            "blockers": blockers,
            "strengths": strengths,
            "warnings": warnings,
            "recommended_actions": recommended_actions,
            "last_analysis": timezone.now().isoformat(),
            "tasks_analyzed": tasks.count(),
        }

    def _calculate_completion_rate(self, tasks) -> float:
        """Calculate overall completion rate."""
        total = tasks.count()
        if total == 0:
            return 0.0

        completed = tasks.filter(status='done').count()
        return round(completed / total, 3)

    def _assess_risk_level(self, completion_rate: float, tasks) -> str:
        """
        Assess risk level based on completion rate and recent trends.

        Returns: "low" | "medium" | "high" | "critical"
        """
        # Check recent 7-day trend
        week_ago = timezone.now() - timedelta(days=7)
        recent_tasks = tasks.filter(created_at__gte=week_ago)
        recent_completion = self._calculate_completion_rate(recent_tasks)

        # Critical: < 30% completion or sharp decline
        if completion_rate < 0.3 or (recent_completion < 0.2 and recent_tasks.count() >= 5):
            return "critical"

        # High: 30-50% completion
        if completion_rate < 0.5:
            return "high"

        # Medium: 50-70% completion
        if completion_rate < 0.7:
            return "medium"

        # Low: > 70% completion
        return "low"

    def _detect_optimal_schedule(self, tasks) -> Dict:
        """
        Detect when user is most productive.

        Returns:
            {
                "high_energy_hours": [9, 10, 11],
                "low_energy_hours": [14, 15, 20, 21],
                "best_day": "Monday",
                "worst_day": "Friday",
                "completion_by_hour": {9: 0.85, 10: 0.90, ...},
                "completion_by_day": {"Monday": 0.75, ...}
            }
        """
        completed_tasks = tasks.filter(status='done', completed_at__isnull=False)

        # Analyze by hour of day
        hourly_completion = defaultdict(lambda: {"completed": 0, "total": 0})
        for task in tasks:
            if task.scheduled_time:
                hour = task.scheduled_time.hour
                hourly_completion[hour]["total"] += 1
                if task.status == 'done':
                    hourly_completion[hour]["completed"] += 1

        completion_by_hour = {}
        for hour, data in hourly_completion.items():
            if data["total"] >= 3:  # Need at least 3 tasks for pattern
                completion_by_hour[hour] = round(data["completed"] / data["total"], 2)

        # Identify high/low energy hours
        if completion_by_hour:
            sorted_hours = sorted(completion_by_hour.items(), key=lambda x: x[1], reverse=True)
            high_energy_hours = [h for h, rate in sorted_hours[:3] if rate > 0.7]
            low_energy_hours = [h for h, rate in sorted_hours[-3:] if rate < 0.5]
        else:
            high_energy_hours = []
            low_energy_hours = []

        # Analyze by day of week
        daily_completion = defaultdict(lambda: {"completed": 0, "total": 0})
        for task in tasks:
            day_name = task.scheduled_date.strftime('%A')
            daily_completion[day_name]["total"] += 1
            if task.status == 'done':
                daily_completion[day_name]["completed"] += 1

        completion_by_day = {}
        for day, data in daily_completion.items():
            if data["total"] >= 2:
                completion_by_day[day] = round(data["completed"] / data["total"], 2)

        best_day = max(completion_by_day.items(), key=lambda x: x[1])[0] if completion_by_day else None
        worst_day = min(completion_by_day.items(), key=lambda x: x[1])[0] if completion_by_day else None

        return {
            "high_energy_hours": high_energy_hours,
            "low_energy_hours": low_energy_hours,
            "best_day": best_day,
            "worst_day": worst_day,
            "completion_by_hour": completion_by_hour,
            "completion_by_day": completion_by_day,
        }

    def _analyze_task_type_performance(self, tasks) -> Dict:
        """
        Analyze completion rates by task type (auto/copilot/manual).

        Returns:
            {
                "auto": {"completed": 5, "total": 8, "rate": 0.625},
                "copilot": {"completed": 3, "total": 10, "rate": 0.3},
                "manual": {"completed": 12, "total": 15, "rate": 0.8}
            }
        """
        task_type_stats = {}

        for task_type in ['auto', 'copilot', 'manual']:
            type_tasks = tasks.filter(task_type=task_type)
            total = type_tasks.count()

            if total > 0:
                completed = type_tasks.filter(status='done').count()
                task_type_stats[task_type] = {
                    "completed": completed,
                    "total": total,
                    "rate": round(completed / total, 3),
                }

        return task_type_stats

    def _detect_blocker_patterns(self, tasks) -> List[Dict]:
        """
        Detect tasks that are repeatedly skipped or postponed.

        Returns:
            [
                {
                    "task_id": 123,
                    "title": "Write SOP",
                    "skipped_count": 4,
                    "days_overdue": 12,
                    "pattern": "Skipped every Monday morning"
                }
            ]
        """
        blockers = []

        # Find tasks that were skipped multiple times
        skipped_tasks = tasks.filter(status='skipped')

        # Find tasks that are long overdue but not completed
        overdue_tasks = tasks.filter(
            status__in=['ready', 'in_progress', 'blocked'],
            scheduled_date__lt=timezone.now().date() - timedelta(days=7)
        )

        for task in overdue_tasks[:5]:  # Top 5 blockers
            blockers.append({
                "task_id": task.id,
                "title": task.title,
                "task_type": task.task_type,
                "days_overdue": task.days_overdue,
                "status": task.status,
                "pattern": self._detect_skip_pattern(task),
            })

        return blockers

    def _detect_skip_pattern(self, task) -> str:
        """
        Detect why a task keeps getting skipped.

        Returns human-readable pattern description.
        """
        patterns = []

        # Check if it's a specific task type
        if task.task_type == 'copilot':
            patterns.append("Requires co-pilot assistance")
        elif task.task_type == 'auto':
            patterns.append("AI-generated task not started")

        # Check if it's high cognitive load
        if task.cognitive_load and task.cognitive_load >= 4:
            patterns.append("High cognitive load task")

        # Check if it's blocked by dependencies
        if task.is_blocked():
            patterns.append("Blocked by dependencies")

        # Check if it requires specific energy level
        if task.energy_level == 'high':
            patterns.append("Requires high energy (morning task)")

        if not patterns:
            return "Repeatedly postponed"

        return " • ".join(patterns)

    def _detect_energy_patterns(self, tasks) -> Dict:
        """
        Analyze completion rates by energy level requirements.

        Returns:
            {
                "high": {"completed": 8, "total": 12, "rate": 0.67},
                "medium": {"completed": 15, "total": 18, "rate": 0.83},
                "low": {"completed": 10, "total": 10, "rate": 1.0}
            }
        """
        energy_stats = {}

        for energy_level in ['high', 'medium', 'low']:
            energy_tasks = tasks.filter(energy_level=energy_level)
            total = energy_tasks.count()

            if total > 0:
                completed = energy_tasks.filter(status='done').count()
                energy_stats[energy_level] = {
                    "completed": completed,
                    "total": total,
                    "rate": round(completed / total, 3),
                }

        return energy_stats

    def _identify_strengths(
        self,
        completion_rate: float,
        task_type_performance: Dict,
        optimal_schedule: Dict,
        energy_patterns: Dict
    ) -> List[str]:
        """Generate positive insights about user's performance."""
        strengths = []

        if completion_rate >= 0.8:
            strengths.append(f"Excellent overall completion rate ({int(completion_rate * 100)}%)")
        elif completion_rate >= 0.7:
            strengths.append(f"Strong task completion rate ({int(completion_rate * 100)}%)")

        # Check task type strengths
        for task_type, stats in task_type_performance.items():
            if stats["rate"] >= 0.8 and stats["total"] >= 5:
                strengths.append(f"High success rate with {task_type} tasks ({int(stats['rate'] * 100)}%)")

        # Check energy level strengths
        for energy, stats in energy_patterns.items():
            if stats["rate"] >= 0.85 and stats["total"] >= 5:
                strengths.append(f"Excellent at {energy} energy tasks ({int(stats['rate'] * 100)}%)")

        # Check time-of-day strengths
        if optimal_schedule.get("high_energy_hours"):
            hours_str = ", ".join([f"{h}:00" for h in optimal_schedule["high_energy_hours"][:3]])
            strengths.append(f"Peak productivity during {hours_str}")

        return strengths

    def _identify_warnings(
        self,
        completion_rate: float,
        task_type_performance: Dict,
        optimal_schedule: Dict,
        blockers: List[Dict]
    ) -> List[str]:
        """Generate warnings about concerning patterns."""
        warnings = []

        if completion_rate < 0.4:
            warnings.append(f"Low completion rate ({int(completion_rate * 100)}%) - need Plan-B intervention")
        elif completion_rate < 0.6:
            warnings.append(f"Below-average completion rate ({int(completion_rate * 100)}%)")

        # Check task type weaknesses
        for task_type, stats in task_type_performance.items():
            if stats["rate"] < 0.4 and stats["total"] >= 5:
                warnings.append(f"Struggling with {task_type} tasks ({int(stats['rate'] * 100)}% completion)")

        # Check for chronic blockers
        if len(blockers) >= 3:
            warnings.append(f"{len(blockers)} tasks are chronically blocked or overdue")

        # Check worst day pattern
        if optimal_schedule.get("worst_day"):
            worst_day = optimal_schedule["worst_day"]
            worst_rate = optimal_schedule["completion_by_day"].get(worst_day, 0)
            if worst_rate < 0.4:
                warnings.append(f"{worst_day}s are consistently low-productivity ({int(worst_rate * 100)}%)")

        return warnings

    def _generate_recommendations(
        self,
        risk_level: str,
        task_type_performance: Dict,
        blockers: List[Dict],
        optimal_schedule: Dict
    ) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []

        # Risk-based recommendations
        if risk_level in ['high', 'critical']:
            recommendations.append("⚠️ URGENT: Schedule 1-on-1 coaching session to reset plan")
            recommendations.append("Switch to Plan-B: Focus on 2-3 quick wins this week")

        # Task type recommendations
        for task_type, stats in task_type_performance.items():
            if stats["rate"] < 0.4 and stats["total"] >= 5:
                if task_type == 'copilot':
                    recommendations.append("Enable proactive AI assistance for co-pilot tasks")
                elif task_type == 'auto':
                    recommendations.append("Review AI-generated tasks with user before scheduling")
                else:
                    recommendations.append(f"Break down {task_type} tasks into smaller sub-tasks")

        # Blocker recommendations
        if blockers:
            for blocker in blockers[:2]:  # Top 2 blockers
                if blocker.get("days_overdue", 0) > 14:
                    recommendations.append(f"Re-scope or skip: '{blocker['title']}' (blocked {blocker['days_overdue']} days)")

        # Schedule optimization
        if optimal_schedule.get("high_energy_hours") and optimal_schedule.get("low_energy_hours"):
            high_hours = optimal_schedule["high_energy_hours"][:2]
            recommendations.append(f"Schedule high-priority tasks during peak hours: {', '.join([f'{h}:00' for h in high_hours])}")

        return recommendations

    def _insufficient_data_response(self) -> Dict:
        """Return when there's not enough data to analyze."""
        return {
            "completion_rate": 0.0,
            "risk_level": "unknown",
            "optimal_schedule": {},
            "task_type_performance": {},
            "energy_patterns": {},
            "blockers": [],
            "strengths": [],
            "warnings": ["Not enough task history for analysis (need at least 5 tasks)"],
            "recommended_actions": ["Continue using PathAI for 1-2 weeks to build performance history"],
            "last_analysis": timezone.now().isoformat(),
            "tasks_analyzed": 0,
        }

    def should_trigger_planb_intervention(self, user) -> Tuple[bool, str]:
        """
        Determine if user needs immediate Plan-B intervention.

        Returns:
            (should_intervene: bool, reason: str)
        """
        analysis = self.analyze_user_performance(user)

        # Trigger if risk is high or critical
        if analysis["risk_level"] in ["high", "critical"]:
            return (True, f"Risk level: {analysis['risk_level']} (completion rate: {int(analysis['completion_rate'] * 100)}%)")

        # Trigger if 3+ chronic blockers
        if len(analysis["blockers"]) >= 3:
            return (True, f"{len(analysis['blockers'])} tasks are chronically blocked")

        # Trigger if specific task type has < 30% success
        for task_type, stats in analysis["task_type_performance"].items():
            if stats["rate"] < 0.3 and stats["total"] >= 5:
                return (True, f"Struggling with {task_type} tasks ({int(stats['rate'] * 100)}% success)")

        return (False, "Performance within acceptable range")


# Singleton instance
performance_analyzer = PerformanceAnalyzer()
