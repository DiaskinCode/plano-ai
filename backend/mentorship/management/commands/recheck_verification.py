"""
Django management command to recheck and sync verification status.

This command ensures that is_verified field stays in sync with verification_status.

Usage:
    python manage.py recheck_verification
"""

from django.core.management.base import BaseCommand
from django.db import models
from mentorship.models import MentorProfile


class Command(BaseCommand):
    help = 'Recheck and sync verification status with is_verified field'

    def handle(self, *args, **options):
        # Sync is_verified with verification_status
        approved_count = MentorProfile.objects.filter(
            verification_status='approved'
        ).update(is_verified=True)

        not_approved_count = MentorProfile.objects.exclude(
            verification_status='approved'
        ).update(is_verified=False)

        self.stdout.write(
            self.style.SUCCESS(
                f'Updated {approved_count} as verified, '
                f'{not_approved_count} as not verified'
            )
        )

        # Show verification status breakdown
        self.stdout.write('\nVerification Status Breakdown:')
        for status, _ in MentorProfile.VERIFICATION_STATUS_CHOICES:
            count = MentorProfile.objects.filter(verification_status=status).count()
            color = self.style.SUCCESS if status == 'approved' else self.style.WARNING
            self.stdout.write(f'  {status}: {count}', color)

        # Show flag statistics
        total_flags = MentorProfile.objects.aggregate(total=models.Sum('flag_count'))['total'] or 0
        self.stdout.write(f'\nTotal flags across all mentors: {total_flags}')

        flagged_mentors = MentorProfile.objects.filter(flag_count__gt=0).count()
        self.stdout.write(f'Mentors with flags: {flagged_mentors}')

        suspended_mentors = MentorProfile.objects.filter(verification_status='suspended').count()
        if suspended_mentors > 0:
            self.stdout.write(
                self.style.ERROR(f'Suspended mentors: {suspended_mentors}')
            )
