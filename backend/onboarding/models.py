"""
Onboarding models for the structured 14-step college application onboarding flow.
This handles the new onboarding system separate from the conversational onboarding.
"""
from django.db import models
from django.conf import settings


class OnboardingState(models.Model):
    """
    Track user progress through the 14-step onboarding flow.

    Steps:
    0: Language Selection
    1: Welcome Screen
    2: Authentication
    3: Basic Profile
    4: Academic Background
    5: Test Scores
    6: Extracurriculars
    7: Target Universities (AI-suggested)
    8: Plan Selection
    9: AI Plan Generation
    10: Plan Preview (Paywall)
    11: Subscription Selection
    12: Payment
    13: Success & Quick Setup
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='structured_onboarding'
    )
    current_step = models.IntegerField(default=0, help_text="Current step (0-13)")
    completed_steps = models.JSONField(default=list, help_text="List of completed step numbers")
    data = models.JSONField(default=dict, help_text="All onboarding data collected")
    selected_language = models.CharField(max_length=10, default='en', help_text="Selected language code")
    is_onboarding_complete = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Onboarding State"
        verbose_name_plural = "Onboarding States"

    def __str__(self):
        return f"{self.user.email} - Step {self.current_step}/13"

    def get_progress_percentage(self):
        """Calculate progress as percentage"""
        return int((self.current_step / 13) * 100)


class SubscriptionPlan(models.Model):
    """
    Subscription tiers for the platform.
    """
    PLAN_CHOICES = [
        ('basic', 'Basic'),
        ('pro', 'Pro'),
        ('premium', 'Premium'),
    ]

    name = models.CharField(max_length=50, choices=PLAN_CHOICES, unique=True)
    display_name = models.CharField(max_length=100)
    price_monthly = models.DecimalField(max_digits=6, decimal_places=2)
    price_yearly = models.DecimalField(max_digits=6, decimal_places=2)
    features = models.JSONField(default=list, help_text="List of feature strings")
    stripe_price_id_monthly = models.CharField(max_length=100, blank=True)
    stripe_price_id_yearly = models.CharField(max_length=100, blank=True)
    is_popular = models.BooleanField(default=False, help_text="Mark as most popular")
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)

    # Limits for Pro/Premium plans
    monthly_video_calls = models.IntegerField(default=0, help_text="Number of video calls per month")
    monthly_text_questions = models.IntegerField(default=0, help_text="Number of text questions per month")
    monthly_mentor_bookings = models.IntegerField(default=0, help_text="Number of mentor session bookings per month")
    dedicated_mentor = models.BooleanField(default=False, help_text="Whether user gets a dedicated mentor")

    class Meta:
        ordering = ['order']
        verbose_name = "Subscription Plan"
        verbose_name_plural = "Subscription Plans"

    def __str__(self):
        return f"{self.display_name} (${self.price_monthly}/mo)"


class UserSubscription(models.Model):
    """
    User subscription information.
    """
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('trial', 'Trial'),
        ('canceled', 'Canceled'),
        ('past_due', 'Past Due'),
        ('incomplete', 'Incomplete'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscription'
    )
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.PROTECT,
        related_name='subscriptions'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='incomplete')
    stripe_subscription_id = models.CharField(max_length=100, unique=True)
    stripe_customer_id = models.CharField(max_length=100, blank=True)

    current_period_start = models.DateTimeField()
    current_period_end = models.DateTimeField()
    cancel_at_period_end = models.BooleanField(default=False)

    # Mentor assignment for Pro/Premium plans
    mentor_assigned = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='mentored_users',
        help_text="Assigned mentor for Pro/Premium users"
    )

    # Usage tracking
    remaining_video_calls = models.IntegerField(default=0)
    remaining_text_questions = models.IntegerField(default=0)
    remaining_mentor_bookings = models.IntegerField(default=0, help_text="Remaining mentor bookings this month")

    # Promotion tracking
    promo_code_used = models.CharField(max_length=50, blank=True)
    discount_percentage = models.IntegerField(default=0, help_text="Discount percentage applied")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User Subscription"
        verbose_name_plural = "User Subscriptions"

    def __str__(self):
        return f"{self.user.email} - {self.plan.display_name} ({self.status})"

    def save(self, *args, **kwargs):
        # Initialize quotas on first creation
        if not self.pk:  # New subscription
            if self.remaining_mentor_bookings == 0:
                self.remaining_mentor_bookings = self.plan.monthly_mentor_bookings
            if self.remaining_video_calls == 0:
                self.remaining_video_calls = self.plan.monthly_video_calls
            if self.remaining_text_questions == 0:
                self.remaining_text_questions = self.plan.monthly_text_questions
        super().save(*args, **kwargs)

    def is_active(self):
        """Check if subscription is active"""
        return self.status == 'active' or self.status == 'trial'

    def can_book_mentor_session(self):
        """Check if user can book a mentor session"""
        if not self.is_active():
            return False
        return self.remaining_mentor_bookings > 0

    def get_mentor_booking_limit(self):
        """Get the monthly mentor booking limit for this subscription"""
        return self.plan.monthly_mentor_bookings

    def use_mentor_booking(self):
        """Decrement mentor booking count"""
        if self.remaining_mentor_bookings > 0:
            self.remaining_mentor_bookings -= 1
            self.save()

    def reset_monthly_mentor_bookings(self):
        """Reset mentor booking count to plan limit (called on subscription renewal)"""
        self.remaining_mentor_bookings = self.plan.monthly_mentor_bookings
        self.save()


class TargetUniversity(models.Model):
    """
    Target universities selected by the user during onboarding.
    Can be AI-suggested or manually added.
    """
    CATEGORY_CHOICES = [
        ('reach', 'Reach'),
        ('target', 'Target'),
        ('safety', 'Safety'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='target_universities'
    )
    university_name = models.CharField(max_length=200)
    university_slug = models.SlugField(max_length=100)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    country = models.CharField(max_length=100)
    state_province = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    acceptance_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    avg_sat = models.IntegerField(null=True, blank=True)
    avg_act = models.IntegerField(null=True, blank=True)
    tuition_per_year = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    application_deadline = models.DateField(null=True, blank=True)
    major = models.CharField(max_length=100)
    why_suggested = models.TextField(blank=True, help_text="AI reasoning for suggestion")
    is_ai_suggested = models.BooleanField(default=True)
    is_selected = models.BooleanField(default=True, help_text="User selected this university")
    priority_order = models.IntegerField(default=0, help_text="User's priority ranking")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['priority_order', 'category']
        verbose_name = "Target University"
        verbose_name_plural = "Target Universities"

    def __str__(self):
        return f"{self.user.email} - {self.university_name} ({self.category})"


class ExtracurricularActivity(models.Model):
    """
    Extracurricular activities collected during onboarding.
    """
    CATEGORY_CHOICES = [
        ('leadership', 'Leadership'),
        ('academic', 'Academic'),
        ('sports', 'Sports'),
        ('arts', 'Arts'),
        ('community_service', 'Community Service'),
        ('work', 'Work Experience'),
        ('entrepreneurship', 'Entrepreneurship'),
        ('technology', 'Technology'),
        ('research', 'Research'),
        ('other', 'Other'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='extracurriculars'
    )
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    title = models.CharField(max_length=200)
    organization = models.CharField(max_length=200, blank=True)
    role = models.CharField(max_length=100)
    description = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_ongoing = models.BooleanField(default=False)
    hours_per_week = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)

    # Achievement metrics (optional)
    achievements = models.TextField(blank=True, help_text="Notable achievements, impact, results")
    leadership_role = models.BooleanField(default=False, help_text="Whether user held leadership position")

    priority_order = models.IntegerField(default=0, help_text="User's priority ranking")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['priority_order', '-start_date']
        verbose_name = "Extracurricular Activity"
        verbose_name_plural = "Extracurricular Activities"

    def __str__(self):
        return f"{self.user.email} - {self.title} ({self.category})"


class OnboardingSnapshot(models.Model):
    """
    Snapshot of onboarding data for analytics and recovery.
    Stores the state at each step for analytics and recovery purposes.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='onboarding_snapshots'
    )
    step = models.IntegerField(help_text="Step number (0-13)")
    data = models.JSONField(default=dict, help_text="Data collected at this step")
    time_spent_seconds = models.IntegerField(default=0, help_text="Time spent on this step")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Onboarding Snapshot"
        verbose_name_plural = "Onboarding Snapshots"

    def __str__(self):
        return f"{self.user.email} - Step {self.step}"
