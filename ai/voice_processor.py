"""
Voice Command Processor

Handles voice-to-text commands and generates intelligent responses.

Supported intents:
- create_task
- complete_task
- list_tasks
- coach_query
- performance_query
- daily_checkin
"""

import os
from anthropic import Anthropic
from typing import Dict, Optional
from datetime import datetime, timedelta
from django.utils import timezone
import json


class VoiceProcessor:
    """
    Processes voice commands and returns structured responses.
    """

    def __init__(self):
        self.anthropic = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        self.model = "claude-3-5-sonnet-20241022"

    def process_command(self, user, transcript: str) -> Dict:
        """
        Main entry point: Process voice command.

        Args:
            user: Django user object
            transcript: Voice-to-text transcript

        Returns:
            {
                "intent": "create_task",
                "action_taken": {...},
                "response_text": "Got it! I've added...",
                "success": True
            }
        """
        # Classify intent
        intent = self._classify_intent(transcript)

        if not intent:
            return {
                "intent": "unknown",
                "action_taken": None,
                "response_text": "I didn't understand that. Could you try again?",
                "success": False
            }

        # Execute based on intent
        if intent['type'] == 'create_task':
            return self._handle_create_task(user, intent)

        elif intent['type'] == 'complete_task':
            return self._handle_complete_task(user, intent)

        elif intent['type'] == 'list_tasks':
            return self._handle_list_tasks(user, intent)

        elif intent['type'] == 'coach_query':
            return self._handle_coach_query(user, intent)

        elif intent['type'] == 'performance_query':
            return self._handle_performance_query(user, intent)

        elif intent['type'] == 'daily_checkin':
            return self._handle_daily_checkin(user, intent)

        else:
            return {
                "intent": intent['type'],
                "action_taken": None,
                "response_text": "I can help with that, but this feature is coming soon!",
                "success": False
            }

    def _classify_intent(self, transcript: str) -> Optional[Dict]:
        """
        Use Claude to classify voice command intent.

        Returns:
            {
                "type": "create_task",
                "entities": {
                    "task_title": "Review Cambridge application",
                    "deadline": "2025-11-08",
                    "priority": "high"
                },
                "sentiment": "neutral"
            }
        """
        prompt = f"""You are PathAI's voice assistant. Classify this user voice command.

Voice command: "{transcript}"

Classify into ONE of these intents:
1. **create_task**: User wants to add a new task
   - Extract: task_title, deadline (if mentioned), priority
2. **complete_task**: User finished a task
   - Extract: task_identifier (title or partial match)
3. **list_tasks**: User wants to see tasks
   - Extract: filter (today, week, all, overdue)
4. **coach_query**: User asking coach for advice/help
   - Extract: question_topic
5. **performance_query**: User asking about their progress
   - Extract: time_period (today, week, month)
6. **daily_checkin**: User doing daily check-in
   - Extract: completed_count, feelings

Also extract:
- **sentiment**: positive, neutral, negative, stressed

Return JSON ONLY:
{{
    "type": "create_task",
    "entities": {{
        "task_title": "Review Cambridge application",
        "deadline": "2025-11-08",
        "priority": "medium"
    }},
    "sentiment": "neutral"
}}

If command is unclear, return {{"type": "unknown"}}.
"""

        try:
            response = self.anthropic.messages.create(
                model=self.model,
                max_tokens=500,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = response.content[0].text

            # Extract JSON
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()

            intent = json.loads(response_text)
            return intent

        except Exception as e:
            print(f"Error classifying intent: {e}")
            return None

    def _handle_create_task(self, user, intent: Dict) -> Dict:
        """Create task from voice command."""
        from todos.models import Todo

        entities = intent.get('entities', {})
        task_title = entities.get('task_title', 'Untitled task')

        # Parse deadline
        deadline_str = entities.get('deadline')
        if deadline_str:
            try:
                scheduled_date = datetime.strptime(deadline_str, '%Y-%m-%d').date()
            except:
                scheduled_date = timezone.now().date() + timedelta(days=7)
        else:
            scheduled_date = timezone.now().date() + timedelta(days=7)

        # Parse priority
        priority_map = {'high': 3, 'medium': 2, 'low': 1}
        priority = priority_map.get(entities.get('priority', 'medium'), 2)

        # Create task
        try:
            task = Todo.objects.create(
                user=user,
                title=task_title,
                priority=priority,
                scheduled_date=scheduled_date,
                status='ready',
                source='ai_generated',
                notes='Created via voice command',
                timebox_minutes=30,
            )

            # Generate response
            deadline_phrase = ""
            if deadline_str:
                date_obj = datetime.strptime(deadline_str, '%Y-%m-%d')
                if date_obj.date() == timezone.now().date():
                    deadline_phrase = "for today"
                elif date_obj.date() == timezone.now().date() + timedelta(days=1):
                    deadline_phrase = "for tomorrow"
                else:
                    deadline_phrase = f"for {date_obj.strftime('%A, %B %d')}"

            response_text = f"Got it! I've added '{task_title}' {deadline_phrase}."

            return {
                "intent": "create_task",
                "action_taken": {
                    "task_id": task.id,
                    "title": task.title,
                    "scheduled_date": str(task.scheduled_date),
                    "priority": task.priority,
                },
                "response_text": response_text,
                "success": True
            }

        except Exception as e:
            print(f"Error creating task: {e}")
            return {
                "intent": "create_task",
                "action_taken": None,
                "response_text": "Sorry, I couldn't create that task. Please try again.",
                "success": False
            }

    def _handle_complete_task(self, user, intent: Dict) -> Dict:
        """Mark task as complete from voice command."""
        from todos.models import Todo

        entities = intent.get('entities', {})
        task_identifier = entities.get('task_identifier', '')

        # Find matching task
        tasks = Todo.objects.filter(
            user=user,
            status__in=['ready', 'in_progress'],
            title__icontains=task_identifier
        ).order_by('-priority', 'scheduled_date')[:1]

        if not tasks.exists():
            return {
                "intent": "complete_task",
                "action_taken": None,
                "response_text": f"I couldn't find a task matching '{task_identifier}'. Can you be more specific?",
                "success": False
            }

        task = tasks.first()
        task.status = 'done'
        task.completed_at = timezone.now()
        task.save(update_fields=['status', 'completed_at'])

        # Count today's completions
        today_completed = Todo.objects.filter(
            user=user,
            completed_at__date=timezone.now().date()
        ).count()

        response_text = f"Awesome! '{task.title}' is marked done. That's task {today_completed} today!"

        return {
            "intent": "complete_task",
            "action_taken": {
                "task_id": task.id,
                "title": task.title,
                "today_count": today_completed,
            },
            "response_text": response_text,
            "success": True
        }

    def _handle_list_tasks(self, user, intent: Dict) -> Dict:
        """List tasks based on filter."""
        from todos.models import Todo

        entities = intent.get('entities', {})
        filter_type = entities.get('filter', 'today')

        if filter_type == 'today':
            tasks = Todo.objects.filter(
                user=user,
                scheduled_date=timezone.now().date(),
                status__in=['ready', 'in_progress']
            ).order_by('-priority')[:5]

        elif filter_type == 'overdue':
            tasks = Todo.objects.filter(
                user=user,
                scheduled_date__lt=timezone.now().date(),
                status__in=['ready', 'in_progress']
            ).order_by('scheduled_date')[:5]

        else:  # this week
            week_end = timezone.now().date() + timedelta(days=7)
            tasks = Todo.objects.filter(
                user=user,
                scheduled_date__lte=week_end,
                status__in=['ready', 'in_progress']
            ).order_by('-priority', 'scheduled_date')[:5]

        if not tasks.exists():
            return {
                "intent": "list_tasks",
                "action_taken": {"tasks": []},
                "response_text": f"You have no {filter_type} tasks. Great job staying on top of things!",
                "success": True
            }

        # Build response
        task_list = []
        for i, task in enumerate(tasks, 1):
            task_list.append({
                "id": task.id,
                "title": task.title,
                "priority": task.priority,
                "scheduled_date": str(task.scheduled_date),
            })

        response_lines = [f"Here are your {filter_type} tasks:"]
        for i, task in enumerate(tasks, 1):
            priority_marker = "🔥" if task.priority == 3 else "⭐" if task.priority == 2 else "📝"
            response_lines.append(f"{i}. {priority_marker} {task.title}")

        response_text = "\n".join(response_lines)

        return {
            "intent": "list_tasks",
            "action_taken": {"tasks": task_list},
            "response_text": response_text,
            "success": True
        }

    def _handle_coach_query(self, user, intent: Dict) -> Dict:
        """Answer coach query using performance insights."""
        from ai.performance_analyzer import performance_analyzer

        # Get performance insights
        analysis = performance_analyzer.analyze_user_performance(user)

        entities = intent.get('entities', {})
        question_topic = entities.get('question_topic', 'general')

        # Generate personalized response
        completion_rate = analysis.get('completion_rate', 0)
        risk_level = analysis.get('risk_level', 'unknown')
        strengths = analysis.get('strengths', [])

        if risk_level in ['high', 'critical']:
            response = (
                f"I'm noticing you're falling behind - your completion rate is {int(completion_rate * 100)}%. "
                f"Let me help: {analysis.get('recommended_actions', ['Focus on quick wins'])[0]}"
            )
        elif completion_rate >= 0.7:
            response = (
                f"You're doing great! {int(completion_rate * 100)}% completion rate this month. "
                f"{strengths[0] if strengths else 'Keep up the momentum!'}"
            )
        else:
            response = (
                f"You're at {int(completion_rate * 100)}% completion. Room for improvement. "
                f"Here's my suggestion: {analysis.get('recommended_actions', ['Break down large tasks'])[0]}"
            )

        return {
            "intent": "coach_query",
            "action_taken": {"analysis": analysis},
            "response_text": response,
            "success": True
        }

    def _handle_performance_query(self, user, intent: Dict) -> Dict:
        """Answer performance query."""
        from todos.models import Todo

        entities = intent.get('entities', {})
        time_period = entities.get('time_period', 'week')

        # Calculate stats
        if time_period == 'today':
            date_filter = timezone.now().date()
            tasks = Todo.objects.filter(user=user, scheduled_date=date_filter)
        elif time_period == 'week':
            week_start = timezone.now().date() - timedelta(days=timezone.now().weekday())
            tasks = Todo.objects.filter(user=user, scheduled_date__gte=week_start)
        else:  # month
            month_start = timezone.now().date().replace(day=1)
            tasks = Todo.objects.filter(user=user, scheduled_date__gte=month_start)

        total = tasks.count()
        completed = tasks.filter(status='done').count()
        completion_rate = (completed / total * 100) if total > 0 else 0

        response_text = (
            f"This {time_period}, you've completed {completed} out of {total} tasks. "
            f"That's {int(completion_rate)}% completion rate. "
            f"Your current streak is {user.current_streak} days."
        )

        return {
            "intent": "performance_query",
            "action_taken": {
                "completed": completed,
                "total": total,
                "completion_rate": completion_rate,
                "streak": user.current_streak,
            },
            "response_text": response_text,
            "success": True
        }

    def _handle_daily_checkin(self, user, intent: Dict) -> Dict:
        """Process daily check-in from voice."""
        # This could create a CheckInEvent or trigger adaptive coach
        entities = intent.get('entities', {})
        completed_count = entities.get('completed_count', 0)
        feelings = entities.get('feelings', 'neutral')

        response_text = (
            f"Thanks for checking in! I've recorded that you completed {completed_count} tasks today. "
            f"How are you feeling about your progress?"
        )

        # If user expresses stress/overwhelm, trigger intervention
        sentiment = intent.get('sentiment', 'neutral')
        if sentiment in ['negative', 'stressed']:
            response_text += " I noticed you might be feeling overwhelmed. Let me help lighten your load."

        return {
            "intent": "daily_checkin",
            "action_taken": {
                "completed_count": completed_count,
                "sentiment": sentiment,
            },
            "response_text": response_text,
            "success": True
        }


# Singleton instance
voice_processor = VoiceProcessor()
