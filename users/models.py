from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser
    """
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Streak tracking
    current_streak = models.IntegerField(default=0)
    longest_streak = models.IntegerField(default=0)
    last_activity_date = models.DateField(null=True, blank=True)

    # Push notifications
    push_token = models.CharField(max_length=255, blank=True, null=True, help_text="Expo push notification token")
    push_enabled = models.BooleanField(default=True, help_text="Global push notifications toggle")

    # User timezone (IANA timezone string, e.g., "Asia/Almaty", "America/New_York")
    timezone = models.CharField(max_length=63, default='UTC', help_text="User's timezone for accurate time interpretation")

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email


class UserProfile(models.Model):
    """
    Extended user profile with onboarding data
    """
    COACH_CHARACTER_CHOICES = [
        ('aggressive', 'Aggressive'),
        ('cute', 'Cute'),
        ('supportive', 'Supportive'),
        ('professional', 'Professional'),
    ]

    ENERGY_PEAK_CHOICES = [
        ('morning', 'Morning'),
        ('afternoon', 'Afternoon'),
        ('evening', 'Evening'),
        ('night', 'Night'),
    ]

    NOTIFICATION_TONE_CHOICES = [
        ('gentle', 'Gentle'),
        ('firm', 'Firm'),
        ('motivational', 'Motivational'),
    ]

    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('ru', 'Русский'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')

    # Basic Info
    name = models.CharField(max_length=255)
    age = models.IntegerField(null=True, blank=True)
    country_of_residence = models.CharField(max_length=100, blank=True)

    # Goals & Situation
    current_situation = models.TextField(blank=True)
    future_goals = models.TextField(blank=True)
    dream_career = models.TextField(blank=True)
    budget_range = models.CharField(max_length=100, blank=True)
    target_timeline = models.CharField(max_length=100, blank=True)

    # Preferences
    preferred_language = models.CharField(
        max_length=5,
        choices=LANGUAGE_CHOICES,
        default='en'
    )
    coach_character = models.CharField(
        max_length=20,
        choices=COACH_CHARACTER_CHOICES,
        default='supportive'
    )
    energy_peak = models.CharField(
        max_length=20,
        choices=ENERGY_PEAK_CHOICES,
        default='morning'
    )
    notification_tone = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TONE_CHOICES,
        default='gentle'
    )
    check_in_time = models.TimeField(null=True, blank=True)
    daily_available_minutes = models.IntegerField(
        default=480,
        help_text="User's available working minutes per day (default: 480 = 8 hours)"
    )

    # Additional Context (JSON fields for flexibility)
    languages = models.JSONField(default=list, blank=True)  # [{"code": "en", "level": "B2"}]
    destinations = models.JSONField(default=list, blank=True)  # ["UK", "DE"]
    network = models.JSONField(default=dict, blank=True)  # {"mentors": [...], "warm_intros": [...]}
    constraints = models.JSONField(default=dict, blank=True)  # Risks, deadlines, etc.

    # Domain-Specific Assessment Fields (for Day 1 personalization)
    # Study/Education
    gpa = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True, help_text="GPA on 4.0 scale")
    test_scores = models.JSONField(default=dict, blank=True, help_text='{"IELTS": 7.0, "TOEFL": 100, "GRE": 320, "GMAT": 700} or {"ielts": 7.0} from conversational')
    field_of_study = models.CharField(max_length=200, blank=True, help_text="e.g., Computer Science, Business")
    prior_education = models.JSONField(default=list, blank=True, help_text='[{"degree": "BSc", "institution": "KazNU", "year": 2023}]')

    # NEW: Conversational Onboarding - Study
    degree_level = models.CharField(max_length=50, blank=True, help_text="bachelor, master, phd, bootcamp from conversational onboarding")
    target_country = models.CharField(max_length=100, blank=True, help_text="Target country for studying from conversational onboarding")
    budget = models.CharField(max_length=100, blank=True, help_text="Budget per year (e.g., '$15,000') from conversational onboarding")
    target_schools = models.JSONField(default=list, blank=True, help_text='["University of Edinburgh", "UCL"] from conversational onboarding')
    current_education = models.CharField(max_length=300, blank=True, help_text="Current degree and university from conversational onboarding")
    research_interests = models.TextField(blank=True, help_text="Research interests for grad programs from conversational onboarding")
    coding_experience = models.TextField(blank=True, help_text="Programming background and skills for technical programs")
    why_this_field = models.TextField(blank=True, help_text="Motivation for choosing this field of study")

    # Career/Professional
    years_of_experience = models.IntegerField(null=True, blank=True, help_text="Total years of professional experience")
    current_role = models.CharField(max_length=200, blank=True, help_text="Current job title")
    companies_worked = models.JSONField(default=list, blank=True, help_text='["Google", "Startup XYZ"]')
    skills = models.JSONField(default=list, blank=True, help_text='["Python", "React", "Project Management"]')
    referral_network_size = models.IntegerField(null=True, blank=True, help_text="Number of people who could refer you")

    # Role-Specific Career Fields (for hyper-personalization)
    career_specialization = models.CharField(max_length=100, blank=True, help_text="e.g., Backend Engineer, UX Designer, Product Manager")
    tech_stack = models.JSONField(default=dict, blank=True, help_text='Can be dict {"languages": [...]} OR list ["Python", "Django"] from conversational onboarding')
    design_tools = models.JSONField(default=dict, blank=True, help_text='{"design": ["Figma", "Sketch"], "prototyping": ["Protopie"], "research": ["Maze"]}')
    design_discipline = models.CharField(max_length=100, blank=True, help_text="e.g., UX Designer, UI Designer, Product Designer")
    design_specialization = models.CharField(max_length=200, blank=True, help_text="e.g., B2B SaaS, Mobile Apps, E-commerce")
    portfolio_quality = models.CharField(max_length=50, blank=True, choices=[
        ('none', 'No portfolio yet'),
        ('basic', 'Basic portfolio (3-5 projects)'),
        ('strong', 'Strong portfolio (5-10 case studies)'),
        ('award_winning', 'Award-winning portfolio'),
    ], help_text="Self-assessed portfolio quality")
    experience_level = models.CharField(max_length=50, blank=True, choices=[
        ('entry', 'Entry-level (0-1 years)'),
        ('junior', 'Junior (1-2 years)'),
        ('mid', 'Mid-level (3-5 years)'),
        ('senior', 'Senior (5-8 years)'),
        ('staff_plus', 'Staff+ (8+ years)'),
    ], help_text="Structured experience level")
    target_company_types = models.JSONField(default=list, blank=True, help_text='["Startups", "FAANG", "Finance", "Remote-first"]')
    notable_projects = models.JSONField(default=list, blank=True, help_text='[{"title": "Built real-time chat", "impact": "Handled 10k users"}]')
    current_company = models.CharField(max_length=200, blank=True, help_text="Current employer name")

    # NEW: Conversational Onboarding - Career
    target_role = models.CharField(max_length=200, blank=True, help_text="Target role from conversational onboarding")
    notable_achievements = models.JSONField(default=list, blank=True, help_text='["Built system handling 50k req/sec", "Led team of 5"] from conversational onboarding')
    target_companies = models.JSONField(default=list, blank=True, help_text='["Startups", "FAANG"] from conversational onboarding')
    years_experience = models.IntegerField(null=True, blank=True, help_text="Alias for years_of_experience for conversational onboarding compatibility")

    # Fitness/Health
    fitness_level = models.CharField(max_length=50, blank=True, choices=[
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ], help_text="Self-assessed fitness level")
    injuries_limitations = models.JSONField(default=list, blank=True, help_text='["Knee injury", "Lower back pain"]')
    gym_access = models.BooleanField(null=True, blank=True, help_text="Has access to gym equipment")
    workout_history = models.JSONField(default=dict, blank=True, help_text='{"frequency": "3x/week", "duration": "45min"}')

    # NEW: Conversational Onboarding - Sport/Fitness
    fitness_goal_type = models.CharField(max_length=100, blank=True, help_text="lose_weight, build_muscle, run_marathon, etc. from conversational onboarding")
    equipment = models.JSONField(default=list, blank=True, help_text='["dumbbells", "yoga mat"] from conversational onboarding')
    injuries = models.TextField(blank=True, help_text="Text description of injuries from conversational onboarding")

    # NEW: Universal fields for all categories
    timeline = models.CharField(max_length=100, blank=True, help_text="Timeline/deadline from conversational onboarding (e.g., '6 months', 'Fall 2026')")

    # NEW: Background Discovery (universal - makes plans 10x better)
    has_startup_background = models.BooleanField(default=False, help_text="User has founded/built startup, business, or product with users")
    startup_details = models.TextField(blank=True, help_text="Details: what it does, users/customers, revenue, funding, role. Example: 'Language learning app, 10k users, built in high school'")
    has_notable_achievements = models.BooleanField(default=False, help_text="User has impressive achievements: awards, competitions, publications, impactful projects")
    achievement_details = models.TextField(blank=True, help_text="Details with metrics/impact. Example: 'Won national coding olympiad 2023' or 'Built system handling 50k users'")
    has_research_background = models.BooleanField(default=False, help_text="User has research experience: papers, publications, working with professors")
    research_details = models.TextField(blank=True, help_text="Details: field, publications, professors, lab work. Example: 'ML research with Prof. Smith, published at EMNLP 2024'")
    impressive_projects = models.JSONField(default=list, blank=True, help_text='List of impressive projects with metrics. Example: ["E-commerce site with $50k revenue", "Open-source library with 2k stars"]')

    # Performance Insights (updated nightly by PerformanceAnalyzer)
    performance_insights = models.JSONField(default=dict, blank=True, help_text='AI-generated patterns: optimal schedule, blockers, strengths')
    last_performance_analysis = models.DateTimeField(null=True, blank=True, help_text="When performance was last analyzed")

    # Adaptive Coach Interventions (Phase 2: Plan-B adaptation)
    last_intervention_at = models.DateTimeField(null=True, blank=True, help_text="When AdaptiveCoach last intervened")
    last_intervention_type = models.CharField(max_length=50, blank=True, help_text="planb_switch | workload_reduction | blocker_reduction | etc.")
    intervention_history = models.JSONField(default=list, blank=True, help_text='[{"date": "2025-11-06", "type": "planb_switch", "accepted": true}]')

    # LLM Budget Tracking (Week 1 Day 1-2: Hybrid Task Generation Enhancement)
    llm_budget_spent = models.DecimalField(
        max_digits=6,
        decimal_places=4,
        default=0,
        help_text="Total LLM cost spent by user (resets monthly)"
    )
    llm_budget_limit = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=5.00,
        help_text="Monthly LLM budget limit in USD (soft limit with alerts)"
    )
    llm_budget_reset_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When LLM budget counter was last reset (monthly)"
    )

    # Timestamps
    onboarding_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} - {self.name}"


class NotificationPreferences(models.Model):
    """
    User notification preferences
    Controls which types of notifications user receives
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_preferences')

    # Notification types toggles
    task_reminders_enabled = models.BooleanField(default=True, help_text="Reminders before scheduled tasks")
    deadline_notifications_enabled = models.BooleanField(default=True, help_text="Deadline and overdue notifications")
    ai_motivation_enabled = models.BooleanField(default=True, help_text="Motivational messages from AI coach")
    daily_pulse_reminder_enabled = models.BooleanField(default=True, help_text="Daily check-in reminders")

    # Timing preferences
    task_reminder_minutes_before = models.IntegerField(default=15, help_text="How many minutes before task to send reminder")
    daily_pulse_time = models.TimeField(default='20:00', help_text="Time to send daily pulse reminder (e.g., 8 PM)")

    # Quiet hours
    quiet_hours_enabled = models.BooleanField(default=False, help_text="Enable quiet hours (no notifications)")
    quiet_hours_start = models.TimeField(null=True, blank=True, help_text="Quiet hours start time (e.g., 22:00)")
    quiet_hours_end = models.TimeField(null=True, blank=True, help_text="Quiet hours end time (e.g., 08:00)")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Notification Preferences"
        verbose_name_plural = "Notification Preferences"

    def __str__(self):
        return f"{self.user.email} - Notification Preferences"

    def is_quiet_hours(self):
        """Check if current time is within quiet hours"""
        if not self.quiet_hours_enabled or not self.quiet_hours_start or not self.quiet_hours_end:
            return False

        from django.utils import timezone
        now = timezone.localtime().time()

        # Handle quiet hours that span midnight
        if self.quiet_hours_start < self.quiet_hours_end:
            return self.quiet_hours_start <= now < self.quiet_hours_end
        else:
            return now >= self.quiet_hours_start or now < self.quiet_hours_end


