from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class UniversitySeekerProfile(models.Model):
    """
    Independent profile for university recommendations.
    Decoupled from onboarding flow - can be created/updated anytime.
    """

    # A. Academic Profile (Structured)
    GPA_SCALE_CHOICES = [
        ("4.0", "4.0 scale"),
        ("5.0", "5.0 scale"),
        ("100", "100 point scale"),
    ]

    COURSE_RIGOR_CHOICES = [
        ("ap_ib_ib_plus", "AP+IB+ (Most Rigorous)"),
        ("ap_ib", "AP or IB"),
        ("honors", "Honors"),
        ("regular", "Regular"),
    ]

    gpa = models.FloatField(help_text="Student's GPA")
    gpa_scale = models.CharField(
        max_length=10, choices=GPA_SCALE_CHOICES, default="4.0"
    )
    sat_score = models.IntegerField(
        null=True, blank=True, help_text="SAT total score (1600 max)"
    )
    sat_english = models.IntegerField(null=True, blank=True)
    sat_math = models.IntegerField(null=True, blank=True)
    act_score = models.IntegerField(
        null=True, blank=True, help_text="ACT composite score (36 max)"
    )
    toefl_score = models.IntegerField(
        null=True, blank=True, help_text="TOEFL score (120 max)"
    )
    ielts_score = models.FloatField(
        null=True, blank=True, help_text="IELTS score (9.0 max)"
    )

    # NEW: IELTS metadata for detailed tracking
    ielts_date = models.DateField(
        null=True, blank=True, help_text="Date IELTS test was taken"
    )

    ielts_type = models.CharField(
        max_length=20,
        choices=[("academic", "Academic"), ("general", "General Training")],
        null=True,
        blank=True,
        help_text="IELTS test type",
    )

    ielts_reading_score = models.FloatField(
        null=True, blank=True, help_text="IELTS Reading score (9.0 max)"
    )

    ielts_writing_score = models.FloatField(
        null=True, blank=True, help_text="IELTS Writing score (9.0 max)"
    )

    ielts_listening_score = models.FloatField(
        null=True, blank=True, help_text="IELTS Listening score (9.0 max)"
    )

    ielts_speaking_score = models.FloatField(
        null=True, blank=True, help_text="IELTS Speaking score (9.0 max)"
    )

    duolingo_score = models.IntegerField(
        null=True, blank=True, help_text="Duolingo English Test (160 max)"
    )

    # Course Rigor
    course_rigor = models.CharField(
        max_length=20, choices=COURSE_RIGOR_CHOICES, default="regular"
    )
    ap_courses = models.JSONField(
        default=list, help_text="List of AP courses with scores"
    )
    ib_courses = models.JSONField(default=list, help_text="List of IB courses")

    # Olympiads/Awards
    academic_competitions = models.JSONField(
        default=list, help_text="List of academic competitions and awards"
    )

    # Education System & Academic Status (NEW)
    EDUCATION_SYSTEM_CHOICES = [
        ("11_year", "11-year system (Russia/CIS)"),
        ("12_year", "12-year system (US/UK)"),
        ("ib", "IB Diploma"),
        ("a_level", "A-Level"),
        ("ap", "AP"),
        ("foundation", "Foundation completed"),
        ("other", "Other"),
    ]

    education_system = models.CharField(
        max_length=50,
        choices=EDUCATION_SYSTEM_CHOICES,
        blank=True,
        default="",
        help_text="Current or completed education system. Empty = not provided",
    )

    GRADE_LEVEL_CHOICES = [
        ("grade_9", "Grade 9"),
        ("grade_10", "Grade 10"),
        ("grade_11", "Grade 11"),
        ("grade_12", "Grade 12"),
        ("graduated", "Graduated"),
        ("gap_year", "Gap Year"),
    ]

    current_grade_level = models.CharField(
        max_length=50,
        choices=GRADE_LEVEL_CHOICES,
        null=True,
        blank=True,
        help_text="Current grade level",
    )

    graduation_year = models.IntegerField(
        null=True, blank=True, help_text="Expected or actual graduation year"
    )

    tests_completed = models.JSONField(
        default=dict,
        blank=True,
        help_text="Completed tests with scores and dates: {sat: {score: 1200, date: '2024-01'}, ielts: {score: 7.0, date: '2024-02'}}",
    )

    # B. Personal/Financial Profile
    country = models.CharField(max_length=100, help_text="Country of residence")
    citizenship = models.CharField(max_length=100, help_text="Citizenship country")
    budget_currency = models.CharField(
        max_length=3, default="USD", help_text="USD, EUR, GBP, etc."
    )
    max_budget = models.IntegerField(
        null=True, blank=True, help_text="Maximum budget per year in currency"
    )

    FINANCIAL_NEED_CHOICES = [
        ("full_ride", "Full ride needed"),
        ("significant", "Significant aid needed"),
        ("moderate", "Moderate aid helpful"),
        ("none", "No aid needed"),
    ]
    financial_need = models.CharField(
        max_length=50, choices=FINANCIAL_NEED_CHOICES, default="none"
    )

    # Aid Preferences
    need_blind_preference = models.BooleanField(
        default=False, help_text="Prefer schools with need-blind admissions"
    )
    merit_aid_required = models.BooleanField(
        default=False, help_text="Require schools with merit aid opportunities"
    )

    # C. Academic Interests
    intended_major_1 = models.CharField(
        max_length=100, help_text="Primary intended major"
    )
    intended_major_2 = models.CharField(
        max_length=100, blank=True, help_text="Secondary intended major"
    )
    intended_major_3 = models.CharField(
        max_length=100, blank=True, help_text="Tertiary intended major"
    )
    academic_interests = models.TextField(
        blank=True, help_text="Free text explaining academic interests and why"
    )

    # D. Campus Preferences
    SIZE_CHOICES = [
        ("small", "Small (< 5,000 students)"),
        ("medium", "Medium (5,000 - 15,000 students)"),
        ("large", "Large (> 15,000 students)"),
    ]
    LOCATION_CHOICES = [
        ("urban", "Urban"),
        ("suburban", "Suburban"),
        ("rural", "Rural"),
    ]

    preferred_size = models.CharField(max_length=50, choices=SIZE_CHOICES, blank=True)
    preferred_location = models.CharField(
        max_length=50, choices=LOCATION_CHOICES, blank=True
    )
    preferred_region = models.CharField(
        max_length=100, blank=True, help_text="northeast, midwest, etc."
    )
    weather_preference = models.CharField(max_length=50, blank=True)

    # E. Constraints & Preferences
    target_countries = models.JSONField(
        default=list,
        help_text="List of countries to target for university applications",
    )
    excluded_universities = models.JSONField(
        default=list, help_text="List of university short_names to exclude"
    )
    test_optional_flexible = models.BooleanField(
        default=False, help_text="Flexible about test-optional schools"
    )
    early_decision_willing = models.BooleanField(
        default=False, help_text="Willing to apply Early Decision"
    )
    early_action_willing = models.BooleanField(
        default=True, help_text="Willing to apply Early Action"
    )

    # F. Spike Factors (Exceptional achievements)
    SPIKE_AREA_CHOICES = [
        ("research_olympiad", "Research/Olympiad"),
        ("athletics", "Athletics (Recruited)"),
        ("arts", "Arts"),
        ("leadership", "Leadership"),
        ("other", "Other"),
    ]

    spike_area = models.CharField(
        max_length=100, choices=SPIKE_AREA_CHOICES, blank=True
    )
    spike_achievement = models.TextField(
        blank=True, help_text="Description of exceptional achievement in spike area"
    )

    # NEW: Additional context for LLM-powered plan personalization
    additional_context = models.TextField(
        blank=True,
        help_text="Additional context, achievements, or circumstances not captured elsewhere (for personalized planning)"
    )

    # NEW: Education path strategy for eligibility system
    education_path_strategy = models.CharField(
        max_length=30,
        blank=True,
        default="",
        choices=[
            ("direct", "Direct Application"),
            ("foundation", "Foundation Year"),
            ("change_shortlist", "Change Shortlist"),
        ],
        help_text="User's chosen path for education system mismatches. Empty = not chosen yet",
    )

    # NEW: Eligibility tracking
    eligibility_checked_at = models.DateTimeField(
        null=True, blank=True, help_text="Last time eligibility was checked"
    )

    overall_eligibility_status = models.CharField(
        max_length=20,
        blank=True,
        default="",
        choices=[
            ("eligible", "Eligible"),
            ("partially_eligible", "Partially Eligible"),
            ("not_eligible", "Not Eligible"),
            ("", "Not Checked"),
        ],
        help_text="Overall eligibility status across shortlist",
    )

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="university_profile"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "University Seeker Profile"
        verbose_name_plural = "University Seeker Profiles"
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.user.email}'s University Profile"

    @property
    def completion_percentage(self):
        """
        Calculate profile completion percentage
        """
        required_fields = [
            self.gpa,
            self.country,
            self.citizenship,
            self.intended_major_1,
            self.education_system,  # NEW
        ]
        required_count = sum(
            1 for field in required_fields if field is not None and field != ""
        )

        optional_fields = [
            self.sat_score,
            self.act_score,
            self.course_rigor,
            self.financial_need,
            self.preferred_size,
            self.preferred_location,
            self.current_grade_level,  # NEW
            self.graduation_year,  # NEW
            self.tests_completed,  # NEW (check if not empty dict)
        ]
        optional_count = 0
        for field in optional_fields:
            if field is not None:
                if isinstance(field, dict) and field:
                    optional_count += 1
                elif not isinstance(field, dict) and field != "":
                    optional_count += 1

        # Required: 5 fields, Optional: 9 fields
        return min(100, int((required_count / 5) * 40 + (optional_count / 9) * 60))


