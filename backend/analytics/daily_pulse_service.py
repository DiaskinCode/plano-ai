"""
Daily Pulse / Morning Brief Generator

Generates personalized daily briefs with 6 blocks:
1. 🕐 Greeting
2. 🎯 Priorities
3. 📊 Workload
4. ⚠️ Warnings/Reminders
5. 💡 Smart Suggestions
6. 📈 Weekly Progress
"""
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from django.utils import timezone
from django.db.models import Count, Sum, Q, Avg
from collections import defaultdict

from .models import DailyBrief, UserBehaviorPattern
from todos.models import Todo
from users.models import User, GoalSpec
from users.models import UserProfile


class DailyPulseGenerator:
    """
    Generates daily morning briefs for users

    Usage:
        generator = DailyPulseGenerator(user)
        brief = generator.generate_daily_brief()
    """

    def __init__(self, user: User):
        self.user = user
        self.today = timezone.now().date()
        self.now = timezone.now()

        # Get user profile
        try:
            self.profile = UserProfile.objects.get(user=user)
            self.available_minutes = getattr(self.profile, 'daily_available_minutes', 480)
        except UserProfile.DoesNotExist:
            self.available_minutes = 480  # Default 8 hours

    def generate_daily_brief(self, trigger: str = 'scheduled') -> Optional[DailyBrief]:
        """
        Generate complete daily brief

        Args:
            trigger: 'scheduled'/'on_login'/'manual'

        Returns:
            DailyBrief instance or None if generation fails
        """
        # Check if brief already exists
        existing = DailyBrief.objects.filter(
            user=self.user,
            date=self.today
        ).first()

        if existing and trigger == 'on_login':
            # Check if should regenerate
            if not existing.should_regenerate():
                return existing
            # Regenerate
            existing.delete()

        # Generate all blocks
        greeting = self._generate_greeting()
        priorities = self._select_top_priorities()
        workload = self._calculate_workload()
        warnings = self._generate_warnings()
        suggestions = self._generate_smart_suggestions()
        weekly_progress = self._calculate_weekly_progress()

        # Format full message
        full_message = self._format_full_message(
            greeting, priorities, workload, warnings, suggestions, weekly_progress
        )

        # Create brief
        brief = DailyBrief.objects.create(
            user=self.user,
            date=self.today,
            greeting_message=greeting,
            top_priorities=priorities,
            workload_percentage=workload['percentage'],
            workload_status=workload['status'],
            total_timebox_minutes=workload['total_minutes'],
            available_minutes=self.available_minutes,
            warnings=warnings,
            smart_suggestions=suggestions,
            weekly_progress=weekly_progress,
            full_message=full_message,
            generation_trigger=trigger
        )

        return brief

    # ==========================================
    # Block 1: 🕐 Greeting
    # ==========================================

    def _generate_greeting(self) -> str:
        """Generate personalized greeting based on time of day"""
        hour = self.now.hour
        name = self.user.first_name or self.user.email.split('@')[0]

        # Determine greeting based on hour
        if 5 <= hour < 12:
            greeting = f"Доброе утро, {name}! 👋"
        elif 12 <= hour < 18:
            greeting = f"Добрый день, {name}! 👋"
        elif 18 <= hour < 22:
            greeting = f"Добрый вечер, {name}! 👋"
        else:
            greeting = f"Привет, {name}! 🌙"

        # Add streak if exists
        if hasattr(self.user, 'current_streak') and self.user.current_streak > 0:
            streak = self.user.current_streak
            if streak >= 7:
                greeting += f" 🔥 {streak} дней подряд!"
            elif streak >= 3:
                greeting += f" 💪 {streak} дня подряд!"

        return greeting

    # ==========================================
    # Block 2: 🎯 Priorities
    # ==========================================

    def _select_top_priorities(self) -> List[Dict]:
        """Select top 2-3 priority tasks for today"""
        # Get today's tasks
        tasks = Todo.objects.filter(
            user=self.user,
            scheduled_date=self.today,
            status__in=['ready', 'pending', 'in_progress']
        ).select_related('goalspec')

        if not tasks:
            return []

        # Score each task
        scored_tasks = []
        for task in tasks:
            score = self._calculate_priority_score(task)
            scored_tasks.append((task, score))

        # Sort by score
        scored_tasks.sort(key=lambda x: x[1], reverse=True)

        # Select top 2-3
        top_tasks = []
        for task, score in scored_tasks[:3]:
            priority_info = {
                'task_id': task.id,
                'title': task.title,
                'reason': self._get_priority_reason(task),
                'timebox_minutes': task.timebox_minutes,
                'priority_level': task.priority,
            }

            # Add deadline if close
            if task.goalspec and hasattr(task.goalspec, 'target_date') and task.goalspec.target_date:
                days_until = (task.goalspec.target_date - self.today).days
                if days_until <= 3:
                    priority_info['deadline'] = task.goalspec.target_date.isoformat()
                    priority_info['days_until_deadline'] = days_until

            top_tasks.append(priority_info)

        return top_tasks

    def _calculate_priority_score(self, task: Todo) -> float:
        """Calculate priority score for a task"""
        score = 0.0

        # Priority level (most important)
        score += task.priority * 30

        # Deadline proximity
        if task.goalspec and hasattr(task.goalspec, 'target_date') and task.goalspec.target_date:
            days_until = (task.goalspec.target_date - self.today).days
            if days_until <= 1:
                score += 40
            elif days_until <= 3:
                score += 20
            elif days_until <= 7:
                score += 10

        # Contribution weight
        score += task.contribution_weight * 15

        # Overdue tasks
        if task.is_overdue:
            score += 50

        # High energy tasks in morning
        if self.now.hour < 12 and task.energy_level == 'high':
            score += 10

        return score

    def _get_priority_reason(self, task: Todo) -> str:
        """Get human-readable reason why task is priority"""
        reasons = []

        if task.priority == 3:
            reasons.append("высокий приоритет")

        if task.is_overdue:
            reasons.append("просрочено")

        if task.goalspec and hasattr(task.goalspec, 'target_date') and task.goalspec.target_date:
            days_until = (task.goalspec.target_date - self.today).days
            if days_until == 0:
                reasons.append("deadline сегодня")
            elif days_until == 1:
                reasons.append("deadline завтра")
            elif days_until <= 3:
                reasons.append(f"deadline через {days_until} дня")

        if task.contribution_weight > 0.7:
            reasons.append("важно для цели")

        return " + ".join(reasons) if reasons else "запланировано на сегодня"

    # ==========================================
    # Block 3: 📊 Workload
    # ==========================================

    def _calculate_workload(self) -> Dict:
        """Calculate daily workload metrics"""
        # Get today's tasks
        tasks = Todo.objects.filter(
            user=self.user,
            scheduled_date=self.today,
            status__in=['ready', 'pending', 'in_progress']
        )

        # Sum timebox minutes
        total_minutes = tasks.aggregate(
            total=Sum('timebox_minutes')
        )['total'] or 0

        # Calculate percentage
        percentage = int((total_minutes / self.available_minutes) * 100) if self.available_minutes > 0 else 0

        # Determine status
        if percentage <= 40:
            status = 'light'
        elif percentage <= 70:
            status = 'optimal'
        elif percentage <= 90:
            status = 'heavy'
        else:
            status = 'overloaded'

        return {
            'percentage': percentage,
            'status': status,
            'total_minutes': total_minutes,
            'available_minutes': self.available_minutes,
            'task_count': tasks.count()
        }

    # ==========================================
    # Block 4: ⚠️ Warnings/Reminders
    # ==========================================

    def _generate_warnings(self) -> List[Dict]:
        """Generate warnings and reminders"""
        warnings = []

        # Check low progress by category
        low_progress_warnings = self._check_low_category_progress()
        warnings.extend(low_progress_warnings)

        # Check upcoming deadlines
        deadline_warnings = self._check_upcoming_deadlines()
        warnings.extend(deadline_warnings)

        # Check blocked tasks that became ready
        unblocked_warnings = self._check_unblocked_tasks()
        warnings.extend(unblocked_warnings)

        # Check important events today
        event_warnings = self._check_today_events()
        warnings.extend(event_warnings)

        # Sort by severity
        warnings.sort(key=lambda x: {'high': 3, 'medium': 2, 'low': 1}.get(x.get('severity', 'low'), 0), reverse=True)

        return warnings[:5]  # Max 5 warnings

    def _check_low_category_progress(self) -> List[Dict]:
        """Check categories with 0% progress this week"""
        warnings = []

        week_start = self.today - timedelta(days=self.today.weekday())

        # Get all goals
        goals = GoalSpec.objects.filter(
            user=self.user,
            is_active=True
        )

        for goal in goals:
            # Count tasks for this category this week
            tasks = Todo.objects.filter(
                user=self.user,
                goalspec=goal,
                scheduled_date__gte=week_start,
                scheduled_date__lte=self.today
            )

            total = tasks.count()
            completed = tasks.filter(status='done').count()

            if total > 0 and completed == 0:
                category_name = self._translate_category(goal.category)
                warnings.append({
                    'type': 'low_progress',
                    'category': goal.category,
                    'message': f"{category_name} 0% прогресса за неделю",
                    'severity': 'medium'
                })

        return warnings

    def _check_upcoming_deadlines(self) -> List[Dict]:
        """Check tasks with close deadlines"""
        warnings = []

        # Get tasks with external URLs (interviews, meetings)
        tasks_with_events = Todo.objects.filter(
            user=self.user,
            scheduled_date__gte=self.today,
            scheduled_date__lte=self.today + timedelta(days=2),
            external_url__isnull=False
        ).exclude(external_url='')

        for task in tasks_with_events:
            days_until = (task.scheduled_date - self.today).days

            if days_until == 0:
                message = f"{task.title} сегодня"
                if task.scheduled_time:
                    message += f" в {task.scheduled_time.strftime('%H:%M')}"
            elif days_until == 1:
                message = f"{task.title} завтра"
                if task.scheduled_time:
                    message += f" в {task.scheduled_time.strftime('%H:%M')}"
            else:
                message = f"{task.title} через {days_until} дня"

            warnings.append({
                'type': 'deadline',
                'task_id': task.id,
                'message': message,
                'severity': 'high' if days_until == 0 else 'medium'
            })

        return warnings

    def _check_unblocked_tasks(self) -> List[Dict]:
        """Check tasks that were blocked but now ready"""
        warnings = []

        # Get recently unblocked tasks
        ready_tasks = Todo.objects.filter(
            user=self.user,
            status='ready',
            blocked_by__isnull=False
        ).exclude(blocked_by=[])

        for task in ready_tasks[:2]:  # Max 2
            if not task.is_blocked():
                warnings.append({
                    'type': 'unblocked',
                    'task_id': task.id,
                    'message': f"Задача '{task.title}' теперь разблокирована!",
                    'severity': 'low'
                })

        return warnings

    def _check_today_events(self) -> List[Dict]:
        """Check important events scheduled for today"""
        warnings = []

        # Get high priority tasks today
        important_today = Todo.objects.filter(
            user=self.user,
            scheduled_date=self.today,
            priority=3,
            status__in=['ready', 'pending']
        )

        if important_today.count() > 3:
            warnings.append({
                'type': 'high_workload',
                'message': f"У тебя {important_today.count()} важных задач сегодня",
                'severity': 'medium'
            })

        return warnings

    # ==========================================
    # Block 5: 💡 Smart Suggestions
    # ==========================================

    def _generate_smart_suggestions(self) -> List[Dict]:
        """Generate smart suggestions"""
        suggestions = []

        # Category balance check
        balance_suggestions = self._check_category_balance()
        suggestions.extend(balance_suggestions)

        # Workload optimization
        workload_suggestions = self._check_workload_optimization()
        suggestions.extend(workload_suggestions)

        # Time pattern recommendations
        time_suggestions = self._check_time_patterns()
        suggestions.extend(time_suggestions)

        # Quick wins
        quick_win_suggestions = self._find_quick_wins()
        suggestions.extend(quick_win_suggestions)

        return suggestions[:4]  # Max 4 suggestions

    def _check_category_balance(self) -> List[Dict]:
        """Check if user is ignoring certain categories"""
        suggestions = []

        # Check last 3 days of tasks
        three_days_ago = self.today - timedelta(days=3)

        # Get all active goal categories
        active_goals = GoalSpec.objects.filter(
            user=self.user,
            is_active=True
        ).values_list('category', flat=True)

        for category in active_goals:
            # Check if category has been worked on
            recent_tasks = Todo.objects.filter(
                user=self.user,
                goalspec__category=category,
                scheduled_date__gte=three_days_ago,
                scheduled_date__lte=self.today
            )

            if not recent_tasks.exists():
                category_name = self._translate_category(category)

                # Suggest adding task
                suggestions.append({
                    'type': 'category_balance',
                    'category': category,
                    'message': f"Ты не делал {category_name} 3+ дня — добавить короткую задачу?",
                    'action': {
                        'type': 'add_task',
                        'category': category,
                        'timebox': 30
                    }
                })

        return suggestions

    def _check_workload_optimization(self) -> List[Dict]:
        """Suggest workload optimization"""
        suggestions = []

        workload = self._calculate_workload()

        if workload['percentage'] > 80:
            # Too many tasks
            suggestions.append({
                'type': 'workload_high',
                'message': f"Загрузка {workload['percentage']}% — можно перенести {workload['task_count'] // 3} задач на завтра?",
                'action': {
                    'type': 'reschedule',
                    'count': workload['task_count'] // 3
                }
            })
        elif workload['percentage'] < 40:
            # Light day
            suggestions.append({
                'type': 'workload_light',
                'message': f"Лёгкий день ({workload['percentage']}%) — отлично для quick wins!",
                'action': {
                    'type': 'suggest_quick_wins'
                }
            })

        return suggestions

    def _check_time_patterns(self) -> List[Dict]:
        """Use behavior patterns to suggest better timing"""
        suggestions = []

        # Get recent failure_time patterns
        time_patterns = UserBehaviorPattern.objects.filter(
            user=self.user,
            pattern_type='failure_time',
            is_active=True
        ).order_by('-confidence_score').first()

        if time_patterns:
            problematic_slot = time_patterns.data.get('time_slot')
            affected_category = time_patterns.data.get('common_categories', [[]])[0][0] if time_patterns.data.get('common_categories') else None

            if problematic_slot and affected_category:
                better_time = self._suggest_better_time(problematic_slot)
                category_name = self._translate_category(affected_category)

                suggestions.append({
                    'type': 'time_optimization',
                    'message': f"Задачи по {category_name} лучше работают {better_time}",
                    'pattern_data': time_patterns.data,
                    'action': {
                        'type': 'reschedule_category',
                        'category': affected_category,
                        'to_time': better_time
                    }
                })

        return suggestions

    def _find_quick_wins(self) -> List[Dict]:
        """Find quick win tasks for momentum"""
        suggestions = []

        # Get quick win tasks (< 20 min, priority 1-2)
        quick_wins = Todo.objects.filter(
            user=self.user,
            scheduled_date=self.today,
            timebox_minutes__lte=20,
            priority__in=[1, 2],
            status__in=['ready', 'pending']
        )

        count = quick_wins.count()
        if count >= 2:
            task_ids = list(quick_wins.values_list('id', flat=True)[:3])
            suggestions.append({
                'type': 'quick_win',
                'message': f"У тебя есть {count} quick win задач (до 20 мин) — отлично для старта дня!",
                'task_ids': task_ids
            })

        return suggestions

    # ==========================================
    # Block 6: 📈 Weekly Progress
    # ==========================================

    def _calculate_weekly_progress(self) -> Dict:
        """Calculate weekly progress summary"""
        week_start = self.today - timedelta(days=self.today.weekday())

        # Get tasks for this week
        week_tasks = Todo.objects.filter(
            user=self.user,
            scheduled_date__gte=week_start,
            scheduled_date__lte=self.today
        )

        total = week_tasks.count()
        completed = week_tasks.filter(status='done').count()
        overdue = week_tasks.filter(
            status__in=['pending', 'ready'],
            scheduled_date__lt=self.today
        ).count()

        completion_rate = int((completed / total * 100)) if total > 0 else 0

        # Get streak
        streak = getattr(self.user, 'current_streak', 0)

        return {
            'completion_rate': completion_rate,
            'completed_tasks': completed,
            'total_tasks': total,
            'overdue_tasks': overdue,
            'streak_days': streak
        }

    # ==========================================
    # Formatting
    # ==========================================

    def _format_full_message(
        self,
        greeting: str,
        priorities: List[Dict],
        workload: Dict,
        warnings: List[Dict],
        suggestions: List[Dict],
        weekly_progress: Dict
    ) -> str:
        """Format complete daily brief message"""
        lines = []

        # Block 1: Greeting
        lines.append(greeting)
        lines.append("")

        # Block 2: Priorities
        if priorities:
            count = len(priorities)
            lines.append(f"🎯 Сегодня у тебя {count} приоритет{'а' if count == 2 else 'ов' if count > 2 else ''}:")
            for p in priorities:
                line = f"• {p['title']}"
                if 'deadline' in p:
                    days = p.get('days_until_deadline', 0)
                    if days == 0:
                        line += " (deadline сегодня)"
                    elif days == 1:
                        line += " (deadline завтра)"
                    else:
                        line += f" (deadline через {days} дня)"
                lines.append(line)
            lines.append("")

        # Block 3: Workload
        status_text = {
            'light': 'лёгкий день',
            'optimal': 'оптимально',
            'heavy': 'насыщенный день',
            'overloaded': 'перегрузка'
        }
        emoji = {
            'light': '😌',
            'optimal': '⚡',
            'heavy': '💪',
            'overloaded': '⚠️'
        }
        lines.append(f"{emoji.get(workload['status'], '📊')} Общая загрузка — {workload['percentage']}% ({status_text.get(workload['status'], 'нормально')})")
        hours = workload['total_minutes'] // 60
        minutes = workload['total_minutes'] % 60
        lines.append(f"   Запланировано: {hours} ч {minutes} мин")
        lines.append("")

        # Block 4: Warnings
        if warnings:
            lines.append("⚠️ Напоминания:")
            for w in warnings[:3]:  # Max 3
                lines.append(f"• {w['message']}")
            lines.append("")

        # Block 5: Suggestions
        if suggestions:
            lines.append("💡 Smart suggestions:")
            for s in suggestions[:3]:  # Max 3
                lines.append(f"• {s['message']}")
            lines.append("")

        # Block 6: Weekly Progress
        lines.append("📈 Прогресс недели:")
        lines.append(f"   {weekly_progress['completion_rate']}% выполнено ({weekly_progress['completed_tasks']}/{weekly_progress['total_tasks']} задач)")
        if weekly_progress['overdue_tasks'] > 0:
            lines.append(f"   {weekly_progress['overdue_tasks']} просрочено")
        if weekly_progress['streak_days'] >= 3:
            lines.append(f"   🔥 Streak: {weekly_progress['streak_days']} дней!")
        lines.append("")

        lines.append("Готов начать день? 🚀")

        return "\n".join(lines)

    # ==========================================
    # Helper Methods
    # ==========================================

    def _translate_category(self, category: str) -> str:
        """Translate category to Russian"""
        translations = {
            'study': 'учёба',
            'career': 'карьера',
            'sport': 'спорт',
            'health': 'здоровье',
            'finance': 'финансы',
            'creative': 'творчество',
            'admin': 'админ',
            'other': 'другое'
        }
        return translations.get(category, category)

    def _suggest_better_time(self, problematic_slot: str) -> str:
        """Suggest better time based on problematic slot"""
        suggestions = {
            'evening': 'утром (9-11 am)',
            'night': 'днём (2-4 pm)',
            'morning': 'днём (12-2 pm)',
            'afternoon': 'утром (8-10 am)'
        }
        return suggestions.get(problematic_slot, 'другое время')
