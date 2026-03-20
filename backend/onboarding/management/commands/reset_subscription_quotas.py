from django.core.management.base import BaseCommand
from onboarding.models import UserSubscription


class Command(BaseCommand):
    help = "Reset monthly quotas for user subscriptions to match plan limits"

    def add_arguments(self, parser):
        parser.add_argument(
            "--email",
            type=str,
            help="Reset quota for specific user email",
        )
        parser.add_argument(
            "--all",
            action="store_true",
            help="Reset quotas for all users",
        )

    def handle(self, *args, **options):
        email = options.get("email")
        reset_all = options.get("all")

        if reset_all:
            subscriptions = UserSubscription.objects.all()
        elif email:
            subscriptions = UserSubscription.objects.filter(user__email=email)
        else:
            self.stdout.write(
                self.style.ERROR("Please specify --email or --all")
            )
            return

        count = 0
        for sub in subscriptions:
            # Reset quotas to plan limits
            sub.remaining_mentor_bookings = sub.plan.monthly_mentor_bookings
            sub.remaining_video_calls = sub.plan.monthly_video_calls
            sub.remaining_text_questions = sub.plan.monthly_text_questions
            sub.save()
            count += 1
            self.stdout.write(
                f"✓ Reset {sub.user.email} - {sub.plan.display_name}"
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully reset quotas for {count} subscription(s)"
            )
        )
