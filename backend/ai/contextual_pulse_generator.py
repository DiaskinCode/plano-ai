"""
Context-Aware Daily Pulse Generator

Generates personalized daily briefs using:
- Performance insights (from PerformanceAnalyzer)
- Recent intervention history
- User's optimal schedule patterns
- Task completion trends

This makes Daily Pulse feel intelligent, not generic.
"""

import os
from anthropic import Anthropic
from django.utils import timezone
from datetime import datetime, timedelta
from typing import Dict, List


class ContextualPulseGenerator:
    """
    Generates AI-powered daily briefings with full context awareness.
    """

    def __init__(self):
        self.anthropic = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        self.model = "claude-3-5-sonnet-20241022"

    def generate_contextual_pulse(self, user, daily_tasks: List) -> Dict:
        """
        Generate context-aware Daily Pulse.

        Returns:
            {
                "greeting_message": "☀️ Good morning! Let's make today count.",
                "top_priorities": [
                    {"task_id": 123, "title": "...", "reason": "High impact for your goal"},
                    ...
                ],
                "workload_assessment": {
                    "percentage": 85,
                    "status": "manageable",
                    "message": "You have 4 hours of work scheduled"
                },
                "warnings": [
                    "⚠️ Task overdue 7 days: Write SOP. Let's re-scope?"
                ],
                "smart_suggestions": [
                    "💡 Your peak productivity is 9-11am. Schedule SOP draft then."
                ],
                "coaching_note": "Based on last week's patterns, you excel at morning tasks...",
                "full_message": "Comprehensive daily briefing..."
            }
        """
        profile = user.profile

        # Get performance insights
        performance = profile.performance_insights if profile.performance_insights else {}

        # Get intervention history
        recent_interventions = self._get_recent_interventions(profile)

        # Build context for AI
        context = self._build_pulse_context(
            user=user,
            profile=profile,
            daily_tasks=daily_tasks,
            performance=performance,
            recent_interventions=recent_interventions
        )

        # Generate AI-powered pulse
        ai_pulse = self._generate_ai_pulse(context)

        # Structure response
        return self._structure_pulse_response(ai_pulse, daily_tasks, performance)

    def _get_recent_interventions(self, profile) -> List[Dict]:
        """Get last 3 interventions."""
        history = profile.intervention_history if profile.intervention_history else []
        return sorted(history, key=lambda x: x.get('date', ''), reverse=True)[:3]

    def _build_pulse_context(
        self,
        user,
        profile,
        daily_tasks: List,
        performance: Dict,
        recent_interventions: List[Dict]
    ) -> str:
        """Build comprehensive context for AI."""
        today = timezone.now().date()

        context_parts = []

        # User info
        context_parts.append(f"USER: {profile.name}")
        context_parts.append(f"Current Streak: {user.current_streak} days")
        context_parts.append(f"Energy Peak: {profile.energy_peak}")
        context_parts.append(f"Coach Character: {profile.coach_character}")

        # Performance insights
        if performance:
            context_parts.append("\nPERFORMANCE (Last 30 days):")
            context_parts.append(f"- Completion Rate: {int(performance.get('completion_rate', 0) * 100)}%")
            context_parts.append(f"- Risk Level: {performance.get('risk_level', 'unknown')}")

            optimal_schedule = performance.get('optimal_schedule', {})
            if optimal_schedule.get('high_energy_hours'):
                hours_str = ', '.join([f"{h}:00" for h in optimal_schedule['high_energy_hours'][:3]])
                context_parts.append(f"- Peak Hours: {hours_str}")

            if performance.get('strengths'):
                context_parts.append(f"- Strengths: {'; '.join(performance['strengths'][:2])}")

            if performance.get('warnings'):
                context_parts.append(f"- Warnings: {'; '.join(performance['warnings'][:2])}")

        # Recent interventions
        if recent_interventions:
            context_parts.append("\nRECENT INTERVENTIONS:")
            for intervention in recent_interventions[:2]:
                accepted = intervention.get('accepted', False)
                status_emoji = "✅" if accepted else "❌"
                context_parts.append(
                    f"{status_emoji} {intervention.get('type', 'unknown')} "
                    f"({intervention.get('severity', 'medium')})"
                )

        # Today's tasks
        context_parts.append(f"\nTODAY'S TASKS ({len(daily_tasks)} total):")

        high_priority = [t for t in daily_tasks if t.priority == 3]
        quick_wins = [t for t in daily_tasks if getattr(t, 'is_quick_win', False)]
        overdue_tasks = [t for t in daily_tasks if t.is_overdue]

        context_parts.append(f"- High Priority: {len(high_priority)}")
        context_parts.append(f"- Quick Wins: {len(quick_wins)}")
        context_parts.append(f"- Overdue: {len(overdue_tasks)}")

        # Task details
        context_parts.append("\nTop 5 Tasks:")
        for i, task in enumerate(daily_tasks[:5], 1):
            overdue_marker = f" [OVERDUE {task.days_overdue}d]" if task.is_overdue else ""
            quick_win_marker = " [QUICK WIN]" if getattr(task, 'is_quick_win', False) else ""
            context_parts.append(
                f"{i}. [{task.get_priority_display()}] {task.title} "
                f"({task.timebox_minutes}min){overdue_marker}{quick_win_marker}"
            )

        return "\n".join(context_parts)

    def _generate_ai_pulse(self, context: str) -> Dict:
        """Use Claude to generate personalized pulse."""

        prompt = f"""You are PathAI's adaptive coach. Generate a personalized Daily Pulse briefing for this user.

CONTEXT:
{context}

GENERATE:
1. **Greeting Message** (1 sentence, warm and personal, match coach character)
   - If supportive: Encouraging and gentle
   - If aggressive: Tough love, call out slacking
   - If cute: Playful and cheerful
   - If professional: Clear and focused

2. **Top 3 Priorities** (explain WHY each task matters)
   - Reference user's goals
   - Use performance insights to guide priorities
   - Prioritize: Overdue tasks > High priority > Quick wins

3. **Workload Assessment** (realistic evaluation)
   - Is today's schedule achievable?
   - Too much? Suggest pausing low-priority tasks
   - Too light? Suggest adding tasks

4. **Warnings** (if any critical issues)
   - Overdue tasks > 7 days
   - Completion rate dropping
   - Blocked tasks piling up

5. **Smart Suggestions** (actionable tips)
   - Schedule tasks during peak hours
   - Break down overwhelming tasks
   - Leverage strengths from performance data

6. **Coaching Note** (2-3 sentences, personal insight)
   - Reference patterns from performance data
   - Acknowledge recent wins
   - Motivate based on user's goal progress

RESPONSE FORMAT (JSON):
{{
    "greeting": "☀️ Good morning! ...",
    "priorities": [
        {{
            "task_index": 0,
            "reason": "High impact for your Cambridge application"
        }},
        {{
            "task_index": 1,
            "reason": "Quick win to build momentum"
        }},
        {{
            "task_index": 2,
            "reason": "Overdue 7 days - needs immediate attention"
        }}
    ],
    "workload": {{
        "status": "manageable" | "challenging" | "light" | "overwhelming",
        "message": "You have 4 hours of work scheduled - achievable!"
    }},
    "warnings": [
        "⚠️ Task overdue 7 days: Write SOP. Let's re-scope?"
    ],
    "suggestions": [
        "💡 Your peak productivity is 9-11am. Schedule SOP draft then.",
        "🎯 You excel at quick wins - knock out 2 this morning."
    ],
    "coaching_note": "Based on last week's patterns, you're strongest in the morning with quick wins. Let's use that to build momentum today and tackle the overdue SOP task."
}}

IMPORTANT:
- Be concise and actionable
- Reference specific user data (peak hours, strengths, streak)
- Match the coach character tone
- Don't be generic - use context!
"""

        try:
            response = self.anthropic.messages.create(
                model=self.model,
                max_tokens=1500,
                temperature=0.7,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            import json
            ai_response = response.content[0].text

            # Extract JSON
            if "```json" in ai_response:
                ai_response = ai_response.split("```json")[1].split("```")[0].strip()
            elif "```" in ai_response:
                ai_response = ai_response.split("```")[1].split("```")[0].strip()

            return json.loads(ai_response)

        except Exception as e:
            print(f"Error generating AI pulse: {e}")
            return self._fallback_pulse()

    def _fallback_pulse(self) -> Dict:
        """Fallback if AI fails."""
        return {
            "greeting": "☀️ Good morning! Let's make today count.",
            "priorities": [],
            "workload": {
                "status": "manageable",
                "message": "You have tasks scheduled for today"
            },
            "warnings": [],
            "suggestions": [],
            "coaching_note": "Focus on your top priorities and make steady progress."
        }

    def _structure_pulse_response(
        self,
        ai_pulse: Dict,
        daily_tasks: List,
        performance: Dict
    ) -> Dict:
        """Structure the AI response into final format."""

        # Map priority indices to actual tasks
        top_priorities = []
        for priority in ai_pulse.get('priorities', [])[:3]:
            task_index = priority.get('task_index', 0)
            if task_index < len(daily_tasks):
                task = daily_tasks[task_index]
                top_priorities.append({
                    "task_id": task.id,
                    "title": task.title,
                    "reason": priority.get('reason', 'Important task'),
                    "timebox_minutes": task.timebox_minutes,
                    "priority": task.priority,
                })

        # Calculate workload
        total_minutes = sum(t.timebox_minutes or 0 for t in daily_tasks)
        workload_info = ai_pulse.get('workload', {})

        # Build full message
        full_message_parts = [
            ai_pulse.get('greeting', ''),
            '',
            "🎯 **Top Priorities:**",
        ]

        for i, priority in enumerate(top_priorities, 1):
            full_message_parts.append(f"{i}. {priority['title']} - {priority['reason']}")

        full_message_parts.append('')
        full_message_parts.append(f"⏱️ **Workload:** {workload_info.get('message', '')}")

        if ai_pulse.get('warnings'):
            full_message_parts.append('')
            full_message_parts.append("⚠️ **Warnings:**")
            for warning in ai_pulse['warnings']:
                full_message_parts.append(f"- {warning}")

        if ai_pulse.get('suggestions'):
            full_message_parts.append('')
            full_message_parts.append("💡 **Smart Suggestions:**")
            for suggestion in ai_pulse['suggestions']:
                full_message_parts.append(f"- {suggestion}")

        full_message_parts.append('')
        full_message_parts.append(f"🎓 **Coach's Note:** {ai_pulse.get('coaching_note', '')}")

        return {
            "greeting_message": ai_pulse.get('greeting', ''),
            "top_priorities": top_priorities,
            "workload_assessment": {
                "percentage": min(100, int((total_minutes / 480) * 100)),  # 480 = 8 hours
                "status": workload_info.get('status', 'manageable'),
                "message": workload_info.get('message', ''),
                "total_minutes": total_minutes,
            },
            "warnings": ai_pulse.get('warnings', []),
            "smart_suggestions": ai_pulse.get('suggestions', []),
            "coaching_note": ai_pulse.get('coaching_note', ''),
            "full_message": "\n".join(full_message_parts),
            "generated_at": timezone.now().isoformat(),
        }


# Singleton instance
contextual_pulse_generator = ContextualPulseGenerator()
