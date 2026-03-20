# Generated migration for mentor verification system

from django.db import migrations, models
from django.utils import timezone


def auto_verify_existing_mentors(apps, schema_editor):
    """Auto-verify mentors with existing profiles"""
    MentorProfile = apps.get_model('mentorship', 'MentorProfile')

    # Set all existing mentors to approved with reviewed timestamp
    # This ensures existing mentors remain active after migration
    MentorProfile.objects.all().update(
        verification_status='approved',
        verification_reviewed_at=timezone.now(),
        is_verified=True
    )


class Migration(migrations.Migration):

    dependencies = [
        ('mentorship', '0001_initial'),
    ]

    operations = [
        # Add verification fields to MentorProfile
        migrations.AddField(
            model_name='mentorprofile',
            name='verification_status',
            field=models.CharField(
                choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected'), ('suspended', 'Suspended')],
                default='pending',
                db_index=True,
                help_text='Current verification status',
                max_length=20
            ),
        ),
        migrations.AddField(
            model_name='mentorprofile',
            name='verification_video_url',
            field=models.URLField(blank=True, help_text='Video introduction URL (YouTube, Vimeo, or Loom)'),
        ),
        migrations.AddField(
            model_name='mentorprofile',
            name='verification_submitted_at',
            field=models.DateTimeField(
                blank=True,
                help_text='When the profile was first submitted for verification',
                null=True
            ),
        ),
        migrations.AddField(
            model_name='mentorprofile',
            name='verification_reviewed_at',
            field=models.DateTimeField(
                blank=True,
                help_text='When an admin last reviewed this profile',
                null=True
            ),
        ),
        migrations.AddField(
            model_name='mentorprofile',
            name='verification_notes',
            field=models.TextField(blank=True, help_text='Admin feedback for rejection/suspension'),
        ),
        migrations.AddField(
            model_name='mentorprofile',
            name='flag_count',
            field=models.IntegerField(default=0, help_text='Number of complaints/flags received'),
        ),
        migrations.AddField(
            model_name='mentorprofile',
            name='flagged_at',
            field=models.DateTimeField(
                blank=True,
                help_text='When the most recent flag was received',
                null=True
            ),
        ),

        # Add flagging fields to MentorBooking
        migrations.AddField(
            model_name='mentorbooking',
            name='is_flagged',
            field=models.BooleanField(default=False, help_text='Whether this booking has been flagged for review'),
        ),
        migrations.AddField(
            model_name='mentorbooking',
            name='flag_reason',
            field=models.TextField(blank=True, help_text='Reason for flagging this booking/mentor'),
        ),
        migrations.AddField(
            model_name='mentorbooking',
            name='flagged_at',
            field=models.DateTimeField(blank=True, help_text='When this booking was flagged', null=True),
        ),

        # Data migration: Auto-verify existing mentors
        migrations.RunPython(auto_verify_existing_mentors),
    ]
