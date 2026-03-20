from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

USER_MODEL = settings.AUTH_USER_MODEL


class MentorProfile(models.Model):
    """Extended profile for mentors"""

    # Verification status choices
    VERIFICATION_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('suspended', 'Suspended'),
    ]

    user = models.OneToOneField(
        USER_MODEL, on_delete=models.CASCADE, related_name="mentor_profile"
    )

    # Professional info
    title = models.CharField(max_length=200)  # "Dr. Sarah Chen"
    bio = models.TextField(max_length=1000)
    photo_url = models.URLField(blank=True)
    education = models.CharField(max_length=300, blank=True)

    # Expertise (JSON array)
    expertise_areas = models.JSONField(
        default=list
    )  # ["Essay Writing", "Stanford", "Ivy League"]

    # Business
    hourly_rate_credits = models.IntegerField(default=0)  # Platform credits
    timezone = models.CharField(max_length=63, default="America/New_York")
    meeting_link = models.URLField(blank=True, help_text="Google Meet/Zoom link (V1)")

    # Verification fields
    verification_status = models.CharField(
        max_length=20,
        choices=VERIFICATION_STATUS_CHOICES,
        default='pending',
        db_index=True,
        help_text="Current verification status"
    )
    verification_video_url = models.URLField(
        blank=True,
        help_text="Video introduction URL (YouTube, Vimeo, or Loom)"
    )
    verification_submitted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the profile was first submitted for verification"
    )
    verification_reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When an admin last reviewed this profile"
    )
    verification_notes = models.TextField(
        blank=True,
        help_text="Admin feedback for rejection/suspension"
    )

    # Flagging system for review-based suspension
    flag_count = models.IntegerField(
        default=0,
        help_text="Number of complaints/flags received"
    )
    flagged_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the most recent flag was received"
    )

    # Legacy status fields (kept for backward compatibility)
    is_verified = models.BooleanField(
        default=False,
        help_text="Deprecated: Use verification_status instead"
    )
    is_active = models.BooleanField(default=True)

    # Stats (cached, aggregated from bookings)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    total_sessions = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Mentor Profile"
        verbose_name_plural = "Mentor Profiles"
        indexes = [
            models.Index(fields=["is_verified", "is_active"]),
            models.Index(fields=["rating"]),
            models.Index(fields=["verification_status"]),
            models.Index(fields=["flag_count"]),
            models.Index(fields=["verification_status", "is_active"]),
        ]

    def __str__(self):
        return f"{self.title} - {self.user.email}"


class MentorAvailabilityRule(models.Model):
    """Recurring weekly availability - no slot explosion"""

    mentor = models.ForeignKey(
        MentorProfile, on_delete=models.CASCADE, related_name="availability_rules"
    )

    day_of_week = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(6)]
    )  # 0=Monday, 6=Sunday
    start_minute = models.IntegerField()  # 14:00 = 840
    end_minute = models.IntegerField()  # 16:00 = 960

    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Mentor Availability Rule"
        verbose_name_plural = "Mentor Availability Rules"
        unique_together = ["mentor", "day_of_week", "start_minute"]
        indexes = [
            models.Index(fields=["mentor", "day_of_week", "is_active"]),
        ]

    def clean(self):
        """Validate minute values and prevent overlaps"""
        super().clean()

        # Validate minute range
        if not (0 <= self.start_minute < 1440):
            raise ValidationError({"start_minute": "Must be within 0..1439"})
        if not (0 < self.end_minute <= 1440):
            raise ValidationError({"end_minute": "Must be within 1..1440"})

        # Validate ordering
        if self.start_minute >= self.end_minute:
            raise ValidationError({"start_minute": "Must be < end_minute"})

        # Prevent overlaps for same mentor/day
        overlaps = (
            MentorAvailabilityRule.objects.filter(
                mentor=self.mentor, day_of_week=self.day_of_week, is_active=True
            )
            .exclude(pk=self.pk)
            .filter(start_minute__lt=self.end_minute, end_minute__gt=self.start_minute)
        )

        if overlaps.exists():
            raise ValidationError("This time range overlaps with an existing rule")

    def __str__(self):
        day_names = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]
        return f"{self.mentor.title} - {day_names[self.day_of_week]} {self.start_minute}-{self.end_minute}"


