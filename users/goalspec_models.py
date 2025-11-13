"""
GoalSpec Model - User's specific goal configuration
Collected during onboarding to generate atomic tasks
"""
from django.db import models
from django.conf import settings


class GoalSpec(models.Model):
    """
    User's specific goal configuration
    Stores all constraints, preferences, and settings for task generation
    """
    GOAL_TYPE_CHOICES = [
        ('study', 'Study'),  # University admission, language learning, etc.
        ('career', 'Career'),  # Job search, skill development, etc.
        ('sport', 'Sport'),  # Fitness, training, competitions
        ('finance', 'Finance'),  # Financial goals
        ('language', 'Language'),  # Language learning
        ('health', 'Health'),  # Health & wellness
        ('creative', 'Creative'),  # Creative projects
        ('admin', 'Admin'),  # Administrative tasks
        ('research', 'Research'),  # Research projects
        ('networking', 'Networking'),  # Networking goals
        ('travel', 'Travel'),  # Travel planning
        ('other', 'Other'),  # Custom goals
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
        ('archived', 'Archived'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='goalspecs')
    category = models.CharField(max_length=20, choices=GOAL_TYPE_CHOICES, default='other')
    goal_type = models.CharField(max_length=20, choices=GOAL_TYPE_CHOICES)  # Legacy field, use category instead

    # Generic title and description
    title = models.CharField(max_length=200, help_text="e.g., 'Get into top CS MS program'")
    description = models.TextField(blank=True, help_text="Brief description of the goal")
    target_date = models.DateField(null=True, blank=True, help_text="Target completion date")

    # Specifications from survey (replaces individual constraint fields)
    specifications = models.JSONField(
        default=dict,
        blank=True,
        help_text="""
        Complete survey data from onboarding.
        Study: {"country": "USA", "degree": "MSc CS", "budget": "£10-30k", "intake": "Sep 2026", ...}
        Career: {"targetRole": "PM", "industry": "Fintech", "experience": "3 years", ...}
        Sport: {"sportType": "Gym", "sportGoal": "Build muscle", "weeklyHours": "6", ...}
        """
    )

    # AI Permissions (from spec review screen)
    permissions = models.JSONField(
        default=dict,
        blank=True,
        help_text='{"allowDocs": false, "allowEmails": false, "allowCalendar": false}'
    )

    # Quick wins selected during onboarding
    quick_wins = models.JSONField(
        default=list,
        blank=True,
        help_text='[{"title": "...", "description": "...", "estimated_time": "..."}]'
    )

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')

    # Constraints (specific to goal_type)
    # For 'study': country, budget, degree, deadline, test_status, visa_required, etc.
    # For 'career': target_role, industry, experience_level, weekly_applications, etc.
    # For 'sport': sport_type, goal, weekly_hours, current_level, etc.
    constraints = models.JSONField(
        default=dict,
        help_text="""
        Goal-specific constraints. Examples:
        Study: {"country": "USA", "budget": "$10-30k", "degree": "MS CS", "deadline": "2025-12-01"}
        Career: {"target_role": "Product Manager", "industry": "Fintech", "experience": "3-5 years"}
        Sport: {"sport_type": "Gym", "goal": "Build muscle", "weekly_hours": 6}
        """
    )

    # Preferences (soft requirements)
    preferences = models.JSONField(
        default=dict,
        help_text="""
        User preferences. Examples:
        Study: {"regions": ["West Coast"], "program_focus": ["AI/ML"], "campus_size": "Large"}
        Career: {"remote_ok": true, "startup_vs_corporate": "Startup"}
        """
    )

    # Assets (CV, portfolio, etc.)
    assets = models.JSONField(
        default=dict,
        help_text='{"cv_url": "...", "linkedin": "...", "portfolio": "..."}'
    )

    # Timeline
    timeline = models.JSONField(
        default=dict,
        help_text='{"start_date": "2025-10-15", "target_date": "2026-06-01", "hard_deadlines": [...]}'
    )

    # Priority weight for daily planner
    priority_weight = models.FloatField(
        default=1.0,
        help_text="Relative priority compared to other goals (0.1-1.0)"
    )

    # Daily time budget
    daily_time_budget_minutes = models.IntegerField(
        default=120,  # 2 hours default
        help_text="Minutes per day user can dedicate to this goal"
    )

    # Cadence rules (category-specific task patterns)
    cadence_rules = models.JSONField(
        default=dict,
        blank=True,
        help_text="""
        Study: {"pattern": "shortlist → deadlines → essays → lors → submissions"}
        Career: {"weekly": {"M": "apply_2", "W": "apply_2", "F": "apply_2", "Tue": "referrals_3", "Thu": "mocks_2"}}
        Sport: {"daily": {"Mon": "chest", "Tue": "arms", "Wed": "legs", ...}}
        """
    )

    # Status
    is_active = models.BooleanField(default=True)
    completed = models.BooleanField(default=False)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-priority_weight', '-created_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['goal_type']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.title} ({self.goal_type})"

    def get_total_weight(self):
        """Calculate total priority weight across all active goals"""
        total = GoalSpec.objects.filter(
            user=self.user,
            is_active=True
        ).aggregate(total=models.Sum('priority_weight'))['total'] or 1.0
        return total

    def get_daily_minutes(self, total_available_minutes):
        """
        Calculate daily minutes for this goal based on priority weight

        Args:
            total_available_minutes: User's total daily available time

        Returns:
            Minutes allocated to this goal
        """
        total_weight = self.get_total_weight()
        my_share = self.priority_weight / total_weight
        return int(total_available_minutes * my_share)

    def validate_constraints(self):
        """Validate that required constraints are present for goal_type"""
        required_keys = {
            'study': ['country', 'degree'],
            'career': ['target_role'],
            'sport': ['sport_type'],
        }

        required = required_keys.get(self.goal_type, [])
        missing = [key for key in required if key not in self.constraints]

        if missing:
            return False, f"Missing required constraints: {', '.join(missing)}"

        return True, "Valid"
