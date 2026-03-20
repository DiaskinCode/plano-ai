from django.db import models


class University(models.Model):
    """
    Comprehensive university database with all fields needed for recommendations
    """

    # Basic Info
    name = models.CharField(max_length=200)
    short_name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Short identifier for URL matching (e.g., 'mit', 'stanford')",
    )
    location_country = models.CharField(max_length=100)
    location_state = models.CharField(max_length=100, blank=True)
    location_city = models.CharField(max_length=100)

    CAMPUS_TYPE_CHOICES = [
        ("urban", "Urban"),
        ("suburban", "Suburban"),
        ("rural", "Rural"),
    ]
    campus_type = models.CharField(max_length=50, choices=CAMPUS_TYPE_CHOICES)

    INSTITUTION_TYPE_CHOICES = [
        ("public", "Public"),
        ("private", "Private"),
        ("public_private", "Public/Private"),
    ]
    institution_type = models.CharField(max_length=50, choices=INSTITUTION_TYPE_CHOICES)

    SETTING_CHOICES = [
        ("small", "Small (< 5,000)"),
        ("medium", "Medium (5,000 - 15,000)"),
        ("large", "Large (> 15,000)"),
    ]
    setting = models.CharField(max_length=50, choices=SETTING_CHOICES)
    undergraduate_enrollment = models.IntegerField()

    # Admissions Data
    acceptance_rate = models.FloatField(
        help_text="Acceptance rate as percentage (e.g., 5.2 for 5.2%)"
    )
    acceptance_rate_2023 = models.FloatField(null=True, blank=True)

    sat_required = models.BooleanField(default=True)
    sat_optional = models.BooleanField(default=False)
    sat_25th = models.IntegerField(
        null=True, blank=True, help_text="25th percentile SAT score"
    )
    sat_75th = models.IntegerField(
        null=True, blank=True, help_text="75th percentile SAT score"
    )
    sat_avg = models.IntegerField(null=True, blank=True, help_text="Average SAT score")

    act_required = models.BooleanField(default=True)
    act_optional = models.BooleanField(default=False)
    act_25th = models.IntegerField(
        null=True, blank=True, help_text="25th percentile ACT score"
    )
    act_75th = models.IntegerField(
        null=True, blank=True, help_text="75th percentile ACT score"
    )
    act_avg = models.FloatField(null=True, blank=True, help_text="Average ACT score")

    # Application Deadlines
    early_decision_deadline = models.DateField(null=True, blank=True)
    early_action_deadline = models.DateField(null=True, blank=True)
    regular_decision_deadline = models.DateField()
    rolling_admissions = models.BooleanField(default=False)

    # Academic Programs
    popular_majors = models.JSONField(default=list, help_text="List of popular majors")
    all_majors = models.JSONField(
        default=list, help_text="Comprehensive list of all majors offered"
    )
    all_majors_normalized = models.JSONField(
        default=list,
        help_text="Lowercase version of majors for case-insensitive matching",
    )
    strength_programs = models.JSONField(
        default=list, help_text="List of especially strong programs/departments"
    )
    strength_programs_normalized = models.JSONField(
        default=list, help_text="Lowercase version of strength programs for matching"
    )

    # Costs & Financial Aid (CRITICAL)
    tuition_in_state = models.IntegerField(help_text="In-state tuition per year")
    tuition_out_of_state = models.IntegerField(
        help_text="Out-of-state tuition per year"
    )
    room_board = models.IntegerField(help_text="Room and board per year")
    total_cost_per_year = models.IntegerField(help_text="Total cost per year")

    # Aid Information
    need_based_aid = models.BooleanField(
        default=False, help_text="Offers need-based financial aid"
    )
    need_blind = models.BooleanField(
        default=False,
        help_text="Need-blind admissions (does not consider ability to pay)",
    )
    need_aware = models.BooleanField(
        default=False, help_text="Need-aware admissions (considers ability to pay)"
    )
    merit_aid_offered = models.BooleanField(
        default=False, help_text="Offers merit-based scholarships"
    )
    avg_merit_award = models.IntegerField(
        null=True, blank=True, help_text="Average merit scholarship amount"
    )
    full_ride_available = models.BooleanField(
        default=False, help_text="Full-ride scholarships available"
    )

    # International Aid (Critical for trust)
    international_aid = models.BooleanField(
        default=False, help_text="Offers financial aid to international students"
    )
    international_aid_details = models.TextField(
        blank=True, help_text="Details about international student aid policies"
    )
    aid_verified = models.BooleanField(
        default=False, help_text="Aid information has been verified"
    )
    aid_verified_date = models.DateField(null=True, blank=True)
    aid_source = models.CharField(
        max_length=100,
        blank=True,
        help_text="Source of aid data (e.g., common_data_set, website)",
    )

    # Rankings (Simplified - MVP: Keep only 1-2 sources)
    us_news_ranking = models.IntegerField(null=True, blank=True)

    # Campus Characteristics
    RESEARCH_INTENSITY_CHOICES = [
        ("very_high", "Very High (R1)"),
        ("high", "High (R2)"),
        ("medium", "Medium"),
        ("low", "Low"),
    ]
    research_intensity = models.CharField(
        max_length=20, choices=RESEARCH_INTENSITY_CHOICES, default="medium"
    )
    co_op_programs = models.BooleanField(
        default=False, help_text="Offers cooperative education programs"
    )

    # Special Programs
    honors_program = models.BooleanField(default=False)
    first_year_seminars = models.BooleanField(default=False)

    # Employment Outcomes
    employed_within_6_months = models.FloatField(
        null=True,
        blank=True,
        help_text="Percentage employed within 6 months (as percentage, e.g., 95.0)",
    )
    avg_starting_salary = models.IntegerField(
        null=True, blank=True, help_text="Average starting salary"
    )

    # Images
    logo_url = models.URLField(
        max_length=500,
        blank=True,
        help_text="URL to university logo (Wikipedia or official source)",
    )
    campus_photo_url = models.URLField(
        max_length=500,
        blank=True,
        help_text="URL to campus photo (Wikipedia or official source)",
    )

    # Education Requirements (NEW)
    min_years_of_education = models.IntegerField(
        default=12, help_text="Minimum years of education required"
    )

    education_requirements = models.JSONField(
        default=dict,
        blank=True,
        help_text="University-specific education requirements: {min_gpa: 3.5, required_tests: ['SAT'], foundation_accepted: true, special_notes: '...'}",
    )

    # NEW: Foundation settings for eligibility system
    # PRIORITY: If set, overrides country default. If null, use country default.
    foundation_available = models.BooleanField(
        null=True,
        blank=True,
        help_text="Foundation program available. Null = use country default.",
    )

    foundation_min_years = models.IntegerField(
        null=True,
        blank=True,
        help_text="Minimum education years for foundation eligibility. Null = use country default.",
    )

    # NEW: Structured language requirements
    language_requirement_type = models.CharField(
        max_length=20,
        choices=[
            ("ielts", "IELTS"),
            ("toefl", "TOEFL"),
            ("duolingo", "Duolingo"),
            ("none", "None"),
        ],
        blank=True,
        default="",
        help_text="Primary language test type",
    )

    min_ielts_score = models.FloatField(
        null=True, blank=True, help_text="Minimum IELTS score required"
    )

    min_ielts_reading = models.FloatField(
        null=True, blank=True, help_text="Minimum IELTS Reading score"
    )

    min_ielts_writing = models.FloatField(
        null=True, blank=True, help_text="Minimum IELTS Writing score"
    )

    min_ielts_listening = models.FloatField(
        null=True, blank=True, help_text="Minimum IELTS Listening score"
    )

    min_ielts_speaking = models.FloatField(
        null=True, blank=True, help_text="Minimum IELTS Speaking score"
    )

    ielts_validity_years = models.IntegerField(
        default=2, help_text="How many years IELTS score is valid"
    )

    # NEW: Application portal
    application_portal = models.CharField(
        max_length=50,
        choices=[
            ("common_app", "Common App"),
            ("ucas", "UCAS"),
            ("own_portal", "University Own Portal"),
            ("direct", "Direct Application"),
            ("other", "Other"),
        ],
        blank=True,
        default="",
        help_text="Application portal type",
    )

    application_portal_url = models.URLField(blank=True)

    # NEW: Deadlines with better structure
    regular_deadline = models.DateField(
        null=True, blank=True, help_text="Primary application deadline"
    )

    early_deadline = models.DateField(
        null=True, blank=True, help_text="Early action/decision deadline"
    )

    # NEW: Application requirements (null = use country default)
    essay_required = models.BooleanField(
        null=True, blank=True, help_text="Null = use country default"
    )

    essay_prompt = models.TextField(
        blank=True, help_text="Essay prompt for this university"
    )

    num_recommendations = models.IntegerField(
        null=True,
        blank=True,
        help_text="Number of recommendation letters required. Null = use country default.",
    )

    created_at = models.DateTimeField(auto_now=True)
    updated_at = models.DateTimeField(auto_now=True)
    data_source = models.CharField(
        max_length=100, default="manual", help_text="ipeds, common_data_set, manual"
    )
    last_verified = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = "University"
        verbose_name_plural = "Universities"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["short_name"]),
            models.Index(fields=["location_country"]),
            models.Index(fields=["acceptance_rate"]),
            models.Index(fields=["need_blind", "international_aid"]),
        ]

    def __str__(self):
        return f"{self.short_name} - {self.name}"

    # NEW: Methods for eligibility system
    def get_primary_deadline(self):
        """Get the primary deadline for this university"""
        return self.early_deadline or self.regular_deadline

    def get_foundation_settings(self, country_req_cache=None):
        """
        Get foundation settings with proper priority:
        1. University setting (if set)
        2. Country default (fallback)

        Args:
            country_req_cache: Optional dict {country: CountryRequirement} to avoid N+1 queries
        """
        # Use cache if provided, otherwise query DB
        if country_req_cache:
            country_req = country_req_cache.get(self.location_country)
        else:
            country_req = CountryRequirement.objects.filter(
                country=self.location_country
            ).first()

        if self.foundation_available is not None:
            # University has explicit setting
            return {
                "available": self.foundation_available,
                "min_years": self.foundation_min_years,
                "duration": country_req.foundation_duration_years
                if country_req
                else 1.0,
            }

        # Use country default
        if country_req:
            return {
                "available": country_req.foundation_available,
                "min_years": country_req.foundation_min_years,
                "duration": country_req.foundation_duration_years,
            }

        # No information available
        return {"available": False, "min_years": None, "duration": 1.0}


