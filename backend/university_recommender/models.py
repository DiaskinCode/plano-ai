from django.db import models
from django.contrib.auth import get_user_model
from university_database.models import University

User = get_user_model()


class RecommendationLog(models.Model):
    """
    Track each recommendation session for analytics
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recommendation_logs')
    profile_snapshot = models.JSONField(
        help_text="Profile data at the time of recommendation"
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    total_recommendations = models.IntegerField(
        help_text="Total number of universities recommended"
    )
    filter_count = models.IntegerField(
        help_text="Number of universities after filtering"
    )
    llm_reranked = models.BooleanField(
        default=False,
        help_text="Whether LLM reranking was applied"
    )

    class Meta:
        verbose_name = "Recommendation Log"
        verbose_name_plural = "Recommendation Logs"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['-timestamp']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"


class RecommendationItem(models.Model):
    """
    Each university in a recommendation (Tabular model for proper analytics)
    """
    log = models.ForeignKey(
        RecommendationLog,
        on_delete=models.CASCADE,
        related_name='items'
    )
    university = models.ForeignKey(University, on_delete=models.CASCADE)
    rank = models.IntegerField(
        help_text="Position in results (1-indexed)"
    )

    # Scores
    fit_score = models.IntegerField(
        help_text="Fit score (0-100) - how well university matches preferences"
    )
    chance_score = models.IntegerField(
        help_text="Chance score (0-100) - how likely admission is"
    )
    finance_score = models.IntegerField(
        help_text="Finance score (0-100) - how feasible paying is"
    )
    final_rank_score = models.IntegerField(
        help_text="Final ranking score (0-100)"
    )

    # LLM Data (nullable - only for top 20-40 universities)
    llm_fit_score = models.IntegerField(
        null=True,
        blank=True,
        help_text="LLM-assessed fit score"
    )
    LLM_CONFIDENCE_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    llm_confidence = models.CharField(
        max_length=20,
        choices=LLM_CONFIDENCE_CHOICES,
        null=True,
        blank=True
    )
    llm_reasons = models.JSONField(
        default=list,
        help_text="LLM-generated reasons for fit"
    )
    llm_risks = models.JSONField(
        default=list,
        help_text="LLM-generated risks/concerns"
    )
    llm_why_not_fit = models.JSONField(
        default=list,
        help_text="LLM-generated reasons why not a good fit"
    )
    llm_missing_info = models.JSONField(
        default=list,
        help_text="LLM-generated missing info gaps"
    )
    llm_next_actions = models.JSONField(
        default=list,
        help_text="LLM-generated suggested next actions"
    )

    # Bucket Assignment
    BUCKET_CHOICES = [
        ('Reach', 'Reach'),
        ('Match', 'Match'),
        ('Safety', 'Safety'),
    ]
    bucket = models.CharField(
        max_length=20,
        choices=BUCKET_CHOICES,
        help_text="Admissions likelihood category"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Recommendation Item"
        verbose_name_plural = "Recommendation Items"
        ordering = ['log', 'rank']
        indexes = [
            models.Index(fields=['log', 'rank']),
            models.Index(fields=['university', 'bucket']),
            models.Index(fields=['-created_at']),
        ]


class RecommendationFeedback(models.Model):
    """
    User feedback on recommendations for learning and improvement
    """
    item = models.ForeignKey(
        RecommendationItem,
        on_delete=models.CASCADE,
        related_name='feedback'
    )

    ACTION_CHOICES = [
        ('shortlisted', 'Shortlisted'),
        ('removed', 'Removed'),
        ('bucket_changed', 'Bucket Changed'),
        ('applied', 'Applied'),
        ('ignored', 'Ignored'),
    ]
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)

    new_bucket = models.CharField(
        max_length=20,
        choices=RecommendationItem.BUCKET_CHOICES,
        null=True,
        blank=True,
        help_text="New bucket if user changed it"
    )
    notes = models.TextField(blank=True, help_text="User notes on feedback")

    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Recommendation Feedback"
        verbose_name_plural = "Recommendation Feedbacks"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['item', 'action']),
            models.Index(fields=['-timestamp']),
        ]


class UniversityShortlist(models.Model):
    """
    User's saved universities for comparison and tracking
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='university_shortlist')
    university = models.ForeignKey(University, on_delete=models.CASCADE)

    added_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, help_text="User notes about this university")

    STATUS_CHOICES = [
        ('researching', 'Researching'),
        ('applying', 'Applying'),
        ('applied', 'Applied'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('waitlisted', 'Waitlisted'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='researching')

    class Meta:
        verbose_name = "University Shortlist"
        verbose_name_plural = "University Shortlists"
        unique_together = ['user', 'university']
        ordering = ['-added_at']
        indexes = [
            models.Index(fields=['user', '-added_at']),
            models.Index(fields=['user', 'status']),
        ]
