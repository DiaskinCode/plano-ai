"""
AI Plan Generator Service

Generates personalized 8-month college application plans with 200+ atomic tasks.

Key Features:
- Milestone-based planning (8 months)
- 200+ atomic tasks broken down from application goals
- Personalized based on target universities, exam dates, and student profile
- Categorized task types (Documents, Essays, Test Prep, etc.)
- Time estimates and priority levels
- Dependencies and sequencing
- ELIGIBILITY-AWARE: Uses gap-based task generation when eligibility issues exist
"""

import json
from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Tuple


class PlanGenerator:
    """
    AI-powered college application plan generator.
    """

    def __init__(self):
        """Initialize the plan generator."""
        pass

    def generate_plan(
        self,
        student_profile: Dict,
        target_universities: List[Dict],
        plan_options: Dict,
        eligibility_report: Optional[Dict] = None,
    ) -> Dict:
        """
        Generate a comprehensive 8-month application plan.

        Args:
            student_profile: Dict with academic data, test scores, activities
            target_universities: List of selected universities with categories
            plan_options: Dict with keys:
                - include_timeline: bool
                - include_tasks: bool
                - include_milestones: bool
                - start_date: str (ISO format)
                - exam_types: List[str] (SAT, ACT, IELTS, etc.)
            eligibility_report: Optional eligibility report from EligibilityChecker
                If provided and critical gaps exist, generates gap-based tasks

        Returns:
            Dict with generated plan structure
        """
        # Extract key data
        start_date = datetime.fromisoformat(
            plan_options.get("start_date", datetime.now().isoformat())
        )
        include_timeline = plan_options.get("include_timeline", True)
        include_tasks = plan_options.get("include_tasks", True)
        include_milestones = plan_options.get("include_milestones", True)

        # Determine plan scope
        has_university_apps = any(
            u.get("category") in ["reach", "target", "safety"]
            for u in target_universities
        )
        has_exam_prep = len(plan_options.get("exam_types", [])) > 0
        has_language_tests = any(
            t in ["IELTS", "TOEFL", "DELF", "HSK"]
            for t in plan_options.get("exam_types", [])
        )

        # NEW: Check for eligibility gaps
        has_critical_gaps = (
            eligibility_report is not None
            and len(eligibility_report.get("critical_gaps", [])) > 0
        )

        # Generate milestones (8-month timeline)
        milestones = []
        if include_milestones:
            milestones = self._generate_milestones(
                start_date,
                has_university_apps,
                has_exam_prep,
                has_language_tests,
                eligibility_report,  # NEW: Pass eligibility report
            )

        # Generate tasks
        tasks = []
        if include_tasks:
            # NEW: Use gap-based task generator if eligibility report provided
            if eligibility_report is not None:
                from todos.gap_based_generator import GapBasedTaskGenerator

                gap_generator = GapBasedTaskGenerator()
                tasks = gap_generator.generate_tasks(
                    user_id=student_profile.get("user_id", 0),
                    profile=student_profile,
                    eligibility_report=eligibility_report,
                    universities=target_universities,
                    start_date=start_date.date(),
                )
            else:
                # Fallback to standard task generation
                tasks = self._generate_all_tasks(
                    student_profile,
                    target_universities,
                    plan_options,
                    milestones,
                )

        # Calculate estimates
        total_tasks = len(tasks)
        estimated_hours = sum(t.get("estimated_minutes", 0) for t in tasks) / 60

        return {
            "start_date": start_date.isoformat(),
            "end_date": (start_date + timedelta(days=240)).isoformat(),  # 8 months
            "total_months": 8,
            "total_tasks": total_tasks,
            "estimated_total_hours": round(estimated_hours, 1),
            "milestones": milestones,
            "tasks": tasks,
            "eligibility_report": eligibility_report,  # NEW: Include in response
            "has_critical_gaps": has_critical_gaps,  # NEW: Flag for frontend
            "summary": self._generate_summary(
                student_profile, target_universities, tasks
            ),
        }

    def _generate_milestones(
        self,
        start_date: datetime,
        has_university_apps: bool,
        has_exam_prep: bool,
        has_language_tests: bool,
        eligibility_report: Optional[Dict] = None,
    ) -> List[Dict]:
        """
        Generate 8-month milestone timeline.

        Returns list of monthly milestones with key deliverables.

        NEW: If eligibility_report provided with critical gaps, generates
        eligibility-focused milestones first (foundation, language prep, etc.)
        """
        milestones = []

        # NEW: Check if we have critical eligibility gaps
        has_critical_gaps = (
            eligibility_report is not None
            and len(eligibility_report.get("critical_gaps", [])) > 0
        )

        if has_critical_gaps:
            # Generate eligibility-focused milestones
            milestones.extend(
                self._generate_eligibility_milestones(eligibility_report, start_date)
            )

        # Month 1: Foundation & Assessment
        milestones.append(
            {
                "month": 1,
                "title": "Foundation & Assessment"
                if not has_critical_gaps
                else "Complete Foundation Tasks",
                "focus": "Research, planning, and initial preparations",
                "deliverables": [
                    "Finalize university list (8-12 schools)",
                    "Create application spreadsheet",
                    "Research application requirements",
                    "Start test prep timeline"
                    if not has_critical_gaps
                    else "Complete eligibility requirements",
                ],
                "priority_tasks": 15,
                "is_eligibility_milestone": False,
            }
        )

        # Month 2: Test Prep Intensification
        if has_exam_prep or has_language_tests:
            milestones.append(
                {
                    "month": 2,
                    "title": "Test Preparation",
                    "focus": "Intensive test preparation",
                    "deliverables": [
                        "Complete 4+ practice tests",
                        "Improve score by 100+ points",
                        "Register for upcoming exams",
                        "Start vocabulary building",
                    ],
                    "priority_tasks": 25,
                }
            )
        else:
            milestones.append(
                {
                    "month": 2,
                    "title": "Essay Brainstorming",
                    "focus": "Personal statement and supplemental essays",
                    "deliverables": [
                        "Brainstorm essay topics",
                        "Draft personal statement",
                        "Identify unique stories",
                        "Create essay outline",
                    ],
                    "priority_tasks": 20,
                }
            )

        # Month 3: Essays & Recommendations
        milestones.append(
            {
                "month": 3,
                "title": "Essays & Recommendations",
                "focus": "Drafting essays and securing recommenders",
                "deliverables": [
                    "Complete personal statement draft",
                    "Ask teachers for recommendations",
                    "Start supplemental essays",
                    "Create activities resume",
                ],
                "priority_tasks": 28,
            }
        )

        # Month 4: Application Components
        milestones.append(
            {
                "month": 4,
                "title": "Application Components",
                "focus": "Essays, resumes, and additional materials",
                "deliverables": [
                    "Finalize personal statement",
                    "Complete activity resume",
                    "Draft 5+ supplemental essays",
                    "Prepare portfolio (if applicable)",
                ],
                "priority_tasks": 30,
            }
        )

        # Month 5: Finalizing Materials
        milestones.append(
            {
                "month": 5,
                "title": "Finalizing Materials",
                "focus": "Complete essays and gather documents",
                "deliverables": [
                    "Complete all supplemental essays",
                    "Request transcripts",
                    "Finalize recommenders",
                    "Prepare financial aid forms",
                ],
                "priority_tasks": 32,
            }
        )

        # Month 6: Early Applications
        milestones.append(
            {
                "month": 6,
                "title": "Early Applications",
                "focus": "Submit early decision/action applications",
                "deliverables": [
                    "Submit early applications",
                    "Complete common app",
                    "Submit test scores",
                    "Request fee waivers (if needed)",
                ],
                "priority_tasks": 28,
            }
        )

        # Month 7: Regular Applications
        milestones.append(
            {
                "month": 7,
                "title": "Regular Applications",
                "focus": "Complete and submit regular decision applications",
                "deliverables": [
                    "Submit 5+ regular applications",
                    "Complete remaining essays",
                    "Follow up on recommendations",
                    "Track application status",
                ],
                "priority_tasks": 30,
            }
        )

        # Month 8: Final Steps
        milestones.append(
            {
                "month": 8,
                "title": "Final Steps & Decisions",
                "focus": "Submit final applications and prepare for decisions",
                "deliverables": [
                    "Submit all remaining applications",
                    "Send thank you notes",
                    "Prepare for interviews",
                    "Update grades/test scores",
                ],
                "priority_tasks": 20,
            }
        )

        return milestones

    def _generate_all_tasks(
        self,
        student_profile: Dict,
        target_universities: List[Dict],
        plan_options: Dict,
        milestones: List[Dict],
    ) -> List[Dict]:
        """
        Generate all tasks for the plan.

        Returns comprehensive task list with dependencies and time estimates.
        """
        all_tasks = []

        # Extract data
        exam_types = plan_options.get("exam_types", [])
        has_sat = "SAT" in exam_types
        has_act = "ACT" in exam_types
        has_ielts = "IELTS" in exam_types
        has_toefl = "TOEFL" in exam_types
        has_university_apps = any(
            u.get("category") in ["reach", "target", "safety"]
            for u in target_universities
        )

        # Generate task groups
        if has_university_apps:
            all_tasks.extend(self._generate_research_tasks(target_universities))

        if has_sat or has_act:
            all_tasks.extend(self._generate_test_prep_tasks(exam_types, "sat_act"))

        if has_ielts or has_toefl:
            all_tasks.extend(self._generate_test_prep_tasks(exam_types, "language"))

        all_tasks.extend(
            self._generate_essay_tasks(student_profile, target_universities)
        )
        all_tasks.extend(self._generate_recommendation_tasks(student_profile))
        all_tasks.extend(self._generate_document_tasks())
        all_tasks.extend(self._generate_application_tasks(target_universities))
        all_tasks.extend(self._generate_financial_aid_tasks())
        all_tasks.extend(self._generate_interview_prep_tasks(target_universities))

        # Add metadata to tasks
        for idx, task in enumerate(all_tasks):
            task["id"] = f"task_{idx + 1}"
            task["category"] = self._categorize_task(task)
            task["priority"] = self._determine_priority(task, milestones)

        # Sort by priority and month
        all_tasks.sort(key=lambda t: (t.get("month", 0), -t.get("priority_score", 0)))

        return all_tasks

    def _generate_research_tasks(self, target_universities: List[Dict]) -> List[Dict]:
        """Generate university research tasks."""
        tasks = []

        # Initial research
        tasks.extend(
            [
                {
                    "title": "Research application requirements for all target universities",
                    "description": "Create spreadsheet with deadlines, requirements, and essay prompts",
                    "category": "Documents",
                    "month": 1,
                    "estimated_minutes": 120,
                    "dependencies": [],
                },
                {
                    "title": "Create comprehensive university comparison spreadsheet",
                    "description": "Include location, size, majors, deadlines, costs",
                    "category": "Documents",
                    "month": 1,
                    "estimated_minutes": 90,
                    "dependencies": [],
                },
                {
                    "title": "Research each university's supplement essay prompts",
                    "description": "Download and organize all essay prompts",
                    "category": "Documents",
                    "month": 1,
                    "estimated_minutes": 60,
                    "dependencies": [],
                },
                {
                    "title": "Visit virtual campus tours for top 5 universities",
                    "description": "Take notes on campus culture, facilities, and programs",
                    "category": "Documents",
                    "month": 1,
                    "estimated_minutes": 150,
                    "dependencies": [],
                },
                {
                    "title": "Research specific programs and professors at target schools",
                    "description": "Identify unique programs, research opportunities, and notable faculty",
                    "category": "Documents",
                    "month": 1,
                    "estimated_minutes": 120,
                    "dependencies": [],
                },
                {
                    "title": "Finalize university list to 8-12 schools",
                    "description": "Aim for 3-4 reach, 4-5 target, 2-3 safety schools",
                    "category": "Documents",
                    "month": 1,
                    "estimated_minutes": 60,
                    "dependencies": [],
                },
                {
                    "title": "Create application timeline calendar",
                    "description": "Mark all deadlines, test dates, and application milestones",
                    "category": "Documents",
                    "month": 1,
                    "estimated_minutes": 45,
                    "dependencies": [],
                },
            ]
        )

        # Ongoing research
        for i, uni in enumerate(target_universities[:5]):  # Top 5 schools
            uni_name = uni.get("university_name", f"University {i + 1}")
            tasks.append(
                {
                    "title": f"Deep research on {uni_name}",
                    "description": f"Study {uni_name}'s mission, values, and unique offerings for essays",
                    "category": "Documents",
                    "month": 2,
                    "estimated_minutes": 60,
                    "dependencies": [],
                }
            )

        return tasks

    def _generate_test_prep_tasks(
        self, exam_types: List[str], test_group: str
    ) -> List[Dict]:
        """Generate test preparation tasks."""
        tasks = []

        if test_group == "sat_act":
            # SAT/ACT specific tasks
            base_month = 1

            tasks.extend(
                [
                    {
                        "title": "Take diagnostic SAT practice test",
                        "description": "Timed, full-length practice test to establish baseline",
                        "category": "SAT Prep",
                        "month": base_month,
                        "estimated_minutes": 240,
                        "dependencies": [],
                    },
                    {
                        "title": "Analyze diagnostic test results",
                        "description": "Identify weak areas and create study plan",
                        "category": "SAT Prep",
                        "month": base_month,
                        "estimated_minutes": 60,
                        "dependencies": [],
                    },
                    {
                        "title": "Create SAT study schedule",
                        "description": "Plan daily/weekly study sessions for next 3 months",
                        "category": "SAT Prep",
                        "month": base_month,
                        "estimated_minutes": 45,
                        "dependencies": [],
                    },
                    {
                        "title": "Set up SAT study resources and materials",
                        "description": "Gather prep books, online resources, and practice tests",
                        "category": "SAT Prep",
                        "month": base_month,
                        "estimated_minutes": 30,
                        "dependencies": [],
                    },
                ]
            )

            # Weekly practice tests (Months 2-3)
            for week in range(1, 9):
                tasks.append(
                    {
                        "title": f"Complete SAT practice test #{week}",
                        "description": "Full-length timed practice test",
                        "category": "SAT Prep",
                        "month": 2 if week <= 4 else 3,
                        "estimated_minutes": 240,
                        "dependencies": [],
                    }
                )

                tasks.append(
                    {
                        "title": f"Review and analyze practice test #{week}",
                        "description": "Study mistakes and review weak concepts",
                        "category": "SAT Prep",
                        "month": 2 if week <= 4 else 3,
                        "estimated_minutes": 120,
                        "dependencies": [],
                    }
                )

            # Content-specific study
            for month in range(1, 4):
                tasks.extend(
                    [
                        {
                            "title": f"Study SAT Math concepts (Week 1-{month})",
                            "description": "Focus on algebra, geometry, and advanced math",
                            "category": "SAT Prep",
                            "month": month,
                            "estimated_minutes": 180,
                            "dependencies": [],
                        },
                        {
                            "title": f"Study SAT Reading & Writing (Week 1-{month})",
                            "description": "Practice passages, grammar, and evidence-based questions",
                            "category": "SAT Prep",
                            "month": month,
                            "estimated_minutes": 180,
                            "dependencies": [],
                        },
                    ]
                )

        elif test_group == "language":
            # IELTS/TOEFL tasks
            base_month = 2

            tasks.extend(
                [
                    {
                        "title": "Take IELTS/TOEFL diagnostic test",
                        "description": "Establish baseline score in each section",
                        "category": "IELTS Prep",
                        "month": base_month,
                        "estimated_minutes": 180,
                        "dependencies": [],
                    },
                    {
                        "title": "Create language test study schedule",
                        "description": "Focus on weakest sections first",
                        "category": "IELTS Prep",
                        "month": base_month,
                        "estimated_minutes": 45,
                        "dependencies": [],
                    },
                ]
            )

            # Practice for each section
            for section in ["Reading", "Writing", "Listening", "Speaking"]:
                for week in range(1, 5):
                    tasks.append(
                        {
                            "title": f"Practice {section} section (Session {week})",
                            "description": f"Complete {section.lower()} practice exercises and review",
                            "category": "IELTS Prep",
                            "month": base_month,
                            "estimated_minutes": 90 if section != "Speaking" else 60,
                            "dependencies": [],
                        }
                    )

        return tasks

    def _generate_essay_tasks(
        self,
        student_profile: Dict,
        target_universities: List[Dict],
    ) -> List[Dict]:
        """Generate essay writing tasks."""
        tasks = []

        # Brainstorming phase (Month 2-3)
        tasks.extend(
            [
                {
                    "title": "Brainstorm personal statement topics",
                    "description": "List 10+ potential stories and experiences",
                    "category": "Essays",
                    "month": 2,
                    "estimated_minutes": 90,
                    "dependencies": [],
                },
                {
                    "title": "Select top 3 personal statement topics",
                    "description": "Evaluate based on uniqueness, impact, and authenticity",
                    "category": "Essays",
                    "month": 2,
                    "estimated_minutes": 60,
                    "dependencies": [],
                },
                {
                    "title": "Create essay outline for personal statement",
                    "description": "Structure your narrative with key points and examples",
                    "category": "Essays",
                    "month": 2,
                    "estimated_minutes": 60,
                    "dependencies": [],
                },
                {
                    "title": "Write personal statement first draft",
                    "description": "Focus on getting ideas down, not perfection",
                    "category": "Essays",
                    "month": 2,
                    "estimated_minutes": 180,
                    "dependencies": [],
                },
            ]
        )

        # Drafting phase (Month 3-4)
        tasks.extend(
            [
                {
                    "title": "Revise personal statement - Version 2",
                    "description": "Improve structure, clarity, and flow",
                    "category": "Essays",
                    "month": 3,
                    "estimated_minutes": 120,
                    "dependencies": [],
                },
                {
                    "title": "Get feedback on personal statement from teacher/mentor",
                    "description": "Request specific feedback on content and style",
                    "category": "Essays",
                    "month": 3,
                    "estimated_minutes": 30,
                    "dependencies": [],
                },
                {
                    "title": "Revise personal statement - Version 3",
                    "description": "Incorporate feedback and polish",
                    "category": "Essays",
                    "month": 3,
                    "estimated_minutes": 120,
                    "dependencies": [],
                },
                {
                    "title": "Final polish of personal statement",
                    "description": "Proofread for grammar, word choice, and impact",
                    "category": "Essays",
                    "month": 4,
                    "estimated_minutes": 90,
                    "dependencies": [],
                },
            ]
        )

        # Supplemental essays (Month 4-5)
        # Assume 8 supplemental essays across universities
        for i in range(1, 9):
            tasks.append(
                {
                    "title": f"Brainstorm supplemental essay #{i}",
                    "description": "Review prompt and brainstorm responses",
                    "category": "Essays",
                    "month": 4,
                    "estimated_minutes": 45,
                    "dependencies": [],
                }
            )

            tasks.append(
                {
                    "title": f"Draft supplemental essay #{i}",
                    "description": "Write complete first draft",
                    "category": "Essays",
                    "month": 4 if i <= 4 else 5,
                    "estimated_minutes": 90,
                    "dependencies": [],
                }
            )

            tasks.append(
                {
                    "title": f"Revise and finalize supplemental essay #{i}",
                    "description": "Polish and proofread",
                    "category": "Essays",
                    "month": 5 if i <= 4 else 6,
                    "estimated_minutes": 60,
                    "dependencies": [],
                }
            )

        # Additional essay tasks
        tasks.extend(
            [
                {
                    "title": "Write activities list/resume",
                    "description": "Describe extracurricular activities with impact",
                    "category": "Essays",
                    "month": 3,
                    "estimated_minutes": 120,
                    "dependencies": [],
                },
                {
                    "title": "Write additional information essay (if applicable)",
                    "description": "Explain any gaps, issues, or special circumstances",
                    "category": "Essays",
                    "month": 4,
                    "estimated_minutes": 90,
                    "dependencies": [],
                },
            ]
        )

        return tasks

    def _generate_recommendation_tasks(self, student_profile: Dict) -> List[Dict]:
        """Generate recommendation letter tasks."""
        tasks = []

        tasks.extend(
            [
                {
                    "title": "Identify 2-3 teachers for recommendations",
                    "description": "Choose teachers who know you well and can speak to your strengths",
                    "category": "Documents",
                    "month": 3,
                    "estimated_minutes": 60,
                    "dependencies": [],
                },
                {
                    "title": "Prepare recommendation packets for teachers",
                    "description": "Include resume, transcript, and brag sheet for each teacher",
                    "category": "Documents",
                    "month": 3,
                    "estimated_minutes": 90,
                    "dependencies": [],
                },
                {
                    "title": "Schedule meetings with recommenders",
                    "description": "Discuss your goals and provide context for recommendations",
                    "category": "Documents",
                    "month": 3,
                    "estimated_minutes": 60,
                    "dependencies": [],
                },
                {
                    "title": "Formally request recommendation letters",
                    "description": "Send formal requests with deadlines and requirements",
                    "category": "Documents",
                    "month": 3,
                    "estimated_minutes": 30,
                    "dependencies": [],
                },
                {
                    "title": "Follow up with recommenders (Month 4)",
                    "description": "Check progress and provide any additional information needed",
                    "category": "Documents",
                    "month": 4,
                    "estimated_minutes": 30,
                    "dependencies": [],
                },
                {
                    "title": "Send reminder emails 2 weeks before deadlines",
                    "description": "Gentle reminder about upcoming deadlines",
                    "category": "Documents",
                    "month": 5,
                    "estimated_minutes": 30,
                    "dependencies": [],
                },
                {
                    "title": "Verify recommendation submissions",
                    "description": "Confirm all letters have been submitted",
                    "category": "Documents",
                    "month": 6,
                    "estimated_minutes": 30,
                    "dependencies": [],
                },
                {
                    "title": "Send thank you notes to recommenders",
                    "description": "Express gratitude for their support",
                    "category": "Documents",
                    "month": 7,
                    "estimated_minutes": 45,
                    "dependencies": [],
                },
            ]
        )

        return tasks

    def _generate_document_tasks(self) -> List[Dict]:
        """Generate document preparation tasks."""
        tasks = []

        tasks.extend(
            [
                {
                    "title": "Request official transcripts from school",
                    "description": "Contact guidance counselor for official transcripts",
                    "category": "Documents",
                    "month": 4,
                    "estimated_minutes": 30,
                    "dependencies": [],
                },
                {
                    "title": "Create activities resume/CV",
                    "description": "Document all extracurriculars with details and time commitments",
                    "category": "Portfolio",
                    "month": 3,
                    "estimated_minutes": 120,
                    "dependencies": [],
                },
                {
                    "title": "Prepare portfolio (if applicable to your major)",
                    "description": "Compile art, writing, coding samples, or other work",
                    "category": "Portfolio",
                    "month": 4,
                    "estimated_minutes": 240,
                    "dependencies": [],
                },
                {
                    "title": "Gather financial documents for aid applications",
                    "description": "Tax returns, income statements, and financial records",
                    "category": "Documents",
                    "month": 4,
                    "estimated_minutes": 60,
                    "dependencies": [],
                },
                {
                    "title": "Prepare list of extracurricular activities with descriptions",
                    "description": "150 characters max for each activity description",
                    "category": "Documents",
                    "month": 3,
                    "estimated_minutes": 90,
                    "dependencies": [],
                },
            ]
        )

        return tasks

    def _generate_application_tasks(
        self, target_universities: List[Dict]
    ) -> List[Dict]:
        """Generate application submission tasks."""
        tasks = []

        # Common App setup
        tasks.extend(
            [
                {
                    "title": "Create Common App account",
                    "description": "Set up account and complete profile section",
                    "category": "Applications",
                    "month": 4,
                    "estimated_minutes": 60,
                    "dependencies": [],
                },
                {
                    "title": "Complete Common App general information",
                    "description": "Fill out demographics, family info, and education",
                    "category": "Applications",
                    "month": 4,
                    "estimated_minutes": 90,
                    "dependencies": [],
                },
                {
                    "title": "Complete Common App activities section",
                    "description": "Enter all extracurricular activities with details",
                    "category": "Applications",
                    "month": 4,
                    "estimated_minutes": 120,
                    "dependencies": [],
                },
                {
                    "title": "Complete Common App writing section",
                    "description": "Upload personal statement and additional info",
                    "category": "Applications",
                    "month": 5,
                    "estimated_minutes": 60,
                    "dependencies": [],
                },
            ]
        )

        # University-specific applications
        for i, uni in enumerate(target_universities[:8]):  # Up to 8 universities
            uni_name = uni.get("university_name", f"University {i + 1}")

            tasks.append(
                {
                    "title": f"Complete {uni_name} specific application",
                    "description": "Fill out school-specific sections and supplements",
                    "category": "Applications",
                    "month": 5,
                    "estimated_minutes": 90,
                    "dependencies": [],
                }
            )

            tasks.append(
                {
                    "title": f"Review and proofread {uni_name} application",
                    "description": "Double-check all information before submission",
                    "category": "Applications",
                    "month": 5 if i < 4 else 6,
                    "estimated_minutes": 45,
                    "dependencies": [],
                }
            )

            tasks.append(
                {
                    "title": f"Submit {uni_name} application",
                    "description": "Pay fee and submit application",
                    "category": "Applications",
                    "month": 6 if i < 4 else 7,
                    "estimated_minutes": 30,
                    "dependencies": [],
                }
            )

        # Post-submission tasks
        tasks.extend(
            [
                {
                    "title": "Verify all applications were submitted successfully",
                    "description": "Check confirmation emails and portal access",
                    "category": "Applications",
                    "month": 7,
                    "estimated_minutes": 45,
                    "dependencies": [],
                },
                {
                    "title": "Send official test scores to all universities",
                    "description": "Order score reports from College Board/ACT",
                    "category": "Applications",
                    "month": 6,
                    "estimated_minutes": 60,
                    "dependencies": [],
                },
            ]
        )

        return tasks

    def _generate_financial_aid_tasks(self) -> List[Dict]:
        """Generate financial aid application tasks."""
        tasks = []

        tasks.extend(
            [
                {
                    "title": "Research financial aid options for each university",
                    "description": "Understand need-based vs merit-based aid opportunities",
                    "category": "Documents",
                    "month": 3,
                    "estimated_minutes": 120,
                    "dependencies": [],
                },
                {
                    "title": "Create CSS Profile account",
                    "description": "Set up account for institutional aid applications",
                    "category": "Documents",
                    "month": 4,
                    "estimated_minutes": 45,
                    "dependencies": [],
                },
                {
                    "title": "Complete CSS Profile",
                    "description": "Fill out financial information for institutional aid",
                    "category": "Documents",
                    "month": 4,
                    "estimated_minutes": 90,
                    "dependencies": [],
                },
                {
                    "title": "Complete FAFSA (if US citizen/permanent resident)",
                    "description": "Federal financial aid application",
                    "category": "Documents",
                    "month": 4,
                    "estimated_minutes": 60,
                    "dependencies": [],
                },
                {
                    "title": "Research and apply for outside scholarships",
                    "description": "Identify 10+ scholarship opportunities",
                    "category": "Documents",
                    "month": 5,
                    "estimated_minutes": 180,
                    "dependencies": [],
                },
                {
                    "title": "Complete 5 scholarship applications",
                    "description": "Apply for external scholarships to reduce costs",
                    "category": "Documents",
                    "month": 6,
                    "estimated_minutes": 300,
                    "dependencies": [],
                },
            ]
        )

        return tasks

    def _generate_interview_prep_tasks(
        self, target_universities: List[Dict]
    ) -> List[Dict]:
        """Generate interview preparation tasks."""
        tasks = []

        # Some universities offer interviews
        tasks.extend(
            [
                {
                    "title": "Research which universities offer interviews",
                    "description": "Check interview requirements and sign-up processes",
                    "category": "Documents",
                    "month": 5,
                    "estimated_minutes": 60,
                    "dependencies": [],
                },
                {
                    "title": "Prepare for college interviews",
                    "description": "Practice common interview questions and answers",
                    "category": "Documents",
                    "month": 6,
                    "estimated_minutes": 120,
                    "dependencies": [],
                },
                {
                    "title": "Schedule alumni interviews (if offered)",
                    "description": "Contact alumni interviewers and schedule sessions",
                    "category": "Documents",
                    "month": 6,
                    "estimated_minutes": 60,
                    "dependencies": [],
                },
                {
                    "title": "Complete mock interviews with teacher/mentor",
                    "description": "Practice interview skills with feedback",
                    "category": "Documents",
                    "month": 6,
                    "estimated_minutes": 90,
                    "dependencies": [],
                },
            ]
        )

        return tasks

    def _categorize_task(self, task: Dict) -> str:
        """Determine task category based on title and description."""
        title = task.get("title", "").lower()

        if "sat" in title or "act" in title or "test" in title or "practice" in title:
            if "iel" in title or "toefl" in title:
                return "IELTS Prep"
            return "SAT Prep"
        elif (
            "essay" in title or "personal statement" in title or "supplemental" in title
        ):
            return "Essays"
        elif "recommendation" in title or "transcript" in title or "resume" in title:
            return "Documents"
        elif "application" in title or "submit" in title or "common app" in title:
            return "Applications"
        elif "portfolio" in title:
            return "Portfolio"
        elif "scholarship" in title or "financial" in title or "aid" in title:
            return "Documents"
        elif "interview" in title:
            return "Documents"
        else:
            return "Documents"

    def _determine_priority(
        self, task: Dict, milestones: List[Dict]
    ) -> Tuple[str, int]:
        """
        Determine task priority level and score.

        Returns: (priority_level, priority_score)
        - priority_level: 'high', 'medium', 'low'
        - priority_score: 1-100 for sorting
        """
        month = task.get("month", 1)
        title = task.get("title", "").lower()

        # Base score decreases with later months
        base_score = max(100 - (month * 10), 20)

        # Boost critical tasks
        if any(
            word in title
            for word in ["submit", "deadline", "final", "complete application"]
        ):
            base_score += 20
        elif any(word in title for word in ["draft", "first version", "brainstorm"]):
            base_score -= 10

        # Determine level
        if base_score >= 70:
            level = "high"
        elif base_score >= 50:
            level = "medium"
        else:
            level = "low"

        return (level, base_score)

    def _generate_eligibility_milestones(
        self,
        eligibility_report: Dict,
        start_date: datetime,
    ) -> List[Dict]:
        """
        Generate eligibility-focused milestones for users with critical gaps.

        These milestones come FIRST and address:
        - Foundation program research and application
        - Language test preparation and retakes
        - GPA improvement strategies
        - Missing standardized tests
        """
        milestones = []
        critical_gaps = eligibility_report.get("critical_gaps", [])

        # Analyze gap types
        gap_types = set()
        for gap in critical_gaps:
            gap_lower = gap.get("gap", "").lower()
            if "education system" in gap_lower or "11-year" in gap_lower:
                gap_types.add("foundation")
            elif "language" in gap_lower or "ielts" in gap_lower:
                gap_types.add("language")
            elif "gpa" in gap_lower:
                gap_types.add("gpa")
            elif "sat" in gap_lower or "act" in gap_lower:
                gap_types.add("test")

        # Month 0 (Pre-Month 1): Resolve Eligibility Gaps
        if "foundation" in gap_types:
            milestones.append(
                {
                    "month": 0,
                    "title": "Foundation Program Research & Application",
                    "focus": "Address education system requirements",
                    "deliverables": [
                        "Research foundation programs in target countries",
                        "Compare programs (duration, cost, location)",
                        "Check application deadlines",
                        "Prepare foundation application documents",
                        "Submit foundation applications",
                    ],
                    "priority_tasks": 6,
                    "is_eligibility_milestone": True,
                    "gap_type": "foundation",
                }
            )

        if "language" in gap_types:
            # Get current/target scores if available
            current_score = 0.0
            target_score = 6.5
            for gap in critical_gaps:
                if "ielts" in gap.get("gap", "").lower():
                    solution = gap.get("solution", "")
                    import re

                    score_match = re.search(r"([\d.]+)", solution)
                    if score_match:
                        target_score = float(score_match.group(1))

            milestones.append(
                {
                    "month": 0 if "foundation" not in gap_types else 0.5,
                    "title": "Language Test Preparation",
                    "focus": f"Improve IELTS/TOEFL score to {target_score}",
                    "deliverables": [
                        f"Take diagnostic practice test (Current: {current_score}, Target: {target_score})",
                        "Create 4-8 week study plan",
                        "Schedule retake exam date",
                        "Complete section-specific practice (Reading, Writing, Listening, Speaking)",
                        "Take final practice test and measure improvement",
                    ],
                    "priority_tasks": 8,
                    "is_eligibility_milestone": True,
                    "gap_type": "language",
                }
            )

        if "test" in gap_types:
            milestones.append(
                {
                    "month": 0 if len(gap_types) == 1 else 0.5,
                    "title": "Standardized Test Preparation",
                    "focus": "Prepare for missing SAT/ACT requirements",
                    "deliverables": [
                        "Research SAT/ACT requirements for target universities",
                        "Take diagnostic practice test",
                        "Register for exam",
                        "Complete 4+ practice tests",
                        "Review and improve weak areas",
                    ],
                    "priority_tasks": 7,
                    "is_eligibility_milestone": True,
                    "gap_type": "test",
                }
            )

        if "gpa" in gap_types:
            milestones.append(
                {
                    "month": 0 if len(gap_types) == 1 else 0.5,
                    "title": "Academic Performance Improvement",
                    "focus": "Address GPA concerns and highlight strengths",
                    "deliverables": [
                        "Set grade improvement goals for current semester",
                        "Request meetings with teachers",
                        "Create daily study schedule",
                        "Draft special circumstances explanation (if applicable)",
                        "Research alternative pathway options",
                    ],
                    "priority_tasks": 5,
                    "is_eligibility_milestone": True,
                    "gap_type": "gpa",
                }
            )

        return milestones

    def _generate_summary(
        self,
        student_profile: Dict,
        target_universities: List[Dict],
        tasks: List[Dict],
    ) -> Dict:
        """Generate plan summary with key statistics."""
        # Count tasks by category
        category_counts = defaultdict(int)
        for task in tasks:
            category = task.get("category", "Documents")
            category_counts[category] += 1

        # Count by month
        monthly_counts = defaultdict(int)
        for task in tasks:
            month = task.get("month", 1)
            monthly_counts[month] += 1

        return {
            "total_tasks": len(tasks),
            "tasks_by_category": dict(category_counts),
            "tasks_by_month": dict(monthly_counts),
            "target_university_count": len(target_universities),
            "estimated_weekly_hours": round(
                sum(t.get("estimated_minutes", 0) for t in tasks) / 60 / 32,  # 32 weeks
                1,
            ),
        }


# Convenience function for quick plan generation
def generate_application_plan(
    student_profile: Dict,
    target_universities: List[Dict],
    exam_types: Optional[List[str]] = None,
    start_date: Optional[str] = None,
) -> Dict:
    """
    Quick wrapper for generating application plans.

    Args:
        student_profile: Dict with academic data
        target_universities: List of university dicts with category
        exam_types: List of exam types (optional)
        start_date: ISO format date string (optional, defaults to now)

    Returns:
        Dict with generated plan
    """
    generator = PlanGenerator()

    if exam_types is None:
        exam_types = ["SAT"]

    if start_date is None:
        start_date = datetime.now().isoformat()

    plan_options = {
        "include_timeline": True,
        "include_tasks": True,
        "include_milestones": True,
        "start_date": start_date,
        "exam_types": exam_types,
    }

    return generator.generate_plan(
        student_profile=student_profile,
        target_universities=target_universities,
        plan_options=plan_options,
    )
