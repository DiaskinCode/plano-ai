"""
Management command to send proactive coach notifications.

Run multiple times per day via cron:
- 8:00 AM: Morning motivation
- 8:00 PM: Evening check-in
- 2:00 AM: Analyze and send intervention alerts

Usage:
    python manage.py send_proactive_notifications --mode morning
    python manage.py send_proactive_notifications --mode evening
    python manage.py send_proactive_notifications --mode intervention
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta

from ai.proactive_coach import proactive_coach
from ai.adaptive_coach import adaptive_coach
from ai.performance_analyzer import performance_analyzer
from todos.models import Todo

User = get_user_model()


class Command(BaseCommand):
    help = 'Send proactive coach notifications'

    def add_arguments(self, parser):
        parser.add_argument(
            '--mode',
            type=str,
            choices=['morning', 'evening', 'intervention', 'all'],
            default='all',
            help='Which notifications to send',
        )
        parser.add_argument(
            '--user-id',
            type=int,
            help='Send to specific user only (for testing)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print what would be sent without actually sending',
        )

    def handle(self, *args, **options):
        mode = options['mode']
        user_id = options.get('user_id')
        dry_run = options.get('dry_run', False)

        # Get active users
        if user_id:
            users = User.objects.filter(id=user_id)
        else:
            # Only users active in last 7 days
            cutoff = timezone.now() - timedelta(days=7)
            users = User.objects.filter(
                last_login__gte=cutoff,
                push_enabled=True,
                push_token__isnull=False
            )

        self.stdout.write(f"Processing {users.count()} users (mode: {mode})...")

        sent_count = 0
        skipped_count = 0

        for user in users:
            try:
                if mode in ['morning', 'all']:
                    sent = self._send_morning_notification(user, dry_run)
                    if sent:
                        sent_count += 1
                    else:
                        skipped_count += 1

                if mode in ['evening', 'all']:
                    sent = self._send_evening_notification(user, dry_run)
                    if sent:
                        sent_count += 1
                    else:
                        skipped_count += 1

                if mode in ['intervention', 'all']:
                    sent = self._send_intervention_notification(user, dry_run)
                    if sent:
                        sent_count += 1
                    else:
                        skipped_count += 1

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"  ❌ Error for {user.email}: {str(e)}")
                )

        status_msg = "[DRY RUN] " if dry_run else ""
        self.stdout.write(
            self.style.SUCCESS(
                f"\n{status_msg}✅ Sent: {sent_count} | Skipped: {skipped_count}"
            )
        )

    def _send_morning_notification(self, user, dry_run: bool) -> bool:
        """Send morning motivation notification."""
        # Get today's tasks
        today = timezone.now().date()
        daily_tasks = Todo.objects.filter(
            user=user,
            scheduled_date=today,
            status__in=['ready', 'in_progress']
        )

        if not daily_tasks.exists():
            return False  # No tasks today

        # Check user's energy peak
        profile = user.profile
        energy_peak = getattr(profile, 'energy_peak', 'morning')

        # Only send to morning/afternoon people
        if energy_peak not in ['morning', 'afternoon']:
            return False

        if dry_run:
            self.stdout.write(
                f"  [DRY RUN] Would send morning notification to {user.email} "
                f"({daily_tasks.count()} tasks)"
            )
            return True

        ticket_id = proactive_coach.send_morning_motivation(user, list(daily_tasks))

        if ticket_id:
            self.stdout.write(f"  ☀️ Morning notification sent to {user.email}")
            return True
        else:
            return False

    def _send_evening_notification(self, user, dry_run: bool) -> bool:
        """Send evening check-in notification."""
        # Get today's completion summary
        today = timezone.now().date()
        daily_tasks = Todo.objects.filter(
            user=user,
            scheduled_date=today
        )

        if not daily_tasks.exists():
            return False

        completed = daily_tasks.filter(status='done').count()
        total = daily_tasks.count()

        completion_summary = {
            'completed': completed,
            'total': total,
            'rate': completed / total if total > 0 else 0
        }

        # Check user's energy peak
        profile = user.profile
        energy_peak = getattr(profile, 'energy_peak', 'morning')

        # Only send to evening/night people (or if completion rate < 50%)
        if energy_peak not in ['evening', 'night'] and completion_summary['rate'] >= 0.5:
            return False

        if dry_run:
            self.stdout.write(
                f"  [DRY RUN] Would send evening check-in to {user.email} "
                f"({completed}/{total} tasks)"
            )
            return True

        ticket_id = proactive_coach.send_evening_checkin(user, completion_summary)

        if ticket_id:
            self.stdout.write(f"  🌙 Evening check-in sent to {user.email}")
            return True
        else:
            return False

    def _send_intervention_notification(self, user, dry_run: bool) -> bool:
        """Check if intervention needed and send notification."""
        # Check if intervention already checked recently
        profile = user.profile
        if profile.last_intervention_at:
            hours_since = (timezone.now() - profile.last_intervention_at).total_seconds() / 3600
            if hours_since < 72:  # 3 days cooldown
                return False

        # Check if intervention needed
        intervention = adaptive_coach.check_and_intervene(user)

        if not intervention:
            return False  # User is on track

        if dry_run:
            self.stdout.write(
                f"  [DRY RUN] Would send intervention alert to {user.email} "
                f"(type: {intervention['type']}, severity: {intervention['severity']})"
            )
            return True

        ticket_id = proactive_coach.send_intervention_alert(user, intervention)

        if ticket_id:
            severity_emoji = {
                'low': '💡',
                'medium': '⚠️',
                'high': '🔴',
                'critical': '🚨'
            }.get(intervention['severity'], '💡')

            self.stdout.write(
                f"  {severity_emoji} Intervention alert sent to {user.email} "
                f"({intervention['type']})"
            )
            return True
        else:
            return False
