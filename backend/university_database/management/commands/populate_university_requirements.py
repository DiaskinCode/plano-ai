from django.core.management.base import BaseCommand

from university_database.models import University


class Command(BaseCommand):
    help = "Populate university-specific education requirements"

    def handle(self, *args, **options):
        """
        Populate education_requirements field for universities with specific requirements.

        This adds university-specific overrides of country-level requirements.
        """

        # Get all universities
        universities = University.objects.all()

        updated_count = 0

        for uni in universities:
            requirements = {}
            short_name = uni.short_name.lower()
            country = uni.location_country.lower()

            # USA UNIVERSITIES - Generally 12-year system
            if country == "united states":
                requirements = {
                    "education_system": "12-year (High School Diploma)",
                    "foundation_required": False,
                    "min_gpa": self._get_us_gpa_requirement(short_name),
                    "required_tests": self._get_us_test_requirements(short_name),
                    "test_optional": self._is_us_test_optional(short_name),
                    "language_requirement": "TOEFL 80+ / IELTS 6.5+ / Duolingo 105+",
                    "application_system": "Common App"
                    if self._uses_common_app(short_name)
                    else "Coalition App / Direct",
                }

            # UK UNIVERSITIES - 13-year or IB, foundation for 11-year
            elif country == "united kingdom":
                requirements = {
                    "education_system": "13-year (A-Levels) or IB Diploma",
                    "foundation_required": True,  # For international students with 11-year
                    "foundation_duration": "1 year",
                    "min_gpa": self._get_uk_gpa_requirement(short_name),
                    "required_tests": ["A-Levels", "IB"],
                    "language_requirement": self._get_uk_language_requirement(
                        short_name
                    ),
                    "application_system": "UCAS",
                    "special_notes": "A-Levels or IB required for direct entry. Foundation year available for international students.",
                }

            # ITALY UNIVERSITIES - 12-year required, foundation for 11-year
            elif country == "italy":
                requirements = {
                    "education_system": "12-year or IB Diploma",
                    "foundation_required": True,  # For 11-year system students
                    "foundation_duration": "1 year (or 2 semesters)",
                    "min_gpa": 3.0,
                    "required_tests": [],
                    "language_requirement": "IELTS 6.0+ / Italian B2 for Italian-taught",
                    "application_system": "Direct",
                    "special_notes": "Legal translation of documents required. Italian consulate verification may be needed.",
                    "foundation_accepted": True,
                }

            # GERMANY UNIVERSITIES - 13-year Abitur, Studienkolleg for others
            elif country == "germany":
                requirements = {
                    "education_system": "13-year (Abitur)",
                    "foundation_required": True,
                    "foundation_duration": "1 year Studienkolleg",
                    "min_gpa": 2.5,  # German scale
                    "required_tests": [],
                    "language_requirement": "German B2-B3 / English for English-taught programs",
                    "application_system": "uni-assist",
                    "special_notes": "APS certificate required for some countries. Direct admission possible with 3 years university study in home country.",
                    "foundation_accepted": True,
                }

            # NETHERLANDS UNIVERSITIES - 12-year VWO or IB
            elif country == "netherlands":
                requirements = {
                    "education_system": "12-year (VWO) or IB Diploma",
                    "foundation_required": True,
                    "foundation_duration": "1 year",
                    "min_gpa": 3.0,
                    "required_tests": [],
                    "language_requirement": "IELTS 6.0+ / TOEFL 80+",
                    "application_system": "Studielink",
                    "special_notes": "HBO (applied sciences) accepts 11-year with foundation. Research universities require VWO or IB.",
                    "foundation_accepted": True,
                }

            # CANADA UNIVERSITIES - 12-year system
            elif country == "canada":
                requirements = {
                    "education_system": "12-year (High School Diploma)",
                    "foundation_required": False,
                    "min_gpa": self._get_canada_gpa_requirement(short_name),
                    "required_tests": [],
                    "language_requirement": "IELTS 6.5+ / TOEFL 86+",
                    "application_system": "OUAC"
                    if "ontario" in uni.location_state.lower()
                    else "Direct",
                }

            # AUSTRALIA UNIVERSITIES - 12-year system
            elif country == "australia":
                requirements = {
                    "education_system": "12-year (Higher School Certificate)",
                    "foundation_required": False,
                    "min_gpa": 3.0,
                    "required_tests": [],
                    "language_requirement": "IELTS 6.5+ / TOEFL 79+",
                    "application_system": "Direct / State-specific (e.g., VTAC for Victoria)",
                }

            # SWITZERLAND UNIVERSITIES - 12-year Matura
            elif country == "switzerland":
                requirements = {
                    "education_system": "12-year (Swiss Matura)",
                    "foundation_required": True,
                    "foundation_duration": "1 year",
                    "min_gpa": 4.0,  # Swiss scale 1-6
                    "required_tests": [],
                    "language_requirement": "French/German/Italian B2 / English for English programs",
                    "application_system": "Direct",
                }

            # CHINA UNIVERSITIES - 12-year Gaokao
            elif country == "china":
                requirements = {
                    "education_system": "12-year (Gaokao)",
                    "foundation_required": False,
                    "min_gpa": 3.0,
                    "required_tests": ["Gaokao"],
                    "language_requirement": "HSK 5-6 for Chinese-taught / IELTS 6.0+ for English-taught",
                    "application_system": "CUCAS",
                }

            # KAZAKHSTAN - 11-year system (home country)
            elif country == "kazakhstan":
                requirements = {
                    "education_system": "11-year",
                    "foundation_required": False,
                    "min_gpa": 3.0,
                    "required_tests": ["ENT"],
                    "language_requirement": "Varies by program",
                    "application_system": "Direct / Entarak",
                }

            # Default fallback for other countries
            else:
                requirements = {
                    "education_system": "Varies",
                    "foundation_required": False,
                    "min_gpa": 3.0,
                    "required_tests": [],
                    "language_requirement": "IELTS 6.0+ / TOEFL 80+",
                    "application_system": "Direct",
                }

            # Save if we have requirements
            if requirements:
                uni.education_requirements = requirements
                uni.save(update_fields=["education_requirements"])
                updated_count += 1
                self.stdout.write(
                    f"✓ Updated {uni.short_name}: {requirements.get('education_system', 'N/A')}"
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nSuccessfully updated {updated_count} universities with education requirements"
            )
        )

    def _get_us_gpa_requirement(self, short_name: str) -> float:
        """Get minimum GPA requirement for US universities"""
        # Highly selective
        if short_name in [
            "harvard",
            "mit",
            "stanford",
            "princeton",
            "yale",
            "columbia",
            "caltech",
        ]:
            return 3.9
        # Very selective
        elif short_name in [
            "brown",
            "dartmouth",
            "duke",
            "northwestern",
            "chicago",
            "johns_hopkins",
            "vanderbilt",
        ]:
            return 3.7
        # Selective
        elif short_name in [
            "nyu",
            "usc",
            "ucla",
            "berkeley",
            "cornell",
            "rice",
            "wustl",
        ]:
            return 3.5
        # Moderate
        elif short_name in ["boston_university", "tulane", "rochester", "case_western"]:
            return 3.3
        # Default
        else:
            return 3.0

    def _get_us_test_requirements(self, short_name: str) -> list:
        """Get test requirements for US universities"""
        # Test-optional schools (most post-2020)
        test_optional = [
            "harvard",
            "yale",
            "princeton",
            "stanford",
            "mit",
            "columbia",
            "chicago",
            "nyu",
            "ucla",
            "berkeley",
            "usc",
            "brown",
            "dartmouth",
            "cornell",
            "duke",
            "northwestern",
            "vanderbilt",
            "rice",
            "wustl",
        ]

        if short_name in test_optional:
            return []  # Test-optional
        else:
            return ["SAT", "ACT"]  # Required

    def _is_us_test_optional(self, short_name: str) -> bool:
        """Check if US university is test-optional"""
        test_optional = [
            "harvard",
            "yale",
            "princeton",
            "stanford",
            "mit",
            "columbia",
            "chicago",
            "nyu",
            "ucla",
            "berkeley",
            "usc",
            "brown",
            "dartmouth",
            "cornell",
            "duke",
            "northwestern",
            "vanderbilt",
            "rice",
            "wustl",
        ]
        return short_name in test_optional

    def _uses_common_app(self, short_name: str) -> bool:
        """Check if university uses Common App"""
        # Most US universities use Common App
        common_app_exclude = [
            "mit",
            "georgetown",
            "ucla",
            "uc_berkeley",
        ]  # Use their own systems
        return short_name not in common_app_exclude

    def _get_uk_gpa_requirement(self, short_name: str) -> float:
        """Get GPA requirement for UK universities (converted to 4.0 scale)"""
        # Oxford/Cambridge
        if short_name in ["oxford", "cambridge"]:
            return 3.8
        # London universities
        elif "ucl" in short_name or "imperial" in short_name or "lse" in short_name:
            return 3.7
        # Other Russell Group
        elif (
            "king" in short_name
            or "manchester" in short_name
            or "edinburgh" in short_name
        ):
            return 3.5
        # Default
        else:
            return 3.3

    def _get_uk_language_requirement(self, short_name: str) -> str:
        """Get language requirement for UK universities"""
        # Top tier
        if short_name in ["oxford", "cambridge", "imperial", "lse", "ucl"]:
            return "IELTS 7.0-7.5"
        # Standard
        else:
            return "IELTS 6.5"

    def _get_canada_gpa_requirement(self, short_name: str) -> float:
        """Get GPA requirement for Canadian universities"""
        # Top tier
        if short_name in ["toronto", "ubc", "mcgill", "queens"]:
            return 3.5
        # Standard
        else:
            return 3.0
