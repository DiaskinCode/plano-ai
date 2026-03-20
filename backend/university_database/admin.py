from django.contrib import admin

from .models import CountryRequirement, University


@admin.register(University)
class UniversityAdmin(admin.ModelAdmin):
    list_display = [
        "short_name",
        "name",
        "location_country",
        "location_city",
        "acceptance_rate",
        "need_blind",
        "international_aid",
        "aid_verified",
    ]
    search_fields = ["name", "short_name", "location_city", "location_state"]
    list_filter = [
        "location_country",
        "campus_type",
        "institution_type",
        "need_blind",
        "international_aid",
        "aid_verified",
        "research_intensity",
    ]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "name",
                    "short_name",
                    "location_country",
                    "location_state",
                    "location_city",
                    "campus_type",
                    "institution_type",
                )
            },
        ),
        (
            "Admissions",
            {
                "fields": (
                    "acceptance_rate",
                    "sat_required",
                    "sat_optional",
                    "sat_25th",
                    "sat_75th",
                    "act_required",
                    "act_optional",
                )
            },
        ),
        (
            "Deadlines",
            {
                "fields": (
                    "early_decision_deadline",
                    "early_action_deadline",
                    "regular_decision_deadline",
                    "rolling_admissions",
                )
            },
        ),
        (
            "Academic Programs",
            {"fields": ("popular_majors", "all_majors", "strength_programs")},
        ),
        (
            "Costs",
            {
                "fields": (
                    "tuition_in_state",
                    "tuition_out_of_state",
                    "room_board",
                    "total_cost_per_year",
                )
            },
        ),
        (
            "Financial Aid",
            {
                "fields": (
                    "need_based_aid",
                    "need_blind",
                    "merit_aid_offered",
                    "avg_merit_award",
                    "full_ride_available",
                )
            },
        ),
        (
            "International Aid",
            {
                "fields": (
                    "international_aid",
                    "international_aid_details",
                    "aid_verified",
                    "aid_verified_date",
                    "aid_source",
                )
            },
        ),
        (
            "Rankings & Outcomes",
            {
                "fields": (
                    "us_news_ranking",
                    "employed_within_6_months",
                    "avg_starting_salary",
                )
            },
        ),
        (
            "Campus & Programs",
            {
                "fields": (
                    "undergraduate_enrollment",
                    "setting",
                    "research_intensity",
                    "co_op_programs",
                    "honors_program",
                )
            },
        ),
        (
            "Education Requirements",
            {
                "fields": ("education_requirements",),
                "description": "University-specific admission requirements: education system, foundation, GPA, tests, language, etc.",
            },
        ),
        (
            "Metadata",
            {"fields": ("data_source", "last_verified", "created_at", "updated_at")},
        ),
    )


@admin.register(CountryRequirement)
class CountryRequirementAdmin(admin.ModelAdmin):
    list_display = [
        "country",
        "education_system_required",
        "foundation_required",
        "language_requirement",
        "application_system",
    ]
    search_fields = ["country"]
    list_filter = ["foundation_required", "application_system"]
    readonly_fields = ["last_updated"]

    fieldsets = (
        (
            "Country & Education System",
            {
                "fields": (
                    "country",
                    "education_system_required",
                    "foundation_required",
                    "foundation_duration",
                )
            },
        ),
        ("Requirements", {"fields": ("language_requirement", "application_system")}),
        ("Special Rules", {"fields": ("special_rules", "alternative_paths", "notes")}),
        ("Metadata", {"fields": ("last_updated",)}),
    )