class CountryRequirement(models.Model):
    """
    Country-specific admission requirements for international students.

    UPDATED: Enhanced for eligibility-first task generation system.
    Stores rules about education systems, foundation requirements, language
    requirements, and default application requirements.
    """

    country = models.CharField(max_length=100, unique=True)

    # Education Requirements
    min_years_of_education = models.IntegerField(
        default=12, help_text="Minimum years of education required"
    )

    # Foundation settings (used as default when university doesn't specify)
    foundation_available = models.BooleanField(
        default=False, help_text="Foundation programs available in this country"
    )

    foundation_min_years = models.IntegerField(
        null=True,
        blank=True,
        help_text="If student has >= this many years, foundation is an option",
    )

    foundation_duration_years = models.FloatField(
        default=1.0, help_text="Typical foundation program duration"
    )

    # Language Requirements
    default_language_test = models.CharField(
        max_length=20,
        choices=[("ielts", "IELTS"), ("toefl", "TOEFL"), ("none", "None")],
        default="ielts",
    )

    default_min_ielts = models.FloatField(default=6.5)

    # Default Application Requirements (used when university doesn't specify)
    default_essay_required = models.BooleanField(default=True)
    default_num_recommendations = models.IntegerField(default=2)

    # Legacy fields (kept for backward compatibility)
    education_system_required = models.CharField(
        max_length=100,
        blank=True,
        help_text="Minimum education system: '12-year', 'IB', 'A-Level', '13-year', etc. (LEGACY)",
    )

    # Foundation/Gap Year Requirements
    foundation_required = models.BooleanField(
        default=False,
        help_text="Whether foundation year is required for students with insufficient education",
    )

    foundation_duration = models.CharField(
        max_length=100,
        blank=True,
        help_text="Duration of foundation: '1 year', '2 semesters', '9 months', etc.",
    )

    # Alternative Pathways
    alternative_paths = models.TextField(
        blank=True,
        help_text="Alternative options if foundation not viable: 'Study in 12-year system country first', etc.",
    )

    # Language Requirements
    language_requirement = models.CharField(
        max_length=100,
        blank=True,
        help_text="Minimum language scores: 'IELTS 6.5', 'TOEFL 80', 'Italian B2', etc.",
    )

    # Country-Specific Rules
    special_rules = models.TextField(
        blank=True,
        help_text="Special procedures: 'Legal translation required', 'Consulate verification', 'UCAS system', etc.",
    )

    # Application System
    application_system = models.CharField(
        max_length=100,
        blank=True,
        help_text="Application platform: 'Common App', 'UCAS', 'Studielink', 'Direct', etc.",
    )

    # Additional Metadata
    notes = models.TextField(
        blank=True, help_text="Additional notes about admission process"
    )

    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Country Requirement"
        verbose_name_plural = "Country Requirements"
        ordering = ["country"]
        indexes = [
            models.Index(fields=["country"]),
            models.Index(fields=["foundation_required"]),
        ]

    def __str__(self):
        return f"{self.country} - {self.education_system_required or 'No specific requirement'}"
