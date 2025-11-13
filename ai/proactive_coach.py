"""
Proactive Coach Notification System

Sends intelligent, timely push notifications to keep users engaged.

Notification types:
1. Intervention alerts ("I noticed you're falling behind...")
2. Morning motivation ("Ready to crush 3 quick wins today?")
3. Evening check-ins ("How did today go? 2/5 tasks completed")
4. Milestone celebrations ("🎉 You completed 10 tasks this week!")
5. Course corrections ("Task overdue 7 days - let's re-scope?")

This makes PathAI feel like a real coach, not just a todo list.
"""

import os
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from django.utils import timezone
from exponent_server_sdk import (
    DeviceNotRegisteredError,
    PushClient,
    PushMessage,
    PushServerError,
    PushTicketError,
)


class ProactiveCoach:
    """
    Intelligent push notification system for adaptive coaching.

    Sends context-aware notifications at optimal times.
    """

    def __init__(self):
        self.push_client = PushClient()

    def should_send_notification(self, user, notification_type: str) -> bool:
        """
        Check if notification should be sent based on:
        - User's notification preferences
        - Quiet hours
        - Notification frequency limits
        """
        # Check if user has push token
        if not user.push_token or not user.push_enabled:
            return False

        # Check notification preferences
        try:
            prefs = user.notification_preferences
        except:
            return True  # Default to enabled if no preferences set

        # Check notification type preferences
        if notification_type == 'intervention' and not prefs.ai_motivation_enabled:
            return False
        elif notification_type == 'daily_pulse' and not prefs.daily_pulse_reminder_enabled:
            return False
        elif notification_type == 'task_reminder' and not prefs.task_reminders_enabled:
            return False

        # Check quiet hours
        if prefs.is_quiet_hours():
            return False

        return True

    def send_intervention_alert(self, user, intervention: Dict) -> Optional[str]:
        """
        Send push notification about Plan-B intervention.

        Notification examples:
        - "⚠️ I noticed your completion rate dropped to 45%. Let's adjust your plan."
        - "🚧 You have 3 tasks blocked for 2+ weeks. Time to re-scope?"
        """
        if not self.should_send_notification(user, 'intervention'):
            return None

        severity = intervention.get('severity', 'medium')
        intervention_type = intervention.get('type', 'unknown')

        # Craft notification based on severity
        if severity == 'critical':
            title = "⚠️ Let's reset your plan"
            body = "Your completion rate dropped significantly. I have a Plan-B ready for you."
        elif severity == 'high':
            title = "🎯 Time to simplify"
            body = "You're falling behind. Let's focus on just 3 critical tasks this week."
        else:
            title = "💡 I have a suggestion"
            body = intervention.get('title', 'Check your adaptive coaching recommendations')

        return self._send_push_notification(
            user,
            title=title,
            body=body,
            data={
                'type': 'intervention',
                'intervention_type': intervention_type,
                'severity': severity,
                'screen': 'CoachIntervention',
            }
        )

    def send_morning_motivation(self, user, daily_tasks: List) -> Optional[str]:
        """
        Send morning motivational push notification.

        Examples:
        - "☀️ Good morning! Ready to crush 3 quick wins today?"
        - "🔥 You're on a 5-day streak! Let's make it 6."
        - "💪 Today's focus: Complete your SOP draft (1 hour)"
        """
        if not self.should_send_notification(user, 'daily_pulse'):
            return None

        # Get user's energy peak time
        profile = user.profile
        energy_peak = profile.energy_peak if hasattr(profile, 'energy_peak') else 'morning'

        # Don't send morning notification if user is evening person
        if energy_peak == 'evening' or energy_peak == 'night':
            return None

        # Count quick wins
        quick_wins = [t for t in daily_tasks if getattr(t, 'is_quick_win', False)]
        high_priority = [t for t in daily_tasks if t.priority == 3]

        # Craft personalized message
        if user.current_streak >= 3:
            title = f"🔥 {user.current_streak}-day streak!"
            body = f"Keep it going! {len(daily_tasks)} tasks scheduled today."
        elif len(quick_wins) >= 2:
            title = "☀️ Good morning!"
            body = f"Ready to crush {len(quick_wins)} quick wins today?"
        elif len(high_priority) >= 1:
            title = "💪 Focus mode"
            body = f"Today's priority: {high_priority[0].title[:50]}"
        else:
            title = "☀️ Good morning!"
            body = f"{len(daily_tasks)} tasks scheduled today. Let's make progress!"

        return self._send_push_notification(
            user,
            title=title,
            body=body,
            data={
                'type': 'morning_motivation',
                'screen': 'Home',
                'tasks_count': len(daily_tasks),
            }
        )

    def send_evening_checkin(self, user, completion_summary: Dict) -> Optional[str]:
        """
        Send evening check-in notification.

        Examples:
        - "✅ Great job! 4/5 tasks completed today."
        - "📊 How did today go? 2/5 tasks done. Let's review."
        - "🎉 Perfect day! All tasks completed."
        """
        if not self.should_send_notification(user, 'daily_pulse'):
            return None

        completed = completion_summary.get('completed', 0)
        total = completion_summary.get('total', 0)

        if total == 0:
            return None  # No tasks scheduled today

        completion_rate = completed / total if total > 0 else 0

        # Craft message based on performance
        if completion_rate == 1.0:
            title = "🎉 Perfect day!"
            body = f"All {completed} tasks completed. You're crushing it!"
        elif completion_rate >= 0.75:
            title = "✅ Great job!"
            body = f"{completed}/{total} tasks completed today."
        elif completion_rate >= 0.5:
            title = "📊 Solid progress"
            body = f"{completed}/{total} tasks done. How did today go?"
        else:
            title = "📊 End of day check-in"
            body = f"{completed}/{total} tasks completed. Let's review together."

        return self._send_push_notification(
            user,
            title=title,
            body=body,
            data={
                'type': 'evening_checkin',
                'screen': 'DailyPulse',
                'completed': completed,
                'total': total,
            }
        )

    def send_milestone_celebration(self, user, milestone: Dict) -> Optional[str]:
        """
        Celebrate achievements.

        Examples:
        - "🎉 10 tasks completed this week!"
        - "🏆 You hit your first 7-day streak!"
        - "⭐ Goal completed: Get into Imperial College"
        """
        if not self.should_send_notification(user, 'intervention'):
            return None

        milestone_type = milestone.get('type')

        if milestone_type == 'weekly_tasks':
            count = milestone.get('count', 0)
            title = "🎉 Weekly milestone!"
            body = f"{count} tasks completed this week. Keep it up!"
        elif milestone_type == 'streak':
            days = milestone.get('days', 0)
            title = f"🔥 {days}-day streak!"
            body = "You're building momentum. Don't break it!"
        elif milestone_type == 'goal_completed':
            goal_title = milestone.get('goal_title', 'Goal')
            title = "🏆 Goal completed!"
            body = f"Congrats on completing: {goal_title}"
        else:
            title = "⭐ Achievement unlocked!"
            body = milestone.get('message', 'Great progress!')

        return self._send_push_notification(
            user,
            title=title,
            body=body,
            data={
                'type': 'milestone',
                'milestone_type': milestone_type,
                'screen': 'Profile',
            }
        )

    def send_course_correction(self, user, task) -> Optional[str]:
        """
        Notify about tasks needing attention.

        Examples:
        - "⏰ Task overdue 7 days: Write SOP. Let's re-scope?"
        - "🚧 Still blocked: Connect with alumni. Need help?"
        """
        if not self.should_send_notification(user, 'task_reminder'):
            return None

        if task.is_overdue and task.days_overdue >= 7:
            title = "⏰ Task needs attention"
            body = f"Overdue {task.days_overdue} days: {task.title[:50]}. Let's re-scope?"
        elif task.status == 'blocked':
            title = "🚧 Still blocked"
            body = f"{task.title[:50]}. Need help breaking it down?"
        else:
            return None

        return self._send_push_notification(
            user,
            title=title,
            body=body,
            data={
                'type': 'course_correction',
                'task_id': task.id,
                'screen': 'TaskDetail',
            }
        )

    def send_task_reminder(self, user, task, minutes_before: int = 15) -> Optional[str]:
        """
        Send reminder before scheduled task.

        Examples:
        - "⏰ Starting in 15 min: Write SOP draft"
        - "📝 Reminder: Review IELTS practice test (2:00 PM)"
        """
        if not self.should_send_notification(user, 'task_reminder'):
            return None

        # Check if task has scheduled time
        if not task.scheduled_time:
            return None

        title = f"⏰ Starting in {minutes_before} min"
        body = f"{task.title[:70]}"

        return self._send_push_notification(
            user,
            title=title,
            body=body,
            data={
                'type': 'task_reminder',
                'task_id': task.id,
                'screen': 'TaskDetail',
            }
        )

    def _send_push_notification(
        self,
        user,
        title: str,
        body: str,
        data: Dict = None
    ) -> Optional[str]:
        """
        Send push notification via Expo.

        Returns:
            Ticket ID if successful, None otherwise
        """
        if not user.push_token:
            return None

        try:
            message = PushMessage(
                to=user.push_token,
                title=title,
                body=body,
                data=data or {},
                sound='default',
                badge=1,
                priority='high',
            )

            response = self.push_client.publish(message)

            # Check for errors
            if response.status == 'error':
                print(f"Push notification error: {response.message}")
                return None

            return response.id

        except DeviceNotRegisteredError:
            # Token is invalid, clear it
            user.push_token = None
            user.save(update_fields=['push_token'])
            print(f"Cleared invalid push token for user {user.email}")
            return None

        except Exception as e:
            print(f"Error sending push notification: {e}")
            return None

    def send_bulk_notifications(self, users_with_messages: List[tuple]) -> Dict:
        """
        Send multiple notifications efficiently.

        Args:
            users_with_messages: [(user, title, body, data), ...]

        Returns:
            {
                "sent": 10,
                "failed": 2,
                "ticket_ids": [...]
            }
        """
        messages = []

        for user, title, body, data in users_with_messages:
            if not user.push_token:
                continue

            messages.append(PushMessage(
                to=user.push_token,
                title=title,
                body=body,
                data=data or {},
                sound='default',
                badge=1,
                priority='high',
            ))

        if not messages:
            return {"sent": 0, "failed": 0, "ticket_ids": []}

        try:
            responses = self.push_client.publish_multiple(messages)

            sent = sum(1 for r in responses if r.status != 'error')
            failed = len(responses) - sent
            ticket_ids = [r.id for r in responses if r.status != 'error']

            return {
                "sent": sent,
                "failed": failed,
                "ticket_ids": ticket_ids,
            }

        except Exception as e:
            print(f"Error sending bulk notifications: {e}")
            return {"sent": 0, "failed": len(messages), "ticket_ids": []}


# Singleton instance
proactive_coach = ProactiveCoach()
