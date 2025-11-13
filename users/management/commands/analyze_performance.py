"""
Management command to analyze user performance patterns.

Run nightly via cron:
    0 2 * * * cd /path/to/backend && ./venv/bin/python manage.py analyze_performance

This updates UserProfile.performance_insights for all active users.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from ai.performance_analyzer import performance_analyzer

User = get_user_model()


class Command(BaseCommand):
    help = 'Analyze user performance patterns and update profiles'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='Analyze specific user by ID (default: all users)',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Print detailed analysis results',
        )

    def handle(self, *args, **options):
        user_id = options.get('user_id')
        verbose = options.get('verbose')

        if user_id:
            users = User.objects.filter(id=user_id)
        else:
            # Only analyze active users (logged in within last 7 days)
            cutoff = timezone.now() - timezone.timedelta(days=7)
            users = User.objects.filter(last_login__gte=cutoff)

        self.stdout.write(f"Analyzing {users.count()} users...")

        analyzed_count = 0
        skipped_count = 0

        for user in users:
            try:
                # Analyze performance
                analysis = performance_analyzer.analyze_user_performance(user)

                # Skip if insufficient data
                if analysis.get("tasks_analyzed", 0) < 5:
                    skipped_count += 1
                    if verbose:
                        self.stdout.write(f"  ⏭️  {user.email}: Insufficient data ({analysis.get('tasks_analyzed', 0)} tasks)")
                    continue

                # Update user profile with insights
                profile = user.profile
                profile.performance_insights = analysis
                profile.last_performance_analysis = timezone.now()
                profile.save(update_fields=['performance_insights', 'last_performance_analysis'])

                analyzed_count += 1

                # Check if Plan-B intervention needed
                should_intervene, reason = performance_analyzer.should_trigger_planb_intervention(user)

                if verbose or should_intervene:
                    risk_emoji = {
                        "low": "✅",
                        "medium": "⚠️",
                        "high": "🔴",
                        "critical": "🚨"
                    }.get(analysis["risk_level"], "❓")

                    self.stdout.write(
                        f"  {risk_emoji} {user.email}: "
                        f"Rate={int(analysis['completion_rate']*100)}% | "
                        f"Risk={analysis['risk_level']} | "
                        f"Tasks={analysis['tasks_analyzed']}"
                    )

                    if should_intervene:
                        self.stdout.write(f"      🔔 INTERVENTION NEEDED: {reason}")

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"  ❌ {user.email}: Error - {str(e)}")
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"\n✅ Analysis complete: {analyzed_count} analyzed, {skipped_count} skipped"
            )
        )
