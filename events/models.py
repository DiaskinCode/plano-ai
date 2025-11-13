from django.db import models
from django.conf import settings


class CheckInEvent(models.Model):
    """
    Evening check-in events tracking user's day
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='checkins')
    date = models.DateField()

    # What user completed
    completed_tasks = models.JSONField(default=list)  # List of todo IDs
    completed_tasks_text = models.TextField(blank=True)  # Free text of what was done

    # What user missed/skipped
    missed_tasks = models.JSONField(default=list)  # List of todo IDs
    missed_tasks_text = models.TextField(blank=True)
    missed_reason = models.TextField(blank=True)

    # New information/opportunities
    new_opportunities = models.TextField(blank=True)

    # AI response and optimization
    ai_response = models.TextField(blank=True)  # Supportive message
    ai_recommendations = models.JSONField(default=dict)  # Tomorrow's optimization

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']
        unique_together = ['user', 'date']

    def __str__(self):
        return f"{self.user.email} - Check-in {self.date}"


class OpportunityEvent(models.Model):
    """
    New opportunities that might change the vision
    """
    IMPACT_CHOICES = [
        ('low', 'Low Impact'),
        ('medium', 'Medium Impact'),
        ('high', 'High Impact'),
        ('game_changer', 'Game Changer'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='opportunities')
    title = models.CharField(max_length=500)
    description = models.TextField()
    date_occurred = models.DateField()

    # AI analysis
    ai_impact_assessment = models.CharField(
        max_length=20,
        choices=IMPACT_CHOICES,
        default='medium'
    )
    ai_recommendation = models.TextField(blank=True)  # Pivot, integrate, or ignore
    requires_vision_change = models.BooleanField(default=False)

    # User decision
    user_action = models.CharField(max_length=20, blank=True)  # 'pivot', 'integrate', 'ignore'
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date_occurred']

    def __str__(self):
        return f"{self.user.email} - {self.title}"
