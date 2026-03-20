"""
Django management command to auto-verify existing mentor profiles.

This command is useful for:
- Initial migration of existing mentors
- Testing the verification system
- Emergency bulk verification

Usage:
    python manage.py auto_verify_mentors
    python manage.py auto_verify_mentors --dry-run
    python manage.py auto_verify_mentors --user-id 123
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from mentorship.models import MentorProfile


class Command(BaseCommand):
    help = 'Auto-verify existing mentor profiles (with optional dry-run)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='Verify a specific mentor only',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be verified without making changes',
        )

    def handle(self, *args, **options):
        user_id = options.get('user_id')
        dry_run = options.get('dry_run', False)

        # Get mentors to verify (pending status only, or all if specified)
        if user_id:
            mentors = MentorProfile.objects.filter(
                user_id=user_id,
                verification_status='pending'
            )
            self.stdout.write(f"Found {mentors.count()} pending mentor(s) for user {user_id}")
        else:
            mentors = MentorProfile.objects.filter(
                verification_status='pending'
            )
            self.stdout.write(f"Found {mentors.count()} pending mentor(s)")

        if dry_run:
            self.stdout.write("\nDRY RUN - No changes will be made:")
            for mentor in mentors:
                self.stdout.write(f"  - {mentor.title} ({mentor.user.email})")
            self.stdout.write(f"\nWould verify {mentors.count()} mentor(s)")
            return

        # Verify mentors
        updated = mentors.update(
            verification_status='approved',
            verification_reviewed_at=timezone.now(),
            is_verified=True
        )

        self.stdout.write(
            self.style.SUCCESS(f'Successfully verified {updated} mentor(s)')
        )

        # Show verification status breakdown
        self.stdout.write('\nVerification Status Breakdown:')
        for status, _ in MentorProfile.VERIFICATION_STATUS_CHOICES:
            count = MentorProfile.objects.filter(verification_status=status).count()
            self.stdout.write(f'  {status}: {count}')
