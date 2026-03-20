"""
Gap-Based Task Generator

Generates tasks specifically tailored to address identified eligibility gaps.
This is the "if X, then Y" logic engine that creates tasks only for things
the user actually needs to do, not generic checklists.

Key Features:
- Education system mismatch → Foundation year tasks
- Language score insufficient → Retake/prep tasks
- GPA too low → Grade improvement/alternative tasks
- Missing tests → Register/prep tasks
- No critical gaps → Standard application tasks
"""

from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Tuple

from django.conf import settings
from django.utils import timezone


class GapBasedTaskGenerator:
    """
    Generates tasks based on identified gaps in user's eligibility profile.

    Unlike generic task generators, this creates ONLY the tasks that address
    specific gaps the user has. If no gaps, it generates standard application tasks.
    """

    def __init__(self):
        """Initialize the gap-based task generator."""
        pass

    def generate_tasks(
        self,
        user_id: int,
        profile: Dict,
        eligibility_report: Dict,
        universities: List[Dict],
        start_date: Optional[date] = None,
    ) -> List[Dict]:
        """
        Generate tasks based on identified gaps.

        Args:
            user_id: User ID for task creation
            profile: User profile dict with education_system, tests_completed, etc.
            eligibility_report: Eligibility report from EligibilityChecker
            universities: List of selected universities
            start_date: Start date for task scheduling (defaults to today)

        Returns:
            List of task dicts ready for Todo model creation
        """
        if start_date is None:
            start_date = timezone.now().date()

        tasks = []

        # 1. CRITICAL GAPS FIRST - Address eligibility blockers
        if eligibility_report.get("critical_gaps"):
            tasks.extend(
                self._generate_critical_gap_tasks(
                    user_id,
                    eligibility_report["critical_gaps"],
                    profile,
                    universities,
                    start_date,
                )
            )

        # 2. UNIVERSITY-SPECIFIC GAPS
        by_university = eligibility_report.get("by_university", {})
        for uni_slug, uni_data in by_university.items():
            if uni_data.get("gaps"):
                tasks.extend(
                    self._generate_university_gap_tasks(
                        user_id,
                        uni_slug,
                        uni_data,
                        profile,
                        start_date,
                    )
                )

        # 3. STANDARD APPLICATION TASKS (only if no critical gaps)
        if not eligibility_report.get("critical_gaps"):
            tasks.extend(
                self._generate_standard_application_tasks(
                    user_id,
                    profile,
                    universities,
                    start_date,
                )
            )

        # Add metadata to all tasks
        for idx, task in enumerate(tasks):
            task["id"] = f"task_{idx + 1}"
            task["user_id"] = user_id
            if "source" not in task:
                task["source"] = "ai_generated"

        return tasks

    def _generate_critical_gap_tasks(
        self,
        user_id: int,
        critical_gaps: List[Dict],
        profile: Dict,
        universities: List[Dict],
        start_date: date,
    ) -> List[Dict]:
        """
        Generate tasks for critical gaps that affect most/all universities.

        Examples:
        - Education system mismatch → Foundation program research & application
        - Language score insufficient → Retake IELTS/TOEFL with timeline
        """
        tasks = []

        for gap in critical_gaps:
            gap_type = gap.get("gap", "").lower()

            # Education System Mismatch
            if (
                "education system" in gap_type
                or "11-year" in gap_type
                or "12-year" in gap_type
            ):
                tasks.extend(
                    self._generate_foundation_tasks(
                        user_id,
                        gap,
                        profile,
                        start_date,
                    )
                )

            # Language Score Insufficient
            elif "language" in gap_type or "ielts" in gap_type or "toefl" in gap_type:
                tasks.extend(
                    self._generate_language_prep_tasks(
                        user_id,
                        gap,
                        profile,
                        start_date,
                    )
                )

            # GPA Issues
            elif "gpa" in gap_type or "grade" in gap_type:
                tasks.extend(
                    self._generate_gpa_improvement_tasks(
                        user_id,
                        gap,
                        profile,
                        start_date,
                    )
                )

            # Missing Tests
            elif "sat" in gap_type or "act" in gap_type or "test" in gap_type:
                tasks.extend(
                    self._generate_test_prep_tasks(
                        user_id,
                        gap,
                        profile,
                        start_date,
                    )
                )

        return tasks

    def _generate_foundation_tasks(
        self,
        user_id: int,
        gap: Dict,
        profile: Dict,
        start_date: date,
    ) -> List[Dict]:
        """
        Generate tasks for foundation pathway.

        Foundation year tasks include:
        - Research foundation programs in target countries
        - Check application deadlines
        - Prepare foundation application
        - Apply for foundation programs
        """
        tasks = []
        affected_unis = gap.get("affected_universities", [])
        solution = gap.get("solution", "")
        timeline = gap.get("timeline", "1 year")

        # Determine target countries from affected universities
        countries = set()
        for uni_ref in affected_unis:
            # Extract country if available
            if isinstance(uni_ref, dict):
                countries.add(uni_ref.get("country", ""))
            elif isinstance(uni_ref, str):
                # Try to infer country from university name/slug
                if "italy" in uni_ref.lower() or "bocconi" in uni_ref.lower():
                    countries.add("Italy")
                elif (
                    "uk" in uni_ref.lower()
                    or "cambridge" in uni_ref.lower()
                    or "oxford" in uni_ref.lower()
                ):
                    countries.add("United Kingdom")

        countries = [c for c in countries if c]

        # Week 1: Research phase
        tasks.extend(
            [
                {
                    "title": "Research foundation programs in target countries",
                    "description": f"Explore foundation options in: {', '.join(countries) if countries else 'target countries'}. Compare programs, duration, costs, and admission requirements.",
                    "category": "Documents",
                    "priority": 3,  # High
                    "estimated_duration_minutes": 120,
                    "scheduled_date": start_date,
                    "task_level": "sub_goal",
                    "energy_level": "medium",
                    "cognitive_load": 3,
                    "task_category": "foundation",
                    "notes": {
                        "gap_type": "education_system",
                        "solution": solution,
                        "timeline": timeline,
                    },
                },
                {
                    "title": "Check foundation program application deadlines",
                    "description": f"Foundation programs have different deadlines than regular admissions. Find deadlines for: {', '.join(countries[:3]) if countries else 'your target programs'}.",
                    "category": "Documents",
                    "priority": 3,
                    "estimated_duration_minutes": 60,
                    "scheduled_date": start_date + timedelta(days=1),
                    "task_level": "action",
                    "energy_level": "low",
                    "cognitive_load": 2,
                    "task_category": "foundation",
                    "notes": {
                        "gap_type": "education_system",
                        "deadline_importance": "Foundation deadlines are often earlier than regular applications",
                    },
                },
                {
                    "title": "Create foundation program comparison spreadsheet",
                    "description": "Track program details: university, duration, cost, location, deadline, acceptance rate, pathway options.",
                    "category": "Documents",
                    "priority": 2,
                    "estimated_duration_minutes": 90,
                    "scheduled_date": start_date + timedelta(days=2),
                    "task_level": "action",
                    "energy_level": "medium",
                    "cognitive_load": 3,
                    "task_category": "foundation",
                },
            ]
        )

        # Week 2-3: Application preparation
        tasks.extend(
            [
                {
                    "title": "Check foundation program admission requirements",
                    "description": "Verify what's needed: transcripts, references, personal statement, English test. Note if any requirements differ from regular admissions.",
                    "category": "Documents",
                    "priority": 3,
                    "estimated_duration_minutes": 90,
                    "scheduled_date": start_date + timedelta(days=7),
                    "task_level": "action",
                    "energy_level": "medium",
                    "cognitive_load": 3,
                    "task_category": "foundation",
                },
                {
                    "title": "Prepare foundation application documents",
                    "description": "Gather transcripts, translate documents if needed, prepare references, draft personal statement for foundation program.",
                    "category": "Documents",
                    "priority": 3,
                    "estimated_duration_minutes": 180,
                    "scheduled_date": start_date + timedelta(days=10),
                    "task_level": "action",
                    "energy_level": "high",
                    "cognitive_load": 4,
                    "task_category": "foundation",
                },
            ]
        )

        # Week 4: Application submission
        tasks.append(
            {
                "title": "Submit foundation program applications",
                "description": f"Apply to selected foundation programs. Timeline: {timeline}. Keep copies of all submissions.",
                "category": "Applications",
                "priority": 3,
                "estimated_duration_minutes": 120,
                "scheduled_date": start_date + timedelta(days=21),
                "task_level": "action",
                "energy_level": "high",
                "cognitive_load": 4,
                "task_category": "foundation",
                "external_url": "",
                "notes": {
                    "tip": "Foundation programs often have rolling admissions - apply early for best chances",
                },
            }
        )

        return tasks

    def _generate_language_prep_tasks(
        self,
        user_id: int,
        gap: Dict,
        profile: Dict,
        start_date: date,
    ) -> List[Dict]:
        """
        Generate tasks for language test improvement.

        Includes:
        - Diagnostic practice test
        - Study plan creation
        - Section-specific prep (Reading, Writing, Listening, Speaking)
        - Practice tests
        - Exam registration
        """
        tasks = []
        solution = gap.get("solution", "")
        affected_unis = gap.get("affected_universities", [])

        # Determine required score from solution
        required_score = "6.5"  # Default IELTS
        if "IELTS" in solution:
            import re

            score_match = re.search(r"IELTS\s*([\d.]+)", solution)
            if score_match:
                required_score = score_match.group(1)

        # Current scores
        current_scores = profile.get("tests_completed", {})
        current_ielts = current_scores.get("ielts", {}).get("score", 0)

        tasks.extend(
            [
                {
                    "title": f"Take IELTS diagnostic practice test",
                    "description": f"Current score: {current_ielts}, Target: {required_score}. Take full-length timed practice test to identify specific weak areas.",
                    "category": "IELTS Prep",
                    "priority": 3,
                    "estimated_duration_minutes": 180,
                    "scheduled_date": start_date,
                    "task_level": "action",
                    "energy_level": "high",
                    "cognitive_load": 4,
                    "task_category": "learning",
                    "notes": {
                        "current_score": current_ielts,
                        "target_score": required_score,
                        "gap": required_score - current_ielts if current_ielps else 0,
                    },
                },
                {
                    "title": f"Create IELTS study plan to reach {required_score}",
                    "description": "Based on diagnostic results, create 4-8 week study plan focusing on weakest sections. Schedule daily practice sessions.",
                    "category": "IELTS Prep",
                    "priority": 3,
                    "estimated_duration_minutes": 60,
                    "scheduled_date": start_date + timedelta(days=1),
                    "task_level": "action",
                    "energy_level": "medium",
                    "cognitive_load": 3,
                    "task_category": "foundation",
                },
                {
                    "title": "Schedule IELTS retake exam date",
                    "description": f"Book IELTS exam allowing 4-8 weeks prep time. Check deadlines for: {', '.join(affected_unis[:3])}. Plan for score release time (3-5 days for computer, 13 days for paper).",
                    "category": "IELTS Prep",
                    "priority": 3,
                    "estimated_duration_minutes": 30,
                    "scheduled_date": start_date + timedelta(days=3),
                    "task_level": "action",
                    "energy_level": "low",
                    "cognitive_load": 2,
                    "task_category": "foundation",
                    "external_url": "https://www.ielts.org/book-test",
                },
            ]
        )

        # Section-specific practice tasks
        sections = [
            ("Reading", 90),
            ("Writing", 90),
            ("Listening", 60),
            ("Speaking", 45),
        ]

        week_offset = 0
        for section, duration in sections:
            for session in range(1, 4):  # 3 sessions per section
                tasks.append(
                    {
                        "title": f"Practice IELTS {section} section (Session {session})",
                        "description": f"Complete {section.lower()} practice exercises. Focus on common question types and time management.",
                        "category": "IELTS Prep",
                        "priority": 2,
                        "estimated_duration_minutes": duration,
                        "scheduled_date": start_date + timedelta(days=7 + week_offset),
                        "task_level": "action",
                        "energy_level": "medium",
                        "cognitive_load": 3,
                        "task_category": "learning",
                    }
                )
                week_offset += 2  # Space out sessions

        # Final practice test
        tasks.append(
            {
                "title": "Take full-length IELTS practice test #2",
                "description": "Timed practice test to measure improvement. Compare with diagnostic results.",
                "category": "IELTS Prep",
                "priority": 3,
                "estimated_duration_minutes": 180,
                "scheduled_date": start_date + timedelta(days=28),
                "task_level": "action",
                "energy_level": "high",
                "cognitive_load": 4,
                "task_category": "learning",
            }
        )

        return tasks

    def _generate_gpa_improvement_tasks(
        self,
        user_id: int,
        gap: Dict,
        profile: Dict,
        start_date: date,
    ) -> List[Dict]:
        """
        Generate tasks for GPA improvement.

        Note: GPA improvement is often NOT feasible in short timeframes.
        These tasks focus on alternative strategies:
        - Highlighting upward grade trend
        - Explaining special circumstances
        - Emphasizing strengths in other areas
        """
        tasks = []
        current_grade_level = profile.get("current_grade_level", "")

        # Only generate improvement tasks if student is still in high school
        if "graduated" in current_grade_level.lower():
            # Alternative strategies for graduated students
            tasks.extend(
                [
                    {
                        "title": "Draft special circumstances explanation (optional)",
                        "description": "If there were valid reasons for lower GPA (illness, family issues, etc.), prepare a brief, professional explanation for additional information section.",
                        "category": "Documents",
                        "priority": 2,
                        "estimated_duration_minutes": 90,
                        "scheduled_date": start_date,
                        "task_level": "action",
                        "energy_level": "medium",
                        "cognitive_load": 3,
                        "task_category": "regular",
                    },
                    {
                        "title": "Identify alternative pathway options",
                        "description": "Research colleges with more flexible GPA requirements, community college transfer pathways, or test-optional policies.",
                        "category": "Documents",
                        "priority": 2,
                        "estimated_duration_minutes": 120,
                        "scheduled_date": start_date + timedelta(days=1),
                        "task_level": "sub_goal",
                        "energy_level": "medium",
                        "cognitive_load": 3,
                        "task_category": "regular",
                    },
                ]
            )
        else:
            # Current student - can still improve
            tasks.extend(
                [
                    {
                        "title": "Set grade improvement goals for current semester",
                        "description": "Identify specific courses where improvement is possible. Create study plan with target grades.",
                        "category": "Documents",
                        "priority": 3,
                        "estimated_duration_minutes": 60,
                        "scheduled_date": start_date,
                        "task_level": "action",
                        "energy_level": "medium",
                        "cognitive_load": 3,
                        "task_category": "learning",
                    },
                    {
                        "title": "Request meeting with teachers for improvement strategies",
                        "description": "Ask teachers for specific feedback and extra credit opportunities in key courses.",
                        "category": "Documents",
                        "priority": 2,
                        "estimated_duration_minutes": 90,
                        "scheduled_date": start_date + timedelta(days=2),
                        "task_level": "action",
                        "energy_level": "high",
                        "cognitive_load": 4,
                        "task_category": "regular",
                    },
                    {
                        "title": "Create daily study schedule for grade improvement",
                        "description": "Dedicate extra time to challenging subjects. Consider tutoring or study groups.",
                        "category": "Documents",
                        "priority": 2,
                        "estimated_duration_minutes": 45,
                        "scheduled_date": start_date + timedelta(days=3),
                        "task_level": "action",
                        "energy_level": "medium",
                        "cognitive_load": 2,
                        "task_category": "foundation",
                    },
                ]
            )

        return tasks

    def _generate_test_prep_tasks(
        self,
        user_id: int,
        gap: Dict,
        profile: Dict,
        start_date: date,
    ) -> List[Dict]:
        """
        Generate tasks for missing standardized tests (SAT/ACT).

        Includes:
        - Research test requirements
        - Register for exam
        - Create study plan
        - Practice tests
        """
        tasks = []
        affected_unis = gap.get("affected_universities", [])

        tasks.extend(
            [
                {
                    "title": "Research SAT/ACT requirements for target universities",
                    "description": f"Check if SAT/ACT is required or optional for: {', '.join(affected_unis[:5])}. Note specific score requirements.",
                    "category": "SAT Prep",
                    "priority": 3,
                    "estimated_duration_minutes": 90,
                    "scheduled_date": start_date,
                    "task_level": "action",
                    "energy_level": "medium",
                    "cognitive_load": 3,
                    "task_category": "foundation",
                },
                {
                    "title": "Take SAT diagnostic practice test",
                    "description": "Establish baseline score. Use official College Board practice test.",
                    "category": "SAT Prep",
                    "priority": 3,
                    "estimated_duration_minutes": 240,
                    "scheduled_date": start_date + timedelta(days=1),
                    "task_level": "action",
                    "energy_level": "high",
                    "cognitive_load": 4,
                    "task_category": "learning",
                },
                {
                    "title": "Register for SAT exam",
                    "description": "Choose test date allowing 8-12 weeks prep time. Consider early registration for preferred location.",
                    "category": "SAT Prep",
                    "priority": 3,
                    "estimated_duration_minutes": 45,
                    "scheduled_date": start_date + timedelta(days=3),
                    "task_level": "action",
                    "energy_level": "low",
                    "cognitive_load": 2,
                    "task_category": "foundation",
                    "external_url": "https://satsuite.collegeboard.org/sat/register",
                },
            ]
        )

        # Weekly practice tests
        for week in range(1, 5):
            tasks.append(
                {
                    "title": f"Complete SAT practice test #{week}",
                    "description": "Full-length timed practice test. Alternate between different test versions.",
                    "category": "SAT Prep",
                    "priority": 2,
                    "estimated_duration_minutes": 240,
                    "scheduled_date": start_date + timedelta(days=7 + (week * 7)),
                    "task_level": "action",
                    "energy_level": "high",
                    "cognitive_load": 4,
                    "task_category": "learning",
                }
            )

            tasks.append(
                {
                    "title": f"Review and analyze SAT practice test #{week}",
                    "description": "Study mistakes, review weak concepts, update study plan.",
                    "category": "SAT Prep",
                    "priority": 2,
                    "estimated_duration_minutes": 120,
                    "scheduled_date": start_date + timedelta(days=8 + (week * 7)),
                    "task_level": "action",
                    "energy_level": "medium",
                    "cognitive_load": 3,
                    "task_category": "learning",
                }
            )

        return tasks

    def _generate_university_gap_tasks(
        self,
        user_id: int,
        uni_slug: str,
        uni_data: Dict,
        profile: Dict,
        start_date: date,
    ) -> List[Dict]:
        """
        Generate tasks for university-specific gaps.

        These are gaps that only affect certain universities, not all of them.
        """
        tasks = []
        gaps = uni_data.get("gaps", [])
        solutions = uni_data.get("solutions", [])

        for gap, solution in zip(gaps, solutions):
            tasks.append(
                {
                    "title": f"Resolve gap for {uni_slug.replace('_', ' ').title()}: {gap}",
                    "description": f"Solution: {solution}",
                    "category": "Documents",
                    "priority": 2,
                    "estimated_duration_minutes": 90,
                    "scheduled_date": start_date + timedelta(days=7),
                    "task_level": "action",
                    "energy_level": "medium",
                    "cognitive_load": 3,
                    "task_category": "regular",
                    "notes": {
                        "university": uni_slug,
                        "gap": gap,
                        "solution": solution,
                    },
                }
            )

        return tasks

    def _generate_standard_application_tasks(
        self,
        user_id: int,
        profile: Dict,
        universities: List[Dict],
        start_date: date,
    ) -> List[Dict]:
        """
        Generate standard application tasks when NO critical gaps exist.

        These are the "normal" application tasks that all students need:
        - Essay writing
        - Recommendation letters
        - Document preparation
        - Application completion
        """
        tasks = []

        # Month 1: Research & Planning
        tasks.extend(
            [
                {
                    "title": "Create university application spreadsheet",
                    "description": "Track deadlines, requirements, essay prompts, and submission status for all universities.",
                    "category": "Documents",
                    "priority": 3,
                    "estimated_duration_minutes": 90,
                    "scheduled_date": start_date,
                    "task_level": "sub_goal",
                    "energy_level": "medium",
                    "cognitive_load": 3,
                    "task_category": "regular",
                },
                {
                    "title": "Research essay prompts for all universities",
                    "description": "Download and organize all personal statement and supplemental essay prompts.",
                    "category": "Documents",
                    "priority": 3,
                    "estimated_duration_minutes": 90,
                    "scheduled_date": start_date + timedelta(days=2),
                    "task_level": "action",
                    "energy_level": "medium",
                    "cognitive_load": 3,
                    "task_category": "regular",
                },
                {
                    "title": "Create application timeline calendar",
                    "description": "Mark all deadlines, test dates, and personal milestones.",
                    "category": "Documents",
                    "priority": 2,
                    "estimated_duration_minutes": 60,
                    "scheduled_date": start_date + timedelta(days=4),
                    "task_level": "action",
                    "energy_level": "low",
                    "cognitive_load": 2,
                    "task_category": "regular",
                },
            ]
        )

        # Month 1-2: Essay Brainstorming & Drafting
        tasks.extend(
            [
                {
                    "title": "Brainstorm personal statement topics",
                    "description": "List 10+ potential stories, experiences, and themes for your personal statement.",
                    "category": "Essays",
                    "priority": 3,
                    "estimated_duration_minutes": 90,
                    "scheduled_date": start_date + timedelta(days=7),
                    "task_level": "action",
                    "energy_level": "medium",
                    "cognitive_load": 3,
                    "task_category": "learning",
                },
                {
                    "title": "Select top 3 personal statement topics",
                    "description": "Evaluate based on uniqueness, impact, authenticity, and alignment with your goals.",
                    "category": "Essays",
                    "priority": 2,
                    "estimated_duration_minutes": 60,
                    "scheduled_date": start_date + timedelta(days=9),
                    "task_level": "action",
                    "energy_level": "medium",
                    "cognitive_load": 3,
                    "task_category": "learning",
                },
                {
                    "title": "Draft personal statement - Version 1",
                    "description": "Write complete first draft. Focus on getting ideas down, not perfection.",
                    "category": "Essays",
                    "priority": 3,
                    "estimated_duration_minutes": 180,
                    "scheduled_date": start_date + timedelta(days=14),
                    "task_level": "action",
                    "energy_level": "high",
                    "cognitive_load": 4,
                    "task_category": "regular",
                },
            ]
        )

        # Month 2: Recommendations
        tasks.extend(
            [
                {
                    "title": "Identify 2-3 teachers for recommendation letters",
                    "description": "Choose teachers who know you well and can speak to your strengths and potential.",
                    "category": "Documents",
                    "priority": 3,
                    "estimated_duration_minutes": 60,
                    "scheduled_date": start_date + timedelta(days=10),
                    "task_level": "action",
                    "energy_level": "low",
                    "cognitive_load": 2,
                    "task_category": "regular",
                },
                {
                    "title": "Prepare recommendation packets for teachers",
                    "description": 'Include resume, transcript, and "brag sheet" to help teachers write strong recommendations.',
                    "category": "Documents",
                    "priority": 2,
                    "estimated_duration_minutes": 90,
                    "scheduled_date": start_date + timedelta(days=12),
                    "task_level": "action",
                    "energy_level": "medium",
                    "cognitive_load": 3,
                    "task_category": "regular",
                },
                {
                    "title": "Formally request recommendation letters",
                    "description": "Provide teachers with deadlines, requirements, and recommendation packets.",
                    "category": "Documents",
                    "priority": 3,
                    "estimated_duration_minutes": 45,
                    "scheduled_date": start_date + timedelta(days=17),
                    "task_level": "action",
                    "energy_level": "medium",
                    "cognitive_load": 2,
                    "task_category": "regular",
                },
            ]
        )

        # Month 2-3: Essay Revision
        tasks.extend(
            [
                {
                    "title": "Revise personal statement - Version 2",
                    "description": "Improve structure, clarity, flow, and impact.",
                    "category": "Essays",
                    "priority": 3,
                    "estimated_duration_minutes": 120,
                    "scheduled_date": start_date + timedelta(days=21),
                    "task_level": "action",
                    "energy_level": "high",
                    "cognitive_load": 4,
                    "task_category": "regular",
                },
                {
                    "title": "Get feedback on personal statement from teacher/mentor",
                    "description": "Request specific feedback on content, structure, and authenticity.",
                    "category": "Essays",
                    "priority": 2,
                    "estimated_duration_minutes": 60,
                    "scheduled_date": start_date + timedelta(days=24),
                    "task_level": "action",
                    "energy_level": "medium",
                    "cognitive_load": 2,
                    "task_category": "regular",
                },
                {
                    "title": "Finalize personal statement",
                    "description": "Incorporate feedback and polish. Proofread for grammar, word choice, and impact.",
                    "category": "Essays",
                    "priority": 3,
                    "estimated_duration_minutes": 120,
                    "scheduled_date": start_date + timedelta(days=28),
                    "task_level": "action",
                    "energy_level": "high",
                    "cognitive_load": 4,
                    "task_category": "regular",
                },
            ]
        )

        # Month 3-4: Supplemental Essays (simplified)
        num_supplemental = len(universities) * 2  # Assume 2 per university
        for i in range(1, min(num_supplemental, 10)):  # Cap at 10
            due_date = start_date + timedelta(days=35 + (i * 5))
            tasks.append(
                {
                    "title": f"Write supplemental essay #{i}",
                    "description": f"Draft and polish supplemental essay.",
                    "category": "Essays",
                    "priority": 2,
                    "estimated_duration_minutes": 120,
                    "scheduled_date": due_date,
                    "task_level": "action",
                    "energy_level": "high",
                    "cognitive_load": 4,
                    "task_category": "regular",
                }
            )

        # Month 4-5: Document Preparation
        tasks.extend(
            [
                {
                    "title": "Request official transcripts from school",
                    "description": "Contact guidance counselor for official transcripts.",
                    "category": "Documents",
                    "priority": 3,
                    "estimated_duration_minutes": 30,
                    "scheduled_date": start_date + timedelta(days=35),
                    "task_level": "action",
                    "energy_level": "low",
                    "cognitive_load": 1,
                    "task_category": "regular",
                },
                {
                    "title": "Create activities resume/CV",
                    "description": "Document all extracurriculars with details, time commitment, and impact.",
                    "category": "Documents",
                    "priority": 2,
                    "estimated_duration_minutes": 120,
                    "scheduled_date": start_date + timedelta(days=38),
                    "task_level": "action",
                    "energy_level": "medium",
                    "cognitive_load": 3,
                    "task_category": "regular",
                },
                {
                    "title": "Prepare portfolio (if applicable)",
                    "description": "Compile art, writing, coding, or other work samples for programs requiring portfolios.",
                    "category": "Portfolio",
                    "priority": 2,
                    "estimated_duration_minutes": 240,
                    "scheduled_date": start_date + timedelta(days=42),
                    "task_level": "action",
                    "energy_level": "high",
                    "cognitive_load": 4,
                    "task_category": "regular",
                },
            ]
        )

        # Month 5-6: Applications
        tasks.extend(
            [
                {
                    "title": "Create Common App account and complete profile",
                    "description": "Set up account, fill out demographics, family info, education, and activities sections.",
                    "category": "Applications",
                    "priority": 3,
                    "estimated_duration_minutes": 120,
                    "scheduled_date": start_date + timedelta(days=50),
                    "task_level": "action",
                    "energy_level": "medium",
                    "cognitive_load": 3,
                    "task_category": "regular",
                },
                {
                    "title": "Complete first university application",
                    "description": "Fill out all sections, upload essays, review and proofread.",
                    "category": "Applications",
                    "priority": 3,
                    "estimated_duration_minutes": 150,
                    "scheduled_date": start_date + timedelta(days=60),
                    "task_level": "action",
                    "energy_level": "high",
                    "cognitive_load": 4,
                    "task_category": "regular",
                },
                {
                    "title": "Submit early applications (if applicable)",
                    "description": "Submit early decision/action applications before deadlines.",
                    "category": "Applications",
                    "priority": 3,
                    "estimated_duration_minutes": 120,
                    "scheduled_date": start_date + timedelta(days=75),
                    "task_level": "action",
                    "energy_level": "high",
                    "cognitive_load": 4,
                    "task_category": "regular",
                },
                {
                    "title": "Submit regular decision applications",
                    "description": "Complete and submit remaining regular decision applications.",
                    "category": "Applications",
                    "priority": 3,
                    "estimated_duration_minutes": 180,
                    "scheduled_date": start_date + timedelta(days=90),
                    "task_level": "action",
                    "energy_level": "high",
                    "cognitive_load": 4,
                    "task_category": "regular",
                },
            ]
        )

        return tasks


# Convenience function for quick task generation
def generate_gap_based_tasks(
    user_id: int,
    profile: Dict,
    eligibility_report: Dict,
    universities: List[Dict],
    start_date: Optional[date] = None,
) -> List[Dict]:
    """
    Quick wrapper for generating gap-based tasks.

    Args:
        user_id: User ID
        profile: User profile dict
        eligibility_report: Eligibility report from EligibilityChecker
        universities: List of university dicts
        start_date: Start date (optional)

    Returns:
        List of task dicts
    """
    generator = GapBasedTaskGenerator()
    return generator.generate_tasks(
        user_id=user_id,
        profile=profile,
        eligibility_report=eligibility_report,
        universities=universities,
        start_date=start_date,
    )