class MentorBooking(models.Model):
    """Session booking - stores actual times, not slots"""

    STATUS_CHOICES = [
        ("requested", "Requested"),
        ("confirmed", "Confirmed"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    DURATION_CHOICES = [(15, "15 min"), (30, "30 min"), (45, "45 min"), (60, "60 min")]

    mentor = models.ForeignKey(
        MentorProfile, on_delete=models.CASCADE, related_name="bookings"
    )
    student = models.ForeignKey(
        USER_MODEL, on_delete=models.CASCADE, related_name="mentor_bookings"
    )

    # Timing (UTC)
    start_at_utc = models.DateTimeField()
    end_at_utc = models.DateTimeField()
    duration_minutes = models.IntegerField(
        choices=DURATION_CHOICES, validators=[MinValueValidator(15)]
    )

    # Session details
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="requested"
    )
    topic = models.CharField(
        max_length=100, blank=True
    )  # "Essay Review", "Plan Validation"
    student_notes = models.TextField(blank=True)

    # Meeting
    meeting_url = models.URLField(blank=True)  # Defaults to mentor.meeting_link

    # Post-session (mentor fills)
    mentor_summary = models.TextField(blank=True)
    action_items = models.JSONField(default=list, blank=True)

    # Post-session (student fills - V1, no separate Review model)
    rating = models.IntegerField(
        null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    review_text = models.TextField(blank=True)

    # Flagging for mentor review
    is_flagged = models.BooleanField(
        default=False,
        help_text="Whether this booking has been flagged for review"
    )
    flag_reason = models.TextField(
        blank=True,
        help_text="Reason for flagging this booking/mentor"
    )
    flagged_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this booking was flagged"
    )

    # Notification tracking
    reminder_sent = models.BooleanField(
        default=False,
        help_text="Whether 15-min reminder notification has been sent"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Mentor Booking"
        verbose_name_plural = "Mentor Bookings"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["mentor", "start_at_utc"]),
            models.Index(fields=["student", "-created_at"]),
            models.Index(fields=["status", "start_at_utc"]),
        ]

    def clean(self):
        """Validate time consistency"""
        super().clean()

        if self.start_at_utc and self.end_at_utc:
            if self.start_at_utc >= self.end_at_utc:
                raise ValidationError({"start_at_utc": "Must be < end_at_utc"})

            # Calculate actual duration from start/end
            delta_minutes = int(
                (self.end_at_utc - self.start_at_utc).total_seconds() / 60
            )

            if self.duration_minutes and delta_minutes != self.duration_minutes:
                raise ValidationError(
                    {
                        "duration_minutes": f"Does not match start/end delta ({delta_minutes} minutes)"
                    }
                )

    def __str__(self):
        return f"{self.mentor.title} - {self.student.email} - {self.start_at_utc}"


class MentorReviewRequest(models.Model):
    """Generic review request for plans AND essays - one unified pipeline"""

    TYPE_CHOICES = [("plan", "Plan Review"), ("essay", "Essay Review")]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("in_review", "In Review"),
        ("done", "Done"),
    ]

    mentor = models.ForeignKey(
        MentorProfile, on_delete=models.CASCADE, related_name="review_requests"
    )
    student = models.ForeignKey(
        USER_MODEL, on_delete=models.CASCADE, related_name="review_requests"
    )

    # What to review
    request_type = models.CharField(max_length=20, choices=TYPE_CHOICES)

    # Generic foreign key - exactly one must be set based on request_type
    goal_spec = models.ForeignKey(
        "users.GoalSpec",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="review_requests",
    )
    essay_project = models.ForeignKey(
        "todos.EssayProject",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="review_requests",
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    # Student's questions (serializer accepts "questions" and maps to this)
    student_questions = models.TextField(blank=True)

    # Cost (optional - V1 may be free)
    price_credits = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Mentor Review Request"
        verbose_name_plural = "Mentor Review Requests"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["mentor", "status"]),
            models.Index(fields=["student", "-created_at"]),
        ]

    def clean(self):
        """Validate exactly one target is set based on request_type"""
        super().clean()

        if self.request_type == "plan":
            if not self.goal_spec:
                raise ValidationError({"goal_spec": "Required for plan reviews"})
            if self.essay_project:
                raise ValidationError(
                    {"essay_project": "Must be null for plan reviews"}
                )

        elif self.request_type == "essay":
            if not self.essay_project:
                raise ValidationError({"essay_project": "Required for essay reviews"})
            if self.goal_spec:
                raise ValidationError({"goal_spec": "Must be null for essay reviews"})

    def __str__(self):
        return f"{self.request_type} request by {self.student.email} to {self.mentor.title}"


class MentorReviewResponse(models.Model):
    """Mentor's structured feedback response

    API accepts human-friendly fields; server normalizes to payload_json internally.
    Mentor is derived from request.mentor (no redundant FK).
    """

    request = models.OneToOneField(
        MentorReviewRequest, on_delete=models.CASCADE, related_name="response"
    )

    # Overall feedback (human field)
    overall_comment = models.TextField()

    # Internal normalized payload (server-generated)
    # Plan: {"verdict": "...", "suggestions": [...], "top_risks": [...], "next_steps": [...]}
    # Essay: {"strengths": [...], "improvements": [...], "rewrite_suggestions": [...], "scores": {...}}
    payload_json = models.JSONField(default=dict)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Mentor Review Response"
        verbose_name_plural = "Mentor Review Responses"
        ordering = ["-created_at"]

    @property
    def mentor(self):
        """Derive mentor from request (no redundant FK)"""
        return self.request.mentor

    def __str__(self):
        return f"Response to {self.request}"
