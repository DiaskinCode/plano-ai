"""
Analytics Services for PathAI
- BehaviorAnalyzer: Analyzes user behavior patterns
- ReflectionGenerator: Generates weekly reflections
"""
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from django.utils import timezone
from django.db.models import Count, Q, Avg, F
from collections import defaultdict, Counter

from .models import UserBehaviorPattern, WeeklyReflection
from todos.models import Todo
from todos.advanced_models import TaskCompletion
from chat.models import ChatMessage
from users.models import User, GoalSpec
from ai.services import AIService


class BehaviorAnalyzer:
    """
    Analyzes user behavior patterns for reflection generation

    Pattern types:
    1. failure_time: When user fails/skips tasks (time of day)
    2. failure_category: Which categories user fails most
    3. procrastination: Which tasks get delayed
    4. chat_topics: What user discusses with AI
    """

    def __init__(self, user: User):
        self.user = user
        self.ai_service = AIService(provider='anthropic')

    def analyze_all_patterns(self, start_date: datetime.date, end_date: datetime.date) -> List[UserBehaviorPattern]:
        """
        Analyze all behavior patterns for a time window

        Args:
            start_date: Start of analysis window
            end_date: End of analysis window

        Returns:
            List of detected behavior patterns
        """
        patterns = []

        # 1. Analyze failure patterns by time
        time_patterns = self.analyze_failure_by_time(start_date, end_date)
        patterns.extend(time_patterns)

        # 2. Analyze failure patterns by category
        category_patterns = self.analyze_failure_by_category(start_date, end_date)
        patterns.extend(category_patterns)

        # 3. Analyze procrastination patterns
        procrastination_patterns = self.analyze_procrastination(start_date, end_date)
        patterns.extend(procrastination_patterns)

        # 4. Analyze chat topics
        chat_patterns = self.analyze_chat_topics(start_date, end_date)
        patterns.extend(chat_patterns)

        return patterns

    def analyze_failure_by_time(self, start_date: datetime.date, end_date: datetime.date) -> List[UserBehaviorPattern]:
        """
        Analyze when user fails/skips tasks (morning/afternoon/evening/night)
        """
        patterns = []

        # Get all failed/skipped tasks in time window
        failed_tasks = Todo.objects.filter(
            user=self.user,
            scheduled_date__range=[start_date, end_date],
            status__in=['skipped']
        ).exclude(scheduled_time__isnull=True)

        if failed_tasks.count() < 3:
            # Not enough data
            return patterns

        # Group by time of day
        time_slots = {
            'morning': [],    # 6am - 12pm
            'afternoon': [],  # 12pm - 6pm
            'evening': [],    # 6pm - 10pm
            'night': []       # 10pm - 6am
        }

        for task in failed_tasks:
            hour = task.scheduled_time.hour
            if 6 <= hour < 12:
                time_slots['morning'].append(task)
            elif 12 <= hour < 18:
                time_slots['afternoon'].append(task)
            elif 18 <= hour < 22:
                time_slots['evening'].append(task)
            else:
                time_slots['night'].append(task)

        # Find the most problematic time slot
        total_failed = failed_tasks.count()
        for slot_name, tasks in time_slots.items():
            if len(tasks) >= 3:  # Minimum threshold
                failure_rate = len(tasks) / total_failed

                if failure_rate >= 0.4:  # 40% or more failures in this slot
                    # Extract task categories
                    categories = []
                    for task in tasks:
                        if task.goalspec:
                            categories.append(task.goalspec.category)

                    pattern, created = UserBehaviorPattern.objects.get_or_create(
                        user=self.user,
                        pattern_type='failure_time',
                        time_window_start=start_date,
                        defaults={
                            'time_window_end': end_date,
                            'data': {
                                'time_slot': slot_name,
                                'failure_rate': round(failure_rate, 2),
                                'tasks_affected': len(tasks),
                                'task_ids': [t.id for t in tasks[:5]],
                                'common_categories': Counter(categories).most_common(2) if categories else []
                            },
                            'confidence_score': min(0.9, failure_rate + 0.2),
                            'is_active': True
                        }
                    )
                    if not created:
                        # Update existing pattern
                        pattern.data = {
                            'time_slot': slot_name,
                            'failure_rate': round(failure_rate, 2),
                            'tasks_affected': len(tasks),
                            'task_ids': [t.id for t in tasks[:5]],
                            'common_categories': Counter(categories).most_common(2) if categories else []
                        }
                        pattern.confidence_score = min(0.9, failure_rate + 0.2)
                        pattern.save()
                    patterns.append(pattern)

        return patterns

    def analyze_failure_by_category(self, start_date: datetime.date, end_date: datetime.date) -> List[UserBehaviorPattern]:
        """
        Analyze which goal categories user fails most
        """
        patterns = []

        # Get all tasks with categories
        all_tasks = Todo.objects.filter(
            user=self.user,
            scheduled_date__range=[start_date, end_date],
            goalspec__isnull=False
        )

        if all_tasks.count() < 5:
            return patterns

        # Group by category
        category_stats = defaultdict(lambda: {'total': 0, 'skipped': 0, 'task_ids': []})

        for task in all_tasks:
            category = task.goalspec.category
            category_stats[category]['total'] += 1

            if task.status == 'skipped':
                category_stats[category]['skipped'] += 1
                category_stats[category]['task_ids'].append(task.id)

        # Find categories with high failure rate
        for category, stats in category_stats.items():
            if stats['total'] >= 3:  # Minimum tasks
                failure_rate = stats['skipped'] / stats['total']

                if failure_rate >= 0.5:  # 50% or more failures
                    pattern, created = UserBehaviorPattern.objects.get_or_create(
                        user=self.user,
                        pattern_type='failure_category',
                        time_window_start=start_date,
                        defaults={
                            'time_window_end': end_date,
                            'data': {
                                'category': category,
                                'failure_rate': round(failure_rate, 2),
                                'total_tasks': stats['total'],
                                'skipped_tasks': stats['skipped'],
                                'task_ids': stats['task_ids'][:5]
                            },
                            'confidence_score': min(0.9, failure_rate + 0.1),
                            'is_active': True
                        }
                    )
                    if not created:
                        pattern.data = {
                            'category': category,
                            'failure_rate': round(failure_rate, 2),
                            'total_tasks': stats['total'],
                            'skipped_tasks': stats['skipped'],
                            'task_ids': stats['task_ids'][:5]
                        }
                        pattern.confidence_score = min(0.9, failure_rate + 0.1)
                        pattern.save()
                    patterns.append(pattern)

        return patterns

    def analyze_procrastination(self, start_date: datetime.date, end_date: datetime.date) -> List[UserBehaviorPattern]:
        """
        Analyze which tasks get delayed (pending > 3 days)
        """
        patterns = []

        # Get tasks that were rescheduled or stayed pending for long
        delayed_tasks = Todo.objects.filter(
            user=self.user,
            created_at__date__lte=end_date - timedelta(days=3),
            scheduled_date__range=[start_date, end_date],
            status='pending'
        ).select_related('goalspec')

        if delayed_tasks.count() < 3:
            return patterns

        # Group by category
        category_delays = defaultdict(lambda: {'tasks': [], 'avg_delay': 0})

        for task in delayed_tasks:
            if task.goalspec:
                category = task.goalspec.category
                delay_days = (timezone.now().date() - task.created_at.date()).days
                category_delays[category]['tasks'].append({
                    'id': task.id,
                    'title': task.title,
                    'delay_days': delay_days
                })

        # Calculate average delay per category
        for category, data in category_delays.items():
            if len(data['tasks']) >= 2:
                avg_delay = sum(t['delay_days'] for t in data['tasks']) / len(data['tasks'])

                if avg_delay >= 3:  # Average delay of 3+ days
                    pattern, created = UserBehaviorPattern.objects.get_or_create(
                        user=self.user,
                        pattern_type='procrastination',
                        time_window_start=start_date,
                        defaults={
                            'time_window_end': end_date,
                            'data': {
                                'category': category,
                                'avg_delay_days': round(avg_delay, 1),
                                'tasks_count': len(data['tasks']),
                                'task_examples': data['tasks'][:3]
                            },
                            'confidence_score': min(0.85, avg_delay / 10),
                            'is_active': True
                        }
                    )
                    if not created:
                        pattern.data = {
                            'category': category,
                            'avg_delay_days': round(avg_delay, 1),
                            'tasks_count': len(data['tasks']),
                            'task_examples': data['tasks'][:3]
                        }
                        pattern.confidence_score = min(0.85, avg_delay / 10)
                        pattern.save()
                    patterns.append(pattern)

        return patterns

    def analyze_chat_topics(self, start_date: datetime.date, end_date: datetime.date) -> List[UserBehaviorPattern]:
        """
        Use AI to extract topics from chat messages
        """
        patterns = []

        # Get user's chat messages from the week
        messages = ChatMessage.objects.filter(
            user=self.user,
            role='user',
            created_at__date__range=[start_date, end_date]
        ).order_by('created_at')

        if messages.count() < 5:
            # Not enough chat data
            return patterns

        # Combine messages into chunks for AI analysis
        message_texts = [msg.content for msg in messages]
        combined_text = "\n---\n".join(message_texts[:50])  # Limit to 50 messages

        # Use AI to extract topics
        try:
            system_prompt = """You are analyzing user chat messages to identify recurring topics and themes.

Your task:
1. Identify the 3 most frequently discussed topics
2. For each topic, estimate the emotional tone (neutral, anxious, excited, frustrated)
3. Count approximate frequency

Output as JSON:
{
  "topics": [
    {
      "topic": "topic name",
      "frequency": number of times mentioned,
      "sentiment": "neutral/anxious/excited/frustrated",
      "keywords": ["keyword1", "keyword2"]
    }
  ]
}
"""

            user_prompt = f"""Analyze these user messages and identify the top 3 topics:

{combined_text}

Return only the JSON response."""

            response = self.ai_service._call_anthropic(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                response_format='text'
            )

            # Parse AI response
            # Remove markdown code block if present
            response = response.strip()
            if response.startswith('```json'):
                response = response[7:]
            if response.startswith('```'):
                response = response[3:]
            if response.endswith('```'):
                response = response[:-3]
            response = response.strip()

            analysis = json.loads(response)

            # Create patterns for each topic
            for topic_data in analysis.get('topics', [])[:3]:
                if topic_data.get('frequency', 0) >= 3:
                    pattern, created = UserBehaviorPattern.objects.get_or_create(
                        user=self.user,
                        pattern_type='chat_topics',
                        time_window_start=start_date,
                        defaults={
                            'time_window_end': end_date,
                            'data': {
                                'topic': topic_data.get('topic', 'Unknown'),
                                'frequency': topic_data.get('frequency', 0),
                                'sentiment': topic_data.get('sentiment', 'neutral'),
                                'keywords': topic_data.get('keywords', [])
                            },
                            'confidence_score': 0.7,
                            'is_active': True
                        }
                    )
                    if not created:
                        pattern.data = {
                            'topic': topic_data.get('topic', 'Unknown'),
                            'frequency': topic_data.get('frequency', 0),
                            'sentiment': topic_data.get('sentiment', 'neutral'),
                            'keywords': topic_data.get('keywords', [])
                        }
                        pattern.save()
                    patterns.append(pattern)

        except Exception as e:
            print(f"Error analyzing chat topics: {e}")
            # Fallback: simple keyword counting
            pass

        return patterns


