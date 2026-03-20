from django.core.management.base import BaseCommand
from onboarding.models import SubscriptionPlan


class Command(BaseCommand):
    help = "Create default subscription plans (Basic, Pro, Premium)"

    def handle(self, *args, **options):
        plans = [
            {
                "name": "basic",
                "display_name": "Basic",
                "price_monthly": 25,
                "price_yearly": 250,
                "monthly_video_calls": 0,
                "monthly_text_questions": 10,
                "monthly_mentor_bookings": 0,  # Cannot book mentors
                "dedicated_mentor": False,
                "is_popular": False,
                "is_active": True,
                "order": 1,
                "features": [
                    "10 text questions per month",
                    "Basic task management",
                    "Progress tracking",
                ],
            },
            {
                "name": "pro",
                "display_name": "Pro",
                "price_monthly": 100,
                "price_yearly": 1000,
                "monthly_video_calls": 2,
                "monthly_text_questions": 50,
                "monthly_mentor_bookings": 2,  # Can book 2 mentor sessions/month
                "dedicated_mentor": False,
                "is_popular": True,
                "is_active": True,
                "order": 2,
                "features": [
                    "2 video calls per month",
                    "50 text questions per month",
                    "2 mentor bookings per month",
                    "AI-generated roadmaps",
                    "Priority support",
                ],
            },
            {
                "name": "premium",
                "display_name": "Premium",
                "price_monthly": 200,
                "price_yearly": 2000,
                "monthly_video_calls": 5,
                "monthly_text_questions": 100,
                "monthly_mentor_bookings": 6,  # Can book 6 mentor sessions/month
                "dedicated_mentor": True,
                "is_popular": False,
                "is_active": True,
                "order": 3,
                "features": [
                    "5 video calls per month",
                    "100 text questions per month",
                    "6 mentor bookings per month",
                    "Dedicated mentor",
                    "Priority support",
                    "Advanced analytics",
                ],
            },
        ]

        created = 0
        for plan_data in plans:
            plan, created_flag = SubscriptionPlan.objects.get_or_create(
                name=plan_data["name"], defaults=plan_data
            )
            if created_flag:
                created += 1
                self.stdout.write(f"✓ Created plan: {plan.display_name}")
            else:
                self.stdout.write(f"  Plan already exists: {plan.display_name}")

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully created {created} subscription plans"
            )
        )
