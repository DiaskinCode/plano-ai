"""
Eligibility Checker Service

Checks if user meets university/country requirements and identifies gaps.
"""

from typing import Dict, List, Optional, Tuple

from university_database.models import CountryRequirement, University
from university_profile.models import UniversitySeekerProfile


class EligibilityChecker:
    """
    Checks if user meets university/country requirements.

    Analyzes:
    - Education system compatibility (11-year vs 12-year vs IB)
    - Language score sufficiency
    - GPA requirements
    - Foundation year requirements
    - Country-specific rules
    """

    def check_eligibility(
        self, profile: UniversitySeekerProfile, universities: List[University]
    ) -> Dict:
        """
        Main eligibility check method.

        Returns comprehensive eligibility report:
        {
            'overall_status': 'eligible' | 'partially_eligible' | 'not_eligible',
            'by_university': {
                'harvard': {
                    'status': 'eligible',
                    'gaps': [],
                    'missing_requirements': [],
                    'solutions': []
                },
                'bocconi': {
                    'status': 'not_eligible',
                    'gaps': ['11-year system vs 12-year required'],
                    'missing_requirements': ['Foundation year'],
                    'solutions': ['1-year foundation in Italy'],
                    'fastest_path': 'foundation',
                    'timeline': 'Additional 1 year'
                }
            },
            'critical_gaps': [
                {
                    'gap': 'Education system mismatch',
                    'affected_universities': ['bocconi', 'university_of_milan'],
                    'solution': 'Foundation year',
                    'timeline': '1 year'
                }
            ]
        }
        """
        # Get all unique countries from selected universities
        countries = set([u.location_country for u in universities])

        # Get country requirements for all countries
        country_requirements = {}
        for country in countries:
            try:
                req = CountryRequirement.objects.get(country=country)
                country_requirements[country] = req
            except CountryRequirement.DoesNotExist:
                # No specific requirements - assume flexible
                pass

        # Check each university
        by_university = {}
        all_gaps = []
        critical_gaps = []

        for university in universities:
            uni_result = self._check_university(
                profile, university, country_requirements
            )
            by_university[university.short_name] = uni_result

            # Collect critical gaps
            if uni_result["status"] != "eligible":
                all_gaps.extend(uni_result.get("gaps", []))

        # Identify critical gaps (affecting multiple universities)
        gap_counts = {}
        for gap in all_gaps:
            gap_key = gap.get("gap", gap)
            gap_counts[gap_key] = gap_counts.get(gap_key, 0) + 1

        for gap, count in gap_counts.items():
            if count >= 2:  # Affects 2+ universities
                affected_unis = [
                    u.short_name
                    for u in universities
                    if gap
                    in [
                        g.get("gap", g)
                        for g in by_university[u.short_name].get("gaps", [])
                    ]
                ]
                critical_gaps.append(
                    {
                        "gap": gap,
                        "affected_universities": affected_unis,
                        "solution": self._get_gap_solution(gap, country_requirements),
                        "timeline": self._get_gap_timeline(gap),
                    }
                )

        # Determine overall status
        if critical_gaps:
            overall_status = "not_eligible"
        elif any_gaps:
            overall_status = "partially_eligible"
        else:
            overall_status = "eligible"

        return {
            "overall_status": overall_status,
            "by_university": by_university,
            "critical_gaps": critical_gaps,
            "country_requirements": {
                country: {
                    "education_system_required": req.education_system_required,
                    "foundation_required": req.foundation_required,
                    "language_requirement": req.language_requirement,
                    "special_rules": req.special_rules,
                }
                for country, req in country_requirements.items()
            },
        }

    def _check_university(
        self,
        profile: UniversitySeekerProfile,
        university: University,
        country_requirements: Dict[str, CountryRequirement],
    ) -> Dict:
        """Check eligibility for a single university"""
        gaps = []
        missing_requirements = []
        solutions = []
        fastest_path = None
        timeline = None

        # 1. Check education system compatibility
        edu_check = self._check_education_system(
            profile, university, country_requirements.get(university.location_country)
        )
        if edu_check["status"] != "eligible":
            gaps.append(edu_check)
            missing_requirements.extend(edu_check.get("missing_requirements", []))
            solutions.extend(edu_check.get("solutions", []))
            fastest_path = edu_check.get("fastest_path")
            timeline = edu_check.get("timeline")

        # 2. Check language requirements
        language_check = self._check_language_requirements(profile, university)
        if language_check["status"] != "eligible":
            gaps.append(language_check)
            missing_requirements.extend(language_check.get("missing_requirements", []))
            solutions.extend(language_check.get("solutions", []))

        # 3. Check GPA requirements
        gpa_check = self._check_gpa_requirements(profile, university)
        if gpa_check["status"] != "eligible":
            gaps.append(gpa_check)
            missing_requirements.extend(gpa_check.get("missing_requirements", []))
            solutions.extend(gpa_check.get("solutions", []))

        # Determine overall status
        status = "eligible" if not gaps else "not_eligible"

        return {
            "status": status,
            "gaps": gaps,
            "missing_requirements": missing_requirements,
            "solutions": solutions,
            "fastest_path": fastest_path,
            "timeline": timeline,
        }

    def _check_education_system(
        self,
        profile: UniversitySeekerProfile,
        university: University,
        country_requirement: Optional[CountryRequirement],
    ) -> Dict:
        """Check if education system meets requirements"""
        user_system = profile.education_system

        # Parse required system
        required_system = None
        if country_requirement and country_requirement.education_system_required:
            required_system = country_requirement.education_system_required.lower()

        # Check compatibility
        system_compatibility = {
            # User has 11-year
            "11_year": {
                "12_year": False,
                "13_year": False,
                "ib": True,
                "a_level": True,
                "foundation": True,
            },
            # User has 12-year
            "12_year": {
                "12_year": True,
                "13_year": False,
                "ib": True,
                "a_level": True,
                "foundation": False,
            },
            # User has IB
            "ib": {
                "12_year": True,
                "13_year": True,
                "ib": True,
                "a_level": True,
                "foundation": False,
            },
            # User has A-Level
            "a_level": {
                "12_year": True,
                "13_year": True,
                "ib": True,
                "a_level": True,
                "foundation": False,
            },
        }.get(user_system, {})

        # Check if user's system meets requirements
        is_eligible = True
        gap = None
        missing = []
        sols = []
        fastest = None
        tl = None

        if required_system:
            if "12" in required_system and not system_compatibility.get(
                "12_year", False
            ):
                is_eligible = False
                gap = "Education system mismatch"
                missing.append("12-year education required")

                if country_requirement and country_requirement.foundation_required:
                    sols.append(
                        f"Foundation year ({country_requirement.foundation_duration})"
                    )
                    fastest = "foundation"
                    tl = country_requirement.foundation_duration

                    if country_requirement.alternative_paths:
                        sols.append(country_requirement.alternative_paths)

        return {
            "status": "eligible" if is_eligible else "not_eligible",
            "gap": gap,
            "missing_requirements": missing,
            "solutions": sols,
            "fastest_path": fastest,
            "timeline": tl,
        }

    def _check_language_requirements(
        self, profile: UniversitySeekerProfile, university: University
    ) -> Dict:
        """Check if language scores meet requirements"""
        gaps = []
        missing = []
        solutions = []

        # Get university-specific requirements
        uni_requirements = university.education_requirements or {}
        language_req = uni_requirements.get("language_requirement", "")

        # Parse minimum score from requirement string
        min_ielts = 6.0  # Default
        min_toefl = 80  # Default

        if language_req:
            # Parse IELTS requirement
            import re

            ielts_match = re.search(r"IELTS\s*([\d.]+)", language_req)
            if ielts_match:
                min_ielts = float(ielts_match.group(1))

            # Parse TOEFL requirement
            toefl_match = re.search(r"TOEFL\s*(\d+)", language_req)
            if toefl_match:
                min_toefl = int(toefl_match.group(1))

        # Check IELTS if score exists
        tests_completed = profile.tests_completed or {}
        ielts_data = tests_completed.get("ielts", {})
        if ielts_data:
            current_ielts = ielts_data.get("score", 0)
            if current_ielts < min_ielts:
                gaps.append(
                    {
                        "gap": f"IELTS score {current_ielts} below {min_ielts} required",
                        "missing_requirements": [f"IELTS {min_ielts}+"],
                        "solutions": [f"Retake IELTS to achieve {min_ielts}+"],
                    }
                )

        # Check TOEFL if score exists
        toefl_data = tests_completed.get("toefl", {})
        if toefl_data:
            current_toefl = toefl_data.get("score", 0)
            if current_toefl < min_toefl:
                gaps.append(
                    {
                        "gap": f"TOEFL score {current_toefl} below {min_toefl} required",
                        "missing_requirements": [f"TOEFL {min_toefl}+"],
                        "solutions": [f"Retake TOEFL to achieve {min_toefl}+"],
                    }
                )

        return {
            "status": "eligible" if not gaps else "not_eligible",
            "gaps": gaps,
            "missing_requirements": missing,
            "solutions": solutions,
        }

    def _check_gpa_requirements(
        self, profile: UniversitySeekerProfile, university: University
    ) -> Dict:
        """Check if GPA meets minimum requirements"""
        gaps = []
        missing = []
        solutions = []

        # Get min GPA from university requirements if available
        uni_requirements = university.education_requirements or {}
        min_gpa = uni_requirements.get("min_gpa")

        if min_gpa and profile.gpa:
            # Normalize GPA to 4.0 scale if needed
            user_gpa = profile.gpa
            if profile.gpa_scale == "5.0":
                user_gpa = (profile.gpa / 5.0) * 4.0
            elif profile.gpa_scale == "100":
                user_gpa = (profile.gpa / 100.0) * 4.0

            if user_gpa < min_gpa:
                gaps.append(
                    {
                        "gap": f"GPA {profile.gpa} below {min_gpa} required",
                        "missing_requirements": [f"GPA {min_gpa}+"],
                        "solutions": [
                            "Improve academic performance",
                            "Consider test-optional schools",
                        ],
                    }
                )

        return {
            "status": "eligible" if not gaps else "not_eligible",
            "gaps": gaps,
            "missing_requirements": missing,
            "solutions": solutions,
        }

    def _get_gap_solution(self, gap: str, country_requirements: Dict) -> str:
        """Get recommended solution for a gap"""
        if "education system" in gap.lower():
            return "Foundation year"
        elif "language" in gap.lower():
            return "Retake language test"
        elif "gpa" in gap.lower():
            return "Improve grades or consider test-optional"
        return "See guidance counselor"

    def _get_gap_timeline(self, gap: str) -> str:
        """Get timeline to resolve a gap"""
        if "education system" in gap.lower():
            return "1 year"
        elif "language" in gap.lower():
            return "2-3 months"
        elif "gpa" in gap.lower():
            return "1 semester"
        return "Varies"
