"""
Milestone Generator (Tier 1 of Two-Tier Task Generation)

Generates 5 high-level milestones for a goal, which will then be broken down
into atomic tasks by the atomic_task_generator.

Phase 2, Day 1: Two-Tier Atomic Task Generation
"""

import json
import logging
from typing import Dict, List, Any
from decimal import Decimal

logger = logging.getLogger(__name__)


class MilestoneGenerator:
    """
    Generates high-level milestones using OpenAI GPT-4o-mini.

    Two-tier approach:
    - Tier 1 (this class): Goal → 5 milestones
    - Tier 2 (atomic_task_generator): Milestone → 5-6 atomic tasks

    Example:
        Goal: "Get into MIT Computer Science Master's"
        →
        Milestones:
        1. Research and shortlist programs (2 weeks)
        2. Prepare strong SOP (2 weeks)
        3. Secure recommendation letters (3 weeks)
        4. Apply to universities (2 weeks)
        5. Interview preparation (3 weeks)
    """

    def __init__(self):
        """Initialize with OpenAI service"""
        from ai.services import AIService

        # Use OpenAI GPT-4o-mini (5-8x cheaper than Claude)
        self.ai_service = AIService(provider='openai')
        logger.info("[MilestoneGenerator] Initialized with GPT-4o-mini")

    def generate_milestones(
        self,
        goalspec,
        user_profile,
        context: Dict[str, Any],
        timeline_weeks: int = 12
    ) -> List[Dict[str, Any]]:
        """
        Generate 5 high-level milestones for the goal.

        Args:
            goalspec: GoalSpec instance
            user_profile: UserProfile instance
            context: Personalization context from profile_extractor
            timeline_weeks: Total weeks to complete goal (default: 12)

        Returns:
            List of 5 milestone dictionaries:
            [
                {
                    "title": "Research and shortlist programs",
                    "description": "Research top CS programs, compare requirements...",
                    "duration_weeks": 2,
                    "success_criteria": "5 programs shortlisted with clear fit rationale"
                },
                ...
            ]
        """
        logger.info(f"[MilestoneGenerator] Generating milestones for: {goalspec.title}")

        # Build comprehensive prompt
        prompt = self._build_milestone_prompt(goalspec, user_profile, context, timeline_weeks)

        # Generate with OpenAI
        try:
            response = self.ai_service.call_llm(
                system_prompt="You are an expert career advisor that generates structured milestone plans in JSON format.",
                user_prompt=prompt,
                response_format="json"  # Force JSON output
            )

            # Parse JSON response
            milestones = self._parse_milestone_response(response)

            if not milestones or len(milestones) < 3:
                logger.warning(f"[MilestoneGenerator] Generated only {len(milestones)} milestones, expected 5")
                return []

            logger.info(f"[MilestoneGenerator] ✅ Generated {len(milestones)} milestones")
            for idx, milestone in enumerate(milestones, 1):
                logger.info(f"  {idx}. {milestone['title']} ({milestone['duration_weeks']} weeks)")

            return milestones

        except Exception as e:
            logger.error(f"[MilestoneGenerator] Failed to generate milestones: {e}")
            return []

    def _build_milestone_prompt(
        self,
        goalspec,
        user_profile,
        context: Dict[str, Any],
        timeline_weeks: int
    ) -> str:
        """Build comprehensive prompt for milestone generation"""

        # Extract key context
        background = context.get('background', 'student')
        field = context.get('field', goalspec.title)
        target_universities = context.get('target_universities', [])
        work_experience = context.get('years_experience', 0)
        gpa = context.get('gpa_raw', 'N/A')

        # Career-specific context (target role, companies)
        target_role = context.get('target_role', 'N/A')
        target_companies = context.get('target_companies_string', context.get('target_companies', 'N/A'))
        current_company = context.get('current_company', 'N/A')
        current_role = context.get('current_role', 'N/A')

        prompt = f"""You are an expert career advisor. Generate a 5-milestone plan for this user's goal.

USER PROFILE:
=============
Background: {background}
Current Status: {context.get('current_status', 'Student')}
Current Company: {current_company}
Current Role: {current_role}
Field: {field}
Goal: {goalspec.title}
Target Role: {target_role}
Target Companies: {target_companies}
Timeline: {timeline_weeks} weeks total
Target Universities: {', '.join(target_universities[:3]) if target_universities else 'Not specified'}
GPA: {gpa}
Work Experience: {work_experience} years
Key Achievements: {context.get('achievements', 'None reported')}
Startup Experience: {context.get('startup_experience', 'None')}
Notable Projects: {context.get('notable_achievements', 'None')}

TASK:
=====
Generate exactly 5 major milestones to achieve this goal in {timeline_weeks} weeks.

Each milestone should be:
1. ✅ A major achievement (not a single task)
2. ✅ Takes 2-4 weeks to complete
3. ✅ Has clear, measurable outcome
4. ✅ Builds logically toward the goal
5. ✅ Specific to THIS user's context (use their background, universities, field)

CRITICAL REQUIREMENTS:
=====================
- MUST reference user's ACTUAL goal details: "{goalspec.title}"
- MUST reference current company: "{current_company}" (if not N/A)
- MUST reference target role: "{target_role}" (if not N/A)
- MUST reference target companies: "{target_companies}" (if not N/A)
- MUST reference current role: "{current_role}" (if not N/A)
- NO generic milestones like "Prepare application materials" or "Update LinkedIn"
- YES specific milestones like "Build Audit Knowledge from Your {current_company} Reporting Base"
- YES specific milestones like "Connect with {target_companies} {target_role}s Who Made Similar Transition"
- Include specific details from user context (companies, roles, background, achievements)
- Milestones should total ~{timeline_weeks} weeks (distribute reasonably)

BAD EXAMPLES (TOO GENERIC):
❌ "Improve resume and LinkedIn"
❌ "Network with professionals"
❌ "Prepare for interviews"

GOOD EXAMPLES (SPECIFIC TO USER):
✅ "Build Audit Knowledge from Your Forte Finance Reporting Experience" (for current_company=Forte Finance, target_role=Auditor)
✅ "Connect with KPMG Auditors Who Made Bank→Audit Transition" (for target_companies=KPMG, current_company=Forte Finance)
✅ "Create Forte Finance→KPMG Audit Transition Story" (uses actual company names)

EXAMPLE FOR "Get into MIT CS Master's" (Student, 3.8 GPA, Founder):
=================================================================
{{
  "milestones": [
    {{
      "title": "Research and shortlist 5 top CS programs with strong systems research",
      "description": "Research MIT, Stanford, CMU, Berkeley, Cornell CS programs. Focus on systems/distributed computing labs that align with startup experience. Create comparison spreadsheet with requirements, deadlines, faculty fit.",
      "duration_weeks": 2,
      "success_criteria": "5 programs shortlisted with clear fit rationale for each"
    }},
    {{
      "title": "Draft compelling SOP highlighting startup scaling challenges and CS fundamentals",
      "description": "Write 800-1000 word Statement of Purpose connecting PathAI's 200k user scaling challenges to interest in distributed systems. Emphasize technical problem-solving from production experience. Tailor for each university's research strengths.",
      "duration_weeks": 3,
      "success_criteria": "Complete SOP draft reviewed by 2 mentors, tailored versions for top 3 schools"
    }},
    {{
      "title": "Secure 3 strong recommendation letters (technical mentor, advisor, investor)",
      "description": "Identify recommenders who can speak to technical skills (CTO mentor), academic potential (CS professor), and leadership (investor). Brief them on application goals and provide context. Follow up to ensure timely submission.",
      "duration_weeks": 3,
      "success_criteria": "3 recommenders confirmed and briefed, letters submitted before deadlines"
    }},
    {{
      "title": "Complete and submit applications to 5 target programs",
      "description": "Finalize all application components (transcripts, test scores, SOP, resume). Submit to MIT (Dec 15), Stanford (Dec 10), CMU (Dec 15), Berkeley (Dec 1), Cornell (Jan 2). Verify receipt of all materials.",
      "duration_weeks": 2,
      "success_criteria": "All 5 applications submitted with confirmation emails received"
    }},
    {{
      "title": "Prepare for technical and fit interviews at target programs",
      "description": "Research common interview questions for CS Master's programs. Practice technical fundamentals (algorithms, systems design). Prepare stories about startup experience and research interests. Mock interviews with mentors.",
      "duration_weeks": 2,
      "success_criteria": "Completed 3 mock interviews, prepared answers for 20+ common questions"
    }}
  ]
}}

NOW GENERATE MILESTONES FOR THIS USER:
=======================================
User Goal: {goalspec.title}
User Background: {background}
User Field: {field}
Timeline: {timeline_weeks} weeks

Return ONLY valid JSON in this exact format (no markdown, no explanation):
{{
  "milestones": [
    {{
      "title": "Specific milestone title with user context",
      "description": "Detailed description with specific actions and user details",
      "duration_weeks": 2-4,
      "success_criteria": "Clear, measurable outcome"
    }},
    ... (4 more milestones)
  ]
}}

Generate now:"""

        return prompt

    def _parse_milestone_response(self, response: str) -> List[Dict[str, Any]]:
        """
        Parse JSON response from OpenAI.

        Args:
            response: Raw response from OpenAI

        Returns:
            List of milestone dictionaries
        """
        try:
            # Remove markdown code fences if present
            response = response.strip()
            if response.startswith('```'):
                # Extract JSON from code fence
                lines = response.split('\n')
                json_lines = []
                in_code = False
                for line in lines:
                    if line.startswith('```'):
                        in_code = not in_code
                        continue
                    if in_code or (not line.startswith('```')):
                        json_lines.append(line)
                response = '\n'.join(json_lines)

            # Parse JSON
            data = json.loads(response)

            # Extract milestones array
            if isinstance(data, dict) and 'milestones' in data:
                milestones = data['milestones']
            elif isinstance(data, list):
                milestones = data
            else:
                logger.error(f"[MilestoneGenerator] Unexpected response format: {type(data)}")
                return []

            # Validate each milestone
            validated_milestones = []
            for milestone in milestones:
                if self._validate_milestone(milestone):
                    validated_milestones.append(milestone)
                else:
                    logger.warning(f"[MilestoneGenerator] Invalid milestone skipped: {milestone.get('title', 'Unknown')}")

            return validated_milestones

        except json.JSONDecodeError as e:
            logger.error(f"[MilestoneGenerator] JSON parsing failed: {e}")
            logger.error(f"[MilestoneGenerator] Raw response: {response[:500]}...")
            return []

    def _validate_milestone(self, milestone: Dict[str, Any]) -> bool:
        """
        Validate that milestone has required fields.

        Args:
            milestone: Milestone dictionary

        Returns:
            True if valid, False otherwise
        """
        required_fields = ['title', 'description', 'duration_weeks', 'success_criteria']

        for field in required_fields:
            if field not in milestone:
                logger.warning(f"[MilestoneGenerator] Missing field '{field}' in milestone")
                return False

        # Validate duration
        duration = milestone.get('duration_weeks')
        if not isinstance(duration, (int, float)) or duration < 1 or duration > 8:
            logger.warning(f"[MilestoneGenerator] Invalid duration: {duration} (must be 1-8 weeks)")
            return False

        # Validate title length
        if len(milestone['title']) < 10:
            logger.warning(f"[MilestoneGenerator] Title too short: {milestone['title']}")
            return False

        return True


def create_milestone_generator() -> MilestoneGenerator:
    """Factory function to create MilestoneGenerator instance"""
    return MilestoneGenerator()