class OnboardingProgress(models.Model):
    """
    Track multi-category onboarding progress for conversational onboarding.

    Flow:
    1. User selects categories (e.g., ['study', 'career'])
    2. User chats for each category sequentially
    3. Tasks are generated ONLY after ALL categories are complete
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='onboarding_progress')

    # Category tracking
    selected_categories = models.JSONField(
        default=list,
        help_text='Categories user selected for onboarding, e.g., ["study", "career"]'
    )
    completed_categories = models.JSONField(
        default=list,
        help_text='Categories where user has completed chat, e.g., ["study"]'
    )
    current_category = models.CharField(
        max_length=50,
        blank=True,
        help_text='Category user is currently chatting for, e.g., "study"'
    )

    # Status tracking
    STATUS_CHOICES = [
        ('category_selection', 'Selecting Categories'),
        ('chatting', 'Chatting for Categories'),
        ('generating_tasks', 'Generating Tasks'),
        ('complete', 'Complete'),
    ]
    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default='category_selection',
        help_text='Current onboarding stage'
    )
    is_complete = models.BooleanField(
        default=False,
        help_text='True when all categories are complete and tasks are generated'
    )
    tasks_generated = models.BooleanField(
        default=False,
        help_text='True when tasks have been generated (idempotency check)'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True, help_text='When onboarding fully completed')

    class Meta:
        verbose_name = "Onboarding Progress"
        verbose_name_plural = "Onboarding Progress"

    def __str__(self):
        return f"{self.user.email} - {self.status} - {len(self.completed_categories)}/{len(self.selected_categories)} complete"


class OnboardingChatData(models.Model):
    """
    Temporarily store extracted data from each category's conversational onboarding.
    This data is merged into UserProfile when all categories are complete.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='onboarding_chat_data')
    category = models.CharField(
        max_length=50,
        help_text='Category this data is for, e.g., "study", "career", "sport"'
    )
    extracted_data = models.JSONField(
        default=dict,
        help_text='Extracted data from conversational onboarding for this category'
    )
    is_merged = models.BooleanField(
        default=False,
        help_text='True when data has been merged into UserProfile'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Onboarding Chat Data"
        verbose_name_plural = "Onboarding Chat Data"
        unique_together = ('user', 'category')  # One record per user per category

    def __str__(self):
        return f"{self.user.email} - {self.category} - {'Merged' if self.is_merged else 'Pending'}"


# Import GoalSpec model to make it discoverable by Django
from .goalspec_models import GoalSpec
