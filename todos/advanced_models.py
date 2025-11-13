"""
Advanced Task Models for PathAI
- RecurringTaskTemplate: Auto-generate periodic tasks
- TaskCompletion: Track completion feedback and adaptation
- AIInsight: Store AI-generated insights and suggestions
"""
from django.db import models
from django.conf import settings
from django.utils import timezone


class RecurringTaskTemplate(models.Model):
    """
    Template for automatically generating recurring tasks

    Examples:
    - Every Sunday: "Review career progress"
    - Every Monday: "Plan week ahead"
    - Every 2 weeks: "Update networking contacts"
    """
    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('biweekly', 'Every 2 Weeks'),
        ('monthly', 'Monthly'),
    ]

    WEEKDAY_CHOICES = [
        ('mon', 'Monday'),
        ('tue', 'Tuesday'),
        ('wed', 'Wednesday'),
        ('thu', 'Thursday'),
        ('fri', 'Friday'),
        ('sat', 'Saturday'),
        ('sun', 'Sunday'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='recurring_templates'
    )
    goalspec = models.ForeignKey(
        'users.GoalSpec',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='recurring_templates',
        help_text="Associated goal specification"
    )

    # Template info
    title = models.CharField(max_length=500, help_text="Task title template")
    description = models.TextField(blank=True, help_text="Task description template")
    task_type = models.CharField(max_length=20, default='manual')
    task_level = models.CharField(max_length=20, default='sub_goal')
    energy_level = models.CharField(max_length=20, default='medium')
    cognitive_load = models.IntegerField(default=2)
    timebox_minutes = models.IntegerField(default=30)
    priority = models.IntegerField(default=2)

    # Recurrence rules
    frequency = models.CharField(
        max_length=20,
        choices=FREQUENCY_CHOICES,
        help_text="How often to generate this task"
    )
    schedule_day = models.CharField(
        max_length=10,
        choices=WEEKDAY_CHOICES,
        null=True,
        blank=True,
        help_text="For weekly/biweekly: which day of week"
    )
    schedule_time = models.TimeField(
        null=True,
        blank=True,
        help_text="Preferred time of day"
    )

    # Generation tracking
    is_active = models.BooleanField(
        default=True,
        help_text="Whether to continue generating tasks"
    )
    next_generation_date = models.DateField(
        help_text="Next date to generate task"
    )
    last_generated_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last time task was generated"
    )
    total_generated = models.IntegerField(
        default=0,
        help_text="Total number of tasks generated from this template"
    )

    # AI suggestion tracking
    suggested_by_ai = models.BooleanField(
        default=False,
        help_text="Was this template suggested by AI?"
    )
    ai_confidence = models.FloatField(
        null=True,
        blank=True,
        help_text="AI confidence in this suggestion (0.0-1.0)"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['next_generation_date', '-is_active']
        indexes = [
            models.Index(fields=['user', 'is_active', 'next_generation_date']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.title} ({self.frequency})"

    def calculate_next_generation_date(self):
        """Calculate the next date to generate a task"""
        from datetime import timedelta

        if self.frequency == 'daily':
            return self.next_generation_date + timedelta(days=1)
        elif self.frequency == 'weekly':
            return self.next_generation_date + timedelta(weeks=1)
        elif self.frequency == 'biweekly':
            return self.next_generation_date + timedelta(weeks=2)
        elif self.frequency == 'monthly':
            return self.next_generation_date + timedelta(days=30)

        return self.next_generation_date

    def generate_task(self):
        """Generate a task from this template"""
        from .models import Todo

        task = Todo.objects.create(
            user=self.user,
            goalspec=self.goalspec,
            title=self.title,
            description=self.description,
            task_type=self.task_type,
            task_level=self.task_level,
            energy_level=self.energy_level,
            cognitive_load=self.cognitive_load,
            timebox_minutes=self.timebox_minutes,
            priority=self.priority,
            scheduled_date=self.next_generation_date,
            scheduled_time=self.schedule_time,
            source='daily_planner',  # Mark as auto-generated
            status='ready',
        )

        # Update template
        self.last_generated_at = timezone.now()
        self.total_generated += 1
        self.next_generation_date = self.calculate_next_generation_date()
        self.save()

        return task


class TaskCompletion(models.Model):
    """
    Tracks how user completed/skipped tasks with feedback
    Used for AI adaptation and insights
    """
    DIFFICULTY_CHOICES = [
        (1, 'Very Easy'),
        (2, 'Easy'),
        (3, 'Medium'),
        (4, 'Hard'),
        (5, 'Very Hard'),
    ]

    COMPLETION_REASON_CHOICES = [
        ('completed', 'Successfully Completed'),
        ('skipped_no_time', 'Skipped - No Time'),
        ('skipped_no_motivation', 'Skipped - No Motivation'),
        ('skipped_distracted', 'Skipped - Got Distracted'),
        ('skipped_overestimated', 'Skipped - Overestimated Difficulty'),
        ('skipped_blocked', 'Skipped - Blocked by Dependencies'),
        ('skipped_other', 'Skipped - Other Reason'),
    ]

    task = models.OneToOneField(
        'todos.Todo',
        on_delete=models.CASCADE,
        related_name='completion_feedback'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='task_completions'
    )

    # Completion info
    completed_at = models.DateTimeField(auto_now_add=True)
    actual_duration_minutes = models.IntegerField(
        null=True,
        blank=True,
        help_text="How long it actually took"
    )
    difficulty_rating = models.IntegerField(
        choices=DIFFICULTY_CHOICES,
        null=True,
        blank=True,
        help_text="User's subjective difficulty rating"
    )
    completion_reason = models.CharField(
        max_length=30,
        choices=COMPLETION_REASON_CHOICES,
        default='completed'
    )

    # Context
    time_of_day = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text="morning/afternoon/evening/night"
    )
    energy_level_at_completion = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text="User's energy level when completing (high/medium/low)"
    )

    # Feedback
    notes = models.TextField(
        blank=True,
        help_text="User's additional notes"
    )
    would_reschedule_to = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text="If could redo, when would user schedule this?"
    )

    # AI analysis
    analyzed_by_ai = models.BooleanField(
        default=False,
        help_text="Has AI processed this feedback?"
    )
    ai_insights = models.JSONField(
        default=dict,
        blank=True,
        help_text="AI-generated insights from this completion"
    )

    class Meta:
        ordering = ['-completed_at']
        indexes = [
            models.Index(fields=['user', '-completed_at']),
            models.Index(fields=['completion_reason']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.task.title} ({self.completion_reason})"


class AIInsight(models.Model):
    """
    AI-generated insights about user's progress and patterns
    Shown in the Insights dashboard
    """
    INSIGHT_TYPE_CHOICES = [
        ('category_progress', 'Category Progress'),  # % completion by goal category
        ('skip_pattern', 'Skip Pattern'),  # Why user skips tasks
        ('opportunity', 'New Opportunity'),  # Suggest new goals based on success
        ('milestone_suggestion', 'Milestone Suggestion'),  # Suggest next milestone
        ('time_pattern', 'Time Pattern'),  # Best time for certain tasks
        ('energy_mismatch', 'Energy Mismatch'),  # Tasks scheduled at wrong energy level
        ('overload_warning', 'Overload Warning'),  # Too many tasks
        ('success_celebration', 'Success Celebration'),  # Celebrate achievements
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ai_insights'
    )

    # Insight info
    insight_type = models.CharField(
        max_length=30,
        choices=INSIGHT_TYPE_CHOICES
    )
    category = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text="Related goal category (study/career/sport/etc)"
    )
    title = models.CharField(
        max_length=200,
        help_text="Short insight title"
    )
    message = models.TextField(
        help_text="Full insight message"
    )

    # Supporting data
    data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Supporting data (charts, stats, etc)"
    )
    action_suggestions = models.JSONField(
        default=list,
        blank=True,
        help_text="""
        Actionable suggestions: [
            {"action": "reschedule_to_morning", "task_ids": [1,2,3]},
            {"action": "reduce_daily_tasks", "from": 10, "to": 7}
        ]
        """
    )

    # Status
    is_read = models.BooleanField(default=False)
    is_dismissed = models.BooleanField(default=False)
    action_taken = models.BooleanField(
        default=False,
        help_text="Did user act on this insight?"
    )

    # Priority
    priority = models.IntegerField(
        default=2,
        help_text="1=low, 2=medium, 3=high"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this insight becomes irrelevant"
    )

    class Meta:
        ordering = ['-priority', '-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['is_read', 'is_dismissed']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.title} ({self.insight_type})"


class TaskConversation(models.Model):
    """
    Stores AI assistant conversations for tasks
    Enables conversation history and "AI Notes" feature
    """
    MODE_CHOICES = [
        ('clarify', 'Clarify'),
        ('expand', 'Expand'),
        ('research', 'Research'),
    ]

    task = models.ForeignKey(
        'todos.Todo',
        on_delete=models.CASCADE,
        related_name='conversations'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='task_conversations'
    )

    # Question & Answer
    question = models.TextField(help_text="User's question")
    answer = models.TextField(help_text="AI's response")
    mode = models.CharField(
        max_length=20,
        choices=MODE_CHOICES,
        default='clarify',
        help_text="AI mode used for this response"
    )

    # Structured response data
    links = models.JSONField(
        default=list,
        blank=True,
        help_text="Links provided in response"
    )
    contacts = models.JSONField(
        default=list,
        blank=True,
        help_text="Contacts provided in response"
    )
    steps = models.JSONField(
        default=list,
        blank=True,
        help_text="Steps provided in response"
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    was_expanded = models.BooleanField(
        default=False,
        help_text="Was this question expanded from clarify to research?"
    )

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['task', 'created_at']),
            models.Index(fields=['user', '-created_at']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.task.title[:30]} - {self.question[:50]}"
