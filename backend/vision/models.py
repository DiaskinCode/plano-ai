from django.db import models
from django.conf import settings


class Scenario(models.Model):
    """
    Success scenarios generated for user's goals
    """
    PLAN_TYPE_CHOICES = [
        ('main', 'Main Plan'),
        ('plan_b', 'Plan B'),
        ('plan_c', 'Plan C'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='scenarios')
    title = models.CharField(max_length=500)
    description = models.TextField()
    pros = models.JSONField(default=list)  # List of pros
    cons = models.JSONField(default=list)  # List of cons
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPE_CHOICES, default='main')
    is_selected = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['plan_type', '-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.title} ({self.plan_type})"


class Vision(models.Model):
    """
    User's detailed vision/plan linked to a scenario
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='visions')
    scenario = models.OneToOneField(Scenario, on_delete=models.CASCADE, related_name='vision', null=True, blank=True)

    title = models.CharField(max_length=500)
    summary = models.TextField()
    horizon_start = models.DateField()
    horizon_end = models.DateField()

    # Monthly milestones stored as JSON
    monthly_milestones = models.JSONField(default=list)
    # Format: [{"month": "2025-11", "title": "...", "tasks": [...]}]

    # Progress tracking
    progress_percentage = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_active', '-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.title}"


class Milestone(models.Model):
    """
    Major milestones within a vision
    """
    STATE_CHOICES = [
        ('done', 'Done'),
        ('in_progress', 'In Progress'),
        ('next', 'Next'),
        ('later', 'Later'),
        ('at_risk', 'At Risk'),
    ]

    vision = models.ForeignKey(Vision, on_delete=models.CASCADE, related_name='milestones')
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    due_date = models.DateField()
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Progress tracking
    state = models.CharField(max_length=20, choices=STATE_CHOICES, default='later')
    percent = models.IntegerField(default=0)  # 0-100 completion percentage
    buffer_days = models.IntegerField(default=0)  # Safety buffer days
    risk_flags = models.JSONField(default=list)  # Array of risk identifiers
    proofs = models.JSONField(default=list)  # Array of proof objects (files, tasks, etc.)

    # Stats (cached for performance)
    focus_minutes = models.IntegerField(default=0)  # Cumulative focus time spent
    critical_tasks_done = models.IntegerField(default=0)  # Completed critical tasks count
    critical_tasks_total = models.IntegerField(default=0)  # Total critical tasks count

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['due_date']

    def __str__(self):
        return f"{self.vision.title} - {self.title}"
