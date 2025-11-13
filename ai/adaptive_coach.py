"""
Adaptive Coach Service

The "real AI" that intervenes when users fall behind.

Key responsibilities:
1. Detect when user needs Plan-B intervention (via PerformanceAnalyzer)
2. Generate personalized coaching messages
3. Propose alternative paths (simpler goals, extended timelines)
4. Auto-adjust task priorities and schedules
5. Send proactive check-ins via push notifications

This is what makes PathAI adaptive vs a static todo list.
"""

from django.utils import timezone
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json

from ai.performance_analyzer import performance_analyzer


class AdaptiveCoach:
    """
    Proactive AI coach that adapts plans when users struggle.

    Interventions:
    - Plan-B switching (simplify goals, extend timelines)
    - Task re-prioritization
    - Workload reduction
    - Motivational check-ins
    - Alternative path suggestions
    """

    def __init__(self):
        self.intervention_cooldown_days = 3  # Don't spam users
        self.min_tasks_for_intervention = 7  # Need enough data

    def check_and_intervene(self, user) -> Optional[Dict]:
        """
        Main entry point: Check if user needs intervention.

        Returns intervention dict if needed, None otherwise.

        Intervention types:
        - "planb_switch": Major course correction needed
        - "workload_reduction": Too many tasks, need to simplify
        - "task_reordering": Focus on different task types
        - "motivational_boost": Just need encouragement
        - "timeline_extension": Deadlines too aggressive
        """
        from users.models import UserProfile

        profile = user.profile

        # Check cooldown (don't intervene too frequently)
        if profile.last_intervention_at:
            days_since = (timezone.now() - profile.last_intervention_at).days
            if days_since < self.intervention_cooldown_days:
                return None

        # Check if intervention needed
        should_intervene, reason = performance_analyzer.should_trigger_planb_intervention(user)

        if not should_intervene:
            return None

        # Get performance analysis
        analysis = performance_analyzer.analyze_user_performance(user)

        if analysis.get("tasks_analyzed", 0) < self.min_tasks_for_intervention:
            return None  # Not enough data

        # Determine intervention type
        intervention = self._determine_intervention_type(user, analysis, reason)

        if intervention:
            # Log intervention
            profile.last_intervention_at = timezone.now()
            profile.last_intervention_type = intervention["type"]
            profile.save(update_fields=['last_intervention_at', 'last_intervention_type'])

        return intervention

    def _determine_intervention_type(self, user, analysis: Dict, reason: str) -> Dict:
        """
        Determine what type of intervention is needed.

        Returns:
            {
                "type": "planb_switch" | "workload_reduction" | ...,
                "severity": "low" | "medium" | "high" | "critical",
                "title": "Let's adjust your plan",
                "message": "I noticed you're falling behind on...",
                "actions": [
                    {
                        "action": "extend_deadline",
                        "task_id": 123,
                        "from_date": "2025-11-10",
                        "to_date": "2025-11-17",
                        "reason": "Give you more breathing room"
                    },
                    ...
                ],
                "alternative_paths": [
                    {
                        "title": "Focus on Quick Wins",
                        "description": "Pause long-term tasks, complete 5 quick wins",
                        "confidence": "high"
                    }
                ]
            }
        """
        risk_level = analysis["risk_level"]
        completion_rate = analysis["completion_rate"]
        blockers = analysis.get("blockers", [])
        task_type_performance = analysis.get("task_type_performance", {})

        # Critical risk: Major Plan-B switch needed
        if risk_level == "critical" or completion_rate < 0.3:
            return self._generate_planb_switch_intervention(user, analysis)

        # High risk: Workload reduction
        if risk_level == "high" or completion_rate < 0.5:
            return self._generate_workload_reduction_intervention(user, analysis)

        # Multiple blockers: Task reordering
        if len(blockers) >= 3:
            return self._generate_blocker_resolution_intervention(user, analysis)

        # Specific task type struggles
        for task_type, stats in task_type_performance.items():
            if stats["rate"] < 0.3 and stats["total"] >= 5:
                return self._generate_task_type_intervention(user, analysis, task_type)

        # Fallback: Motivational boost
        return self._generate_motivational_intervention(user, analysis)

    def _generate_planb_switch_intervention(self, user, analysis: Dict) -> Dict:
        """
        Critical intervention: Major course correction.

        Actions:
        - Extend all deadlines by 2 weeks
        - Mark non-critical tasks as "paused"
        - Focus on 3 quick wins
        - Suggest simpler alternative goals
        """
        from todos.models import Todo
        from users.models import GoalSpec

        actions = []

        # 1. Extend all urgent deadlines
        urgent_tasks = Todo.objects.filter(
            user=user,
            status__in=['ready', 'in_progress'],
            scheduled_date__lte=timezone.now().date() + timedelta(days=7)
        ).order_by('scheduled_date')[:10]

        for task in urgent_tasks:
            new_date = task.scheduled_date + timedelta(days=14)
            actions.append({
                "action": "extend_deadline",
                "task_id": task.id,
                "task_title": task.title,
                "from_date": str(task.scheduled_date),
                "to_date": str(new_date),
                "reason": "Give you 2 weeks breathing room",
            })

        # 2. Identify quick wins to boost momentum
        quick_wins = Todo.objects.filter(
            user=user,
            status='ready',
            is_quick_win=True
        )[:3]

        if quick_wins.exists():
            actions.append({
                "action": "focus_on_quick_wins",
                "task_ids": [t.id for t in quick_wins],
                "task_titles": [t.title for t in quick_wins],
                "reason": "Rebuild momentum with easy wins",
            })

        # 3. Suggest alternative paths
        active_goalspecs = GoalSpec.objects.filter(user=user, status='active')
        alternative_paths = []

        for goalspec in active_goalspecs:
            if goalspec.category == 'study':
                alternative_paths.append({
                    "title": f"Extend {goalspec.title} timeline by 6 months",
                    "description": f"Instead of rushing, take time to prepare properly (better IELTS, stronger SOP)",
                    "confidence": "high",
                    "goalspec_id": goalspec.id,
                })
            elif goalspec.category == 'career':
                alternative_paths.append({
                    "title": f"Pivot to lateral move instead of senior role",
                    "description": "Focus on similar-level positions at target companies first",
                    "confidence": "medium",
                    "goalspec_id": goalspec.id,
                })

        return {
            "type": "planb_switch",
            "severity": "critical",
            "title": "⚠️ Let's reset your plan",
            "message": (
                f"I've noticed your completion rate is at {int(analysis['completion_rate']*100)}%, "
                f"which suggests the current plan might be too ambitious. "
                f"Let's adjust to set you up for success."
            ),
            "actions": actions,
            "alternative_paths": alternative_paths,
            "recommended_next_step": "Accept the timeline extensions and focus on quick wins this week",
        }

    def _generate_workload_reduction_intervention(self, user, analysis: Dict) -> Dict:
        """
        High-risk intervention: Reduce workload.

        Actions:
        - Pause low-priority tasks
        - Extend medium-priority deadlines
        - Focus on top 3 tasks only
        """
        from todos.models import Todo

        actions = []

        # Find overdue tasks
        overdue_tasks = Todo.objects.filter(
            user=user,
            status__in=['ready', 'in_progress'],
            scheduled_date__lt=timezone.now().date()
        ).order_by('scheduled_date')

        # Group by priority
        high_priority = overdue_tasks.filter(priority=3)
        medium_priority = overdue_tasks.filter(priority=2)
        low_priority = overdue_tasks.filter(priority=1)

        # Pause low-priority tasks
        if low_priority.exists():
            actions.append({
                "action": "pause_tasks",
                "task_ids": [t.id for t in low_priority[:5]],
                "task_titles": [t.title for t in low_priority[:5]],
                "reason": "Clear your mental load - focus on what matters",
            })

        # Extend medium-priority
        if medium_priority.exists():
            for task in medium_priority[:3]:
                new_date = timezone.now().date() + timedelta(days=7)
                actions.append({
                    "action": "extend_deadline",
                    "task_id": task.id,
                    "task_title": task.title,
                    "from_date": str(task.scheduled_date),
                    "to_date": str(new_date),
                    "reason": "Move to next week",
                })

        # Focus on top 3 high-priority
        if high_priority.exists():
            actions.append({
                "action": "focus_mode",
                "task_ids": [t.id for t in high_priority[:3]],
                "task_titles": [t.title for t in high_priority[:3]],
                "reason": "Just these 3 this week - nothing else",
            })

        return {
            "type": "workload_reduction",
            "severity": "high",
            "title": "🎯 Let's simplify your week",
            "message": (
                f"You have {overdue_tasks.count()} overdue tasks. "
                f"Let's pause some and focus on just 3 critical ones."
            ),
            "actions": actions,
            "alternative_paths": [],
            "recommended_next_step": "Accept these changes and focus on the top 3 tasks only",
        }

    def _generate_blocker_resolution_intervention(self, user, analysis: Dict) -> Dict:
        """
        Intervention for chronic blockers.

        Actions:
        - Break down blocked tasks into smaller sub-tasks
        - Mark unrealistic tasks for re-scoping
        - Suggest skipping tasks that aren't critical
        """
        blockers = analysis.get("blockers", [])
        actions = []

        for blocker in blockers[:3]:
            task_id = blocker["task_id"]
            days_overdue = blocker.get("days_overdue", 0)

            if days_overdue > 21:  # Over 3 weeks
                actions.append({
                    "action": "suggest_skip",
                    "task_id": task_id,
                    "task_title": blocker["title"],
                    "reason": f"Blocked for {days_overdue} days - might not be achievable right now",
                })
            elif blocker.get("task_type") == "copilot":
                actions.append({
                    "action": "schedule_copilot_session",
                    "task_id": task_id,
                    "task_title": blocker["title"],
                    "reason": "Requires AI assistance - let's tackle it together",
                })
            else:
                actions.append({
                    "action": "break_down_task",
                    "task_id": task_id,
                    "task_title": blocker["title"],
                    "reason": "Split into 3 smaller sub-tasks",
                })

        return {
            "type": "blocker_resolution",
            "severity": "medium",
            "title": "🚧 Let's clear your blockers",
            "message": (
                f"You have {len(blockers)} tasks that keep getting postponed. "
                f"Let's tackle them differently."
            ),
            "actions": actions,
            "alternative_paths": [],
            "recommended_next_step": "Review blocked tasks and accept suggested changes",
        }

    def _generate_task_type_intervention(self, user, analysis: Dict, task_type: str) -> Dict:
        """
        Intervention for struggling with specific task type.

        E.g., user avoids "copilot" tasks → offer more AI assistance
        """
        from todos.models import Todo

        stats = analysis["task_type_performance"][task_type]
        actions = []

        # Find pending tasks of this type
        struggling_tasks = Todo.objects.filter(
            user=user,
            task_type=task_type,
            status__in=['ready', 'blocked']
        )[:3]

        if task_type == "copilot":
            for task in struggling_tasks:
                actions.append({
                    "action": "enable_ai_assistance",
                    "task_id": task.id,
                    "task_title": task.title,
                    "reason": "I'll proactively help with this",
                })
        elif task_type == "auto":
            for task in struggling_tasks:
                actions.append({
                    "action": "convert_to_manual",
                    "task_id": task.id,
                    "task_title": task.title,
                    "reason": "Let's make this more hands-on",
                })
        else:
            for task in struggling_tasks:
                actions.append({
                    "action": "break_down_task",
                    "task_id": task.id,
                    "task_title": task.title,
                    "reason": "Split into smaller chunks",
                })

        return {
            "type": "task_type_optimization",
            "severity": "medium",
            "title": f"💡 Let's improve your {task_type} tasks",
            "message": (
                f"I noticed you're completing only {int(stats['rate']*100)}% of {task_type} tasks. "
                f"Let's adjust the approach."
            ),
            "actions": actions,
            "alternative_paths": [],
            "recommended_next_step": f"Try the adjusted {task_type} tasks",
        }

    def _generate_motivational_intervention(self, user, analysis: Dict) -> Dict:
        """
        Low-severity: Just encouragement.
        """
        completion_rate = analysis["completion_rate"]
        strengths = analysis.get("strengths", [])

        return {
            "type": "motivational_boost",
            "severity": "low",
            "title": "💪 You're doing great!",
            "message": (
                f"Your completion rate is {int(completion_rate*100)}%. "
                f"Here's what's working well:\n" + "\n".join([f"• {s}" for s in strengths[:3]])
            ),
            "actions": [],
            "alternative_paths": [],
            "recommended_next_step": "Keep up the momentum!",
        }

    def apply_intervention_actions(self, user, intervention: Dict) -> Dict:
        """
        Apply the intervention actions to user's tasks.

        Returns:
            {
                "tasks_updated": 5,
                "deadlines_extended": 3,
                "tasks_paused": 2,
                "message": "Successfully applied changes"
            }
        """
        from todos.models import Todo

        actions = intervention.get("actions", [])
        tasks_updated = 0
        deadlines_extended = 0
        tasks_paused = 0

        for action_item in actions:
            action = action_item["action"]

            if action == "extend_deadline":
                task_id = action_item["task_id"]
                new_date = datetime.strptime(action_item["to_date"], "%Y-%m-%d").date()

                try:
                    task = Todo.objects.get(id=task_id, user=user)
                    task.scheduled_date = new_date
                    task.save(update_fields=['scheduled_date'])
                    deadlines_extended += 1
                    tasks_updated += 1
                except Todo.DoesNotExist:
                    pass

            elif action == "pause_tasks":
                task_ids = action_item["task_ids"]
                Todo.objects.filter(id__in=task_ids, user=user).update(status='blocked')
                tasks_paused += len(task_ids)
                tasks_updated += len(task_ids)

            elif action == "focus_on_quick_wins" or action == "focus_mode":
                task_ids = action_item["task_ids"]
                # Boost priority
                Todo.objects.filter(id__in=task_ids, user=user).update(priority=3)
                tasks_updated += len(task_ids)

        return {
            "tasks_updated": tasks_updated,
            "deadlines_extended": deadlines_extended,
            "tasks_paused": tasks_paused,
            "message": f"Successfully updated {tasks_updated} tasks",
        }


# Singleton instance
adaptive_coach = AdaptiveCoach()
