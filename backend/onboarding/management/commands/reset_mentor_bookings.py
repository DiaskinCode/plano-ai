"""
Django management command to reset monthly mentor booking counts for all active subscriptions.

Usage:
    python manage.py reset_mentor_bookings
    python manage.py reset_mentor_bookings --user-id 123
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from onboarding.models import UserSubscription


class Command(BaseCommand):
    help = 'Reset monthly mentor booking counts for subscriptions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='Reset bookings for a specific user only',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be reset without actually resetting',
        )

    def handle(self, *args, **options):
        user_id = options.get('user_id')
        dry_run = options.get('dry_run', False)

        # Get subscriptions
        if user_id:
            subscriptions = UserSubscription.objects.filter(
                user_id=user_id,
                status__in=['active', 'trial']
            )
            self.stdout.write(f"Found {subscriptions.count()} subscription(s) for user {user_id}")
        else:
            subscriptions = UserSubscription.objects.filter(
                status__in=['active', 'trial']
            )
            self.stdout.write(f"Found {subscriptions.count()} active subscriptions")

        reset_count = 0
        for subscription in subscriptions:
            plan = subscription.plan
            current = subscription.remaining_mentor_bookings
            new_limit = plan.monthly_mentor_bookings

            if dry_run:
                self.stdout.write(
                    f"  Would reset: {subscription.user.email} - "
                    f"{current} → {new_limit} ({plan.display_name})"
                )
            else:
                subscription.reset_monthly_mentor_bookings()
                reset_count += 1
                self.stdout.write(
                    f"  Reset: {subscription.user.email} - "
                    f"{current} → {new_limit} ({plan.display_name})"
                )

        if dry_run:
            self.stdout.write(self.style.WARNING(f"\nDry run complete. No changes made."))
        else:
            self.stdout.write(self.style.SUCCESS(f"\nReset {reset_count} subscription(s)"))
