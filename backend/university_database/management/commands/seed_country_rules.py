from django.core.management.base import BaseCommand

from university_database.models import CountryRequirement


class Command(BaseCommand):
    help = "Seed country admission requirements for eligibility-first task system"

    def handle(self, *args, **options):
        """
        Seed country requirements with new field structure.
        This updates existing CountryRequirement records or creates new ones.
        """

        requirements_data = [
            {
                "country": "United Kingdom",
                "min_years_of_education": 13,
                "foundation_available": True,
                "foundation_min_years": 12,
                "foundation_duration_years": 1.0,
                "default_language_test": "ielts",
                "default_min_ielts": 6.5,
                "default_essay_required": True,
                "default_num_recommendations": 1,
                "special_rules": {"ucas_required": True, "personal_statement": True},
                # Legacy fields (for backward compatibility)
                "education_system_required": "13-year (A-Levels) or IB",
                "foundation_required": True,
                "foundation_duration": "1 year",
                "alternative_paths": "A-Levels via Cambridge International; Foundation programs at universities",
                "language_requirement": "IELTS 6.5-7.5 depending on university",
                "special_rules_text": "UCAS application system; Personal statement required; References required; Interview may be required",
                "application_system": "UCAS",
            },
            {
                "country": "United States",
                "min_years_of_education": 12,
                "foundation_available": False,
                "foundation_min_years": None,
                "foundation_duration_years": 1.0,
                "default_language_test": "ielts",
                "default_min_ielts": 6.5,
                "default_essay_required": True,
                "default_num_recommendations": 2,
                "special_rules": {
                    "common_app": "many",
                    "sat_act_optional": "many_2025",
                },
                "education_system_required": "12-year (High School Diploma)",
                "foundation_required": False,
                "foundation_duration": "",
                "alternative_paths": "None generally",
                "language_requirement": "TOEFL 80+ / IELTS 6.5+ / Duolingo 105+",
                "special_rules_text": "Common App or Coalition App; SAT/ACT often optional but recommended; Early Decision/Early Action available",
                "application_system": "Common App, Coalition App, or Direct",
            },
            {
                "country": "Italy",
                "min_years_of_education": 12,
                "foundation_available": True,
                "foundation_min_years": 11,
                "foundation_duration_years": 1.0,
                "default_language_test": "ielts",
                "default_min_ielts": 6.0,
                "default_essay_required": True,
                "default_num_recommendations": 2,
                "special_rules": {"foundation_path_available": True},
                "education_system_required": "12-year or IB",
                "foundation_required": True,
                "foundation_duration": "1 year (10 months)",
                "alternative_paths": "Study in 12-year system country first, then transfer",
                "language_requirement": "IELTS 6.0+ / Italian B2 for Italian-taught",
                "special_rules_text": "Legal translation of documents required; Italian consulate verification; Pre-enrollment visa required",
                "application_system": "Direct (university-specific)",
            },
            {
                "country": "China",
                "min_years_of_education": 12,
                "foundation_available": False,
                "foundation_min_years": None,
                "foundation_duration_years": 1.0,
                "default_language_test": "ielts",
                "default_min_ielts": 6.0,
                "default_essay_required": False,
                "default_num_recommendations": 2,
                "special_rules": {"portal": "university_specific"},
                "education_system_required": "12-year (Gaokao)",
                "foundation_required": False,
                "foundation_duration": "",
                "alternative_paths": "None generally",
                "language_requirement": "HSK 5-6 for Chinese-taught / IELTS/TOEFL for English-taught",
                "special_rules_text": "CUCAS application system; Physical examination required; Visa application (X1/X2)",
                "application_system": "CUCAS",
            },
            {
                "country": "Kazakhstan",
                "min_years_of_education": 11,
                "foundation_available": False,
                "foundation_min_years": None,
                "foundation_duration_years": 1.0,
                "default_language_test": "ielts",
                "default_min_ielts": 6.0,
                "default_essay_required": True,
                "default_num_recommendations": 2,
                "special_rules": {"sat_act_often_required": True},
                "education_system_required": "11-year",
                "foundation_required": False,
                "foundation_duration": "",
                "alternative_paths": "None for local students",
                "language_requirement": "Varies by program (Kazakh/Russian/English)",
                "special_rules_text": "Entarak (ENT) exam for local universities; International applicants need different process",
                "application_system": "Direct (university-specific)",
            },
            {
                "country": "Netherlands",
                "min_years_of_education": 12,
                "foundation_available": True,
                "foundation_min_years": 11,
                "foundation_duration_years": 1.0,
                "default_language_test": "ielts",
                "default_min_ielts": 6.5,
                "default_essay_required": True,
                "default_num_recommendations": 2,
                "special_rules": {"stufiles": True},
                "education_system_required": "12-year (VWO) or IB",
                "foundation_required": True,
                "foundation_duration": "1 year",
                "alternative_paths": "HBO (applied sciences) accepts 11-year with foundation",
                "language_requirement": "IELTS 6.0+ / TOEFL 80+",
                "special_rules_text": "Studielink application system; Numerus Fixus for selection; Motivation letter required",
                "application_system": "Studielink",
            },
            {
                "country": "Germany",
                "min_years_of_education": 13,
                "foundation_available": True,
                "foundation_min_years": 12,
                "foundation_duration_years": 1.0,
                "default_language_test": "ielts",
                "default_min_ielts": 6.5,
                "default_essay_required": True,
                "default_num_recommendations": 2,
                "special_rules": {"aps_certificate_required": True, "uni_assist": True},
                "education_system_required": "13-year (Abitur)",
                "foundation_required": True,
                "foundation_duration": "1 year Studienkolleg + 2 semesters",
                "alternative_paths": "Direct admission with 3 years of university study in home country; Studienkolleg for qualified applicants",
                "language_requirement": "German B2-B3 for German-taught / IELTS 6.5+ for English-taught",
                "special_rules_text": "APS certificate required from German embassy; uni-assist application; Some states have semester fee",
                "application_system": "Uni-Assist (for public universities)",
            },
        ]

        created_count = 0
        updated_count = 0

        self.stdout.write("🌍 Seeding country requirements...\n\n")

        for data in requirements_data:
            # Prepare defaults with JSON serialization for special_rules
            defaults = {
                "min_years_of_education": data["min_years_of_education"],
                "foundation_available": data["foundation_available"],
                "foundation_min_years": data["foundation_min_years"],
                "foundation_duration_years": data["foundation_duration_years"],
                "default_language_test": data["default_language_test"],
                "default_min_ielts": data["default_min_ielts"],
                "default_essay_required": data["default_essay_required"],
                "default_num_recommendations": data["default_num_recommendations"],
                # Convert special_rules dict to JSON
                "special_rules": data["special_rules"],
                # Legacy fields
                "education_system_required": data.get("education_system_required", ""),
                "foundation_required": data["foundation_required"],
                "foundation_duration": data.get("foundation_duration", ""),
                "alternative_paths": data.get("alternative_paths", ""),
                "language_requirement": data.get("language_requirement", ""),
                "special_rules_text": data.get("special_rules_text", ""),
                "application_system": data.get("application_system", ""),
            }

            # Only include fields that actually exist in the model
            valid_fields = {
                "min_years_of_education",
                "foundation_available",
                "foundation_min_years",
                "foundation_duration_years",
                "default_language_test",
                "default_min_ielts",
                "default_essay_required",
                "default_num_recommendations",
                "special_rules",
                "education_system_required",
                "foundation_required",
                "foundation_duration",
                "alternative_paths",
                "language_requirement",
                "special_rules_text",
                "application_system",
            }

            # Filter to only include fields that exist
            filtered_defaults = {k: v for k, v in defaults.items() if k in valid_fields}

            obj, created = CountryRequirement.objects.get_or_create(
                country=data["country"],
                defaults=filtered_defaults,
            )

            if created:
                created_count += 1
                self.stdout.write(f"✅ Created: {obj.country}\n")
            else:
                updated_count += 1
                self.stdout.write(f"🔄 Updated: {obj.country}\n")

        self.stdout.write(
            f"\n✅ Done! Created {created_count} new, updated {updated_count} existing.\n"
        )