class ExtracurricularActivity(models.Model):
    """
    Student extracurricular activities - separate model for proper data structure
    """

    CATEGORY_CHOICES = [
        ("leadership", "Leadership"),
        ("research", "Research"),
        ("volunteering", "Volunteering"),
        ("sports", "Sports"),
        ("arts", "Arts"),
        ("work", "Work Experience"),
        ("academic", "Academic Club"),
        ("other", "Other"),
    ]

    IMPACT_LEVEL_CHOICES = [
        ("low", "Low - School level only"),
        ("medium", "Medium - Local/District level"),
        ("high", "High - State/Regional level"),
        ("national", "National level"),
        ("international", "International level"),
    ]

    ACHIEVEMENTS_IMPACT_CHOICES = [
        ("school", "School level"),
        ("state", "State/Regional level"),
        ("national", "National level"),
        ("international", "International level"),
    ]

    profile = models.ForeignKey(
        UniversitySeekerProfile,
        on_delete=models.CASCADE,
        related_name="extracurriculars",
    )

    # Basic Info
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    title = models.CharField(max_length=200, help_text="Activity name")
    role = models.CharField(max_length=100, help_text="Student's role/title")

    # Time Commitment
    hours_per_week = models.IntegerField(help_text="Hours spent per week")
    weeks_per_year = models.IntegerField(help_text="Weeks participated per year")
    years_participated = models.IntegerField(help_text="Number of years participated")

    # Impact & Leadership (Critical for LLM assessment)
    impact_level = models.CharField(
        max_length=20, choices=IMPACT_LEVEL_CHOICES, default="medium"
    )
    leadership_position = models.BooleanField(
        default=False,
        help_text="Was this a leadership position? (President, Captain, etc.)",
    )
    achievements = models.TextField(blank=True, help_text="Description of achievements")
    achievements_impact = models.CharField(
        max_length=20,
        choices=ACHIEVEMENTS_IMPACT_CHOICES,
        blank=True,
        help_text="Level of achievements",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Extracurricular Activity"
        verbose_name_plural = "Extracurricular Activities"
        ordering = ["-years_participated", "-hours_per_week"]

    def __str__(self):
        return f"{self.profile.user.email} - {self.title}"