class ReflectionGenerator:
    """
    Generates weekly reflections based on behavior patterns

    Output format is adaptive:
    - Short (2-3 insights) if few patterns detected
    - Detailed (5+ insights) if many patterns detected
    """

    def __init__(self, user: User):
        self.user = user
        self.ai_service = AIService(provider='anthropic')

    def generate_weekly_reflection(
        self,
        week_start: datetime.date,
        week_end: datetime.date,
        method: str = 'scheduled'
    ) -> Optional[WeeklyReflection]:
        """
        Generate a weekly reflection for the user

        Args:
            week_start: Monday of the week
            week_end: Sunday of the week
            method: 'scheduled' or 'on_demand'

        Returns:
            WeeklyReflection instance or None if not enough data
        """
        # Check if reflection already exists
        existing = WeeklyReflection.objects.filter(
            user=self.user,
            week_start_date=week_start
        ).first()

        if existing:
            return existing

        # Analyze patterns
        analyzer = BehaviorAnalyzer(self.user)
        patterns = analyzer.analyze_all_patterns(week_start, week_end)

        if not patterns:
            # Not enough data to generate reflection
            return None

        # Build insights from patterns
        insights = self._build_insights(patterns)

        # Generate action items
        action_items = self._generate_action_items(patterns)

        # Generate full reflection message with AI
        full_message = self._format_adaptive_message(patterns, insights, action_items, week_start, week_end)

        # Create reflection
        reflection = WeeklyReflection.objects.create(
            user=self.user,
            week_start_date=week_start,
            week_end_date=week_end,
            insights=insights,
            action_items=action_items,
            full_message=full_message,
            patterns_analyzed=len(patterns),
            generation_method=method
        )

        return reflection

    def _build_insights(self, patterns: List[UserBehaviorPattern]) -> List[Dict[str, Any]]:
        """Build structured insights from patterns"""
        insights = []

        for pattern in patterns:
            insight = {
                'type': pattern.pattern_type,
                'icon': self._get_icon(pattern.pattern_type),
                'priority': self._calculate_priority(pattern),
                'evidence': pattern.data
            }

            # Generate human-readable message
            if pattern.pattern_type == 'failure_time':
                time_slot = pattern.data.get('time_slot', 'unknown')
                count = pattern.data.get('tasks_affected', 0)
                categories = pattern.data.get('common_categories', [])

                message = f"Ты откладывал задачи {count} раз — все были запланированы на {self._translate_time_slot(time_slot)}"
                if categories:
                    top_category = categories[0][0]
                    message += f" (чаще всего {self._translate_category(top_category)})"

                insight['message'] = message

            elif pattern.pattern_type == 'failure_category':
                category = pattern.data.get('category', 'unknown')
                rate = int(pattern.data.get('failure_rate', 0) * 100)
                count = pattern.data.get('skipped_tasks', 0)

                insight['message'] = f"Ты пропустил {count} {self._translate_category(category)} задач ({rate}%)"

            elif pattern.pattern_type == 'procrastination':
                category = pattern.data.get('category', 'unknown')
                avg_delay = pattern.data.get('avg_delay_days', 0)
                count = pattern.data.get('tasks_count', 0)

                insight['message'] = f"Задачи по {self._translate_category(category)} откладываются в среднем на {avg_delay} дней ({count} задач)"

            elif pattern.pattern_type == 'chat_topics':
                topic = pattern.data.get('topic', 'unknown')
                freq = pattern.data.get('frequency', 0)
                sentiment = pattern.data.get('sentiment', 'neutral')

                insight['message'] = f"Чаще всего обсуждал: {topic} ({freq} раз)"
                if sentiment != 'neutral':
                    insight['message'] += f" — {self._translate_sentiment(sentiment)}"

            insights.append(insight)

        # Sort by priority
        insights.sort(key=lambda x: x['priority'], reverse=True)

        return insights

    def _generate_action_items(self, patterns: List[UserBehaviorPattern]) -> List[Dict[str, Any]]:
        """Generate actionable suggestions from patterns"""
        actions = []

        for pattern in patterns:
            if pattern.pattern_type == 'failure_time':
                time_slot = pattern.data.get('time_slot', '')
                task_ids = pattern.data.get('task_ids', [])

                # Suggest rescheduling to better time
                better_time = self._suggest_better_time(time_slot)
                actions.append({
                    'action': 'reschedule_tasks',
                    'description': f"Перенести задачи на {better_time}",
                    'task_ids': task_ids,
                    'impact': 'high'
                })

            elif pattern.pattern_type == 'failure_category':
                category = pattern.data.get('category', '')

                actions.append({
                    'action': 'review_category',
                    'description': f"Пересмотреть приоритеты для {self._translate_category(category)}",
                    'category': category,
                    'impact': 'medium'
                })

            elif pattern.pattern_type == 'chat_topics':
                topic = pattern.data.get('topic', '')

                actions.append({
                    'action': 'create_recurring',
                    'description': f"Добавить recurring задачу: {topic}",
                    'impact': 'medium'
                })

        return actions

    def _format_adaptive_message(
        self,
        patterns: List[UserBehaviorPattern],
        insights: List[Dict],
        action_items: List[Dict],
        week_start: datetime.date,
        week_end: datetime.date
    ) -> str:
        """Generate adaptive reflection message using AI"""

        # Prepare context for AI
        patterns_summary = json.dumps([
            {
                'type': p.pattern_type,
                'data': p.data,
                'confidence': p.confidence_score
            }
            for p in patterns
        ], ensure_ascii=False, indent=2)

        insights_summary = json.dumps(insights, ensure_ascii=False, indent=2)
        actions_summary = json.dumps(action_items, ensure_ascii=False, indent=2)

        # AI prompt
        system_prompt = """Ты — персональный AI-коуч для Path AI, который пишет еженедельные рефлексии пользователю.

Твоя задача:
1. Проанализировать паттерны поведения пользователя за неделю
2. Написать краткую, дружелюбную рефлексию на русском языке
3. Формат адаптивный: если паттернов мало (1-2) — короткая рефлексия, если много (3+) — детальная

Стиль:
- Дружелюбный, но профессиональный
- Используй эмодзи (🔴 для проблем, 💬 для чатов, ✨ для предложений)
- Конкретные примеры, а не общие фразы
- Акцент на действия, а не просто наблюдения

Структура:
```
📊 Твоя неделя: [даты]

[Секция с паттернами]

[Секция с предложениями]
```
"""

        week_label = f"{week_start.strftime('%d %b')} - {week_end.strftime('%d %b')}"

        user_prompt = f"""Создай рефлексию для недели: {week_label}

Обнаруженные паттерны:
{patterns_summary}

Инсайты:
{insights_summary}

Предложенные действия:
{actions_summary}

Напиши короткую рефлексию (3-5 абзацев) на русском языке."""

        try:
            message = self.ai_service._call_anthropic(
                system_prompt=system_prompt,
                user_prompt=user_prompt
            )
            return message.strip()
        except Exception as e:
            print(f"Error generating reflection message: {e}")
            # Fallback to simple template
            return self._fallback_message(insights, action_items, week_label)

    def _fallback_message(self, insights: List[Dict], action_items: List[Dict], week_label: str) -> str:
        """Fallback message if AI fails"""
        lines = [f"📊 Твоя неделя: {week_label}\n"]

        if insights:
            lines.append("🔍 Что я заметил:")
            for insight in insights[:3]:
                lines.append(f"• {insight['message']}")
            lines.append("")

        if action_items:
            lines.append("✨ Что можно улучшить:")
            for action in action_items[:3]:
                lines.append(f"• {action['description']}")

        return "\n".join(lines)

    # Helper methods

    def _get_icon(self, pattern_type: str) -> str:
        icons = {
            'failure_time': '🔴',
            'failure_category': '📉',
            'procrastination': '⏳',
            'chat_topics': '💬'
        }
        return icons.get(pattern_type, '📊')

    def _calculate_priority(self, pattern: UserBehaviorPattern) -> int:
        """Calculate priority (1-5) based on confidence and impact"""
        base_priority = 3

        if pattern.confidence_score > 0.8:
            base_priority += 1

        if pattern.pattern_type in ['failure_time', 'failure_category']:
            base_priority += 1

        return min(5, base_priority)

    def _translate_time_slot(self, slot: str) -> str:
        translations = {
            'morning': 'утро',
            'afternoon': 'день',
            'evening': 'вечер',
            'night': 'ночь'
        }
        return translations.get(slot, slot)

    def _translate_category(self, category: str) -> str:
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

    def _translate_sentiment(self, sentiment: str) -> str:
        translations = {
            'anxious': 'тревожно',
            'excited': 'с энтузиазмом',
            'frustrated': 'с фрустрацией',
            'neutral': 'нейтрально'
        }
        return translations.get(sentiment, sentiment)

    def _suggest_better_time(self, problematic_slot: str) -> str:
        suggestions = {
            'evening': 'утро (9-11 am)',
            'night': 'день (2-4 pm)',
            'morning': 'день (12-2 pm)',
            'afternoon': 'утро (8-10 am)'
        }
        return suggestions.get(problematic_slot, 'другое время')
