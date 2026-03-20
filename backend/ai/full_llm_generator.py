"""
Full LLM Task Generator (Week 2 Day 3-4)

Generates 12-18 tasks entirely with LLM when templates don't cover scenario.

Used for uncovered scenarios like:
- Designer → HCI Master's (needs portfolio tasks)
- Nurse → Medical AI PhD (needs healthcare context)
- Teacher → EdTech (needs education experience)
- Lawyer → Bioethics (rare interdisciplinary)

Cost: $0.50-0.80 per user (higher than templates, but necessary for quality)
"""

from typing import Dict, Any, List
import json
from decimal import Decimal

from .llm_service import llm_service
from .task_cache import get_cached_tasks, cache_tasks


class FullLLMGenerator:
    """
    Generates complete task list using LLM (no templates).

    Week 2: Enables personalization for 80% of scenarios not covered by templates.
    """

    def __init__(self, user, user_profile, context: Dict[str, Any]):
        """
        Initialize generator with user data.

        Args:
            user: User instance
            user_profile: UserProfile instance
            context: Full personalization context from profile_extractor
        """
        self.user = user
        self.profile = user_profile
        self.context = context

    def generate_full_task_list(self, goalspec, days_ahead: int = 30) -> List[Dict]:
        """
        Generate complete 12-18 task list using LLM.

        Week 3: Now with caching - checks cache first, generates if miss.

        Args:
            goalspec: GoalSpec instance
            days_ahead: Days until deadline (for prioritization)

        Returns:
            List of 12-18 task dictionaries
        """
        print(f"[FullLLMGenerator] Generating complete task list for uncovered scenario")
        print(f"[FullLLMGenerator] Background: {self.context.get('background', 'unknown')}")
        print(f"[FullLLMGenerator] Field: {self.context.get('field', 'unknown')}")

        # Week 3: Check cache first
        cached_tasks = get_cached_tasks(
            context=self.context,
            goalspec=goalspec,
            generation_type='full_llm'
        )

        if cached_tasks:
            print(f"[FullLLMGenerator] ✅ Using cached tasks ({len(cached_tasks)} tasks)")
            print(f"[FullLLMGenerator] 💰 Cost saved: ~$0.50-0.80 (cache hit)")
            return cached_tasks

        # Cache miss - generate with LLM
        print(f"[FullLLMGenerator] ❌ Cache miss - generating with LLM")

        # Build comprehensive prompt
        prompt = self._build_full_generation_prompt(goalspec, days_ahead)

        # Generate with LLM (higher token limit for full task list)
        result = llm_service.generate(
            prompt=prompt,
            max_tokens=3000,  # Higher limit for 12-18 tasks
            temperature=0.7
        )

        tasks_json = result['text']
        cost = result['cost']
        generation_time = result['generation_time']

        # Track cost
        llm_service.track_cost(
            user=self.user,
            cost=cost,
            operation='full_llm_generation'
        )

        print(f"[FullLLMGenerator] LLM generation complete (cost: ${cost:.4f}, time: {generation_time:.2f}s)")

        # Parse JSON response
        tasks = self._parse_llm_response(tasks_json)

        print(f"[FullLLMGenerator] Generated {len(tasks)} tasks (all from LLM)")

        # Week 3: Cache tasks for future similar users
        if tasks:
            cache_tasks(
                tasks=tasks,
                context=self.context,
                goalspec=goalspec,
                generation_type='full_llm',
                cost=cost
            )

        return tasks

    def _build_full_generation_prompt(self, goalspec, days_ahead: int) -> str:
        """
        Build comprehensive prompt for full task generation.

        This prompt needs to be much more detailed than unique_task_generator
        since it's generating the ENTIRE task list (not just 2-3 unique tasks).
        """
        # Extract key context
        background = self.context.get('background', 'unknown')
        field = self.context.get('field', 'unknown field')
        target_universities = self.context.get('target_universities', [])
        gpa = self.context.get('gpa_raw', 'N/A')
        test_scores = self._format_test_scores()
        work_experience = self.context.get('work_history', 'none')
        achievements = self.context.get('achievements', 'none')

        # Build goal description
        goal_description = f"{goalspec.title}"
        if target_universities:
            goal_description += f" at {', '.join(target_universities[:3])}"

        prompt = f"""You are an expert college/graduate school application advisor. Generate a COMPLETE personalized task list for this user.

USER PROFILE:
==============
Background: {background}
Current Status: {self.context.get('current_status', 'Student')}
Field of Interest: {field}
Goal: {goal_description}
Target Universities: {', '.join(target_universities) if target_universities else 'Not specified'}
GPA: {gpa}
Test Scores: {test_scores}
Work Experience: {work_experience}
Key Achievements: {achievements}

Days Until Deadline: {days_ahead} days

TASK REQUIREMENTS:
==================
Generate 12-18 HIGH-QUALITY tasks that:

1. ✅ LEVERAGE USER'S UNIQUE BACKGROUND
   - Background is "{background}" → tasks should reflect this
   - NOT generic "update resume" - be specific to their experience

2. ✅ ARE ACTIONABLE AND SPECIFIC
   - Start with action verb (Write, Research, Email, Calculate, Register, etc.)
   - Have clear deliverable
   - Include specific details (university names, numbers, deadlines)

3. ✅ COVER ALL APPLICATION COMPONENTS
   Must include:
   - University research (3-4 tasks for target schools)
   - Statement of Purpose / Personal Statement (2-3 tasks: research, draft, revise)
   - Resume/CV (1-2 tasks with quantified achievements)
   - Recommendation letters (2-3 tasks: identify recommenders, brief them, follow up)
   - Test prep (ONLY if current scores < target scores)
   - Scholarships/funding research (1-2 tasks)
   - Application logistics (1-2 tasks: transcripts, deadlines, portals)
   - Optional: Portfolio/projects if relevant to {field}

4. ✅ ARE PRIORITIZED CORRECTLY
   Priority 5 (Highest): Unique differentiators for this user
   Priority 4: Critical requirements (SOP, recommendations)
   Priority 3: Standard requirements (transcripts, test registration)
   Priority 2: Nice-to-have (extra scholarship research)
   Priority 1: Optional enhancements

5. ✅ HAVE REALISTIC TIME ESTIMATES
   - Quick wins: 15-30 minutes
   - Standard tasks: 60-120 minutes
   - Complex tasks: 180-240 minutes
   - Never exceed 300 minutes (5 hours) per task

6. ✅ MATCH USER'S ENERGY LEVELS
   - High energy: Writing, research, creative work
   - Medium energy: Email drafting, administrative tasks
   - Low energy: Simple updates, scheduling, checking deadlines

IMPORTANT CONTEXT-SPECIFIC GUIDANCE:
====================================
{self._get_scenario_specific_guidance()}

OUTPUT FORMAT:
==============
Return ONLY a valid JSON array (no markdown, no explanation):

[
  {{
    "title": "Research MIT's {field} program: Admission requirements and faculty fit",
    "description": "Visit MIT {field} website. Note: GPA requirements, GRE scores, application deadline, required documents. Identify 3 professors whose research aligns with your background in [specific area]. Draft notes on why MIT is a good fit for your goals.",
    "category": "study",
    "priority": 4,
    "timebox_minutes": 90,
    "energy_level": "medium",
    "definition_of_done": "✅ Admission requirements documented\\n✅ 3 faculty members identified with research fit\\n✅ Notes on program fit (2-3 sentences)\\n✅ Application deadline confirmed",
    "task_type": "research"
  }},
  ... (11-17 more tasks)
]

VALIDATION CHECKS (ensure every task passes):
==============================================
1. Has user-specific context (university names, field, background details)
2. Is specific (NOT "Research universities" - name the universities)
3. Is actionable (starts with action verb, clear deliverable)
4. Has time estimate (timebox_minutes: 15-300)
5. No generic language ("your university", "[insert name]", "TODO:")

Generate tasks now:"""

        return prompt

    def _format_test_scores(self) -> str:
        """Format test scores for prompt."""
        scores = []

        if self.context.get('gre_score'):
            scores.append(f"GRE: {self.context['gre_score']}")
        if self.context.get('ielts_score'):
            scores.append(f"IELTS: {self.context['ielts_score']}")
        if self.context.get('toefl_score'):
            scores.append(f"TOEFL: {self.context['toefl_score']}")

        return ', '.join(scores) if scores else 'No test scores reported'

    def _get_scenario_specific_guidance(self) -> str:
        """
        Get scenario-specific guidance based on background+field.

        This helps LLM generate better tasks for edge cases.
        """
        background = self.context.get('background', '').lower()
        field = self.context.get('field', '').lower()

        # Designer → HCI
        if 'designer' in background and ('hci' in field or 'human-computer' in field):
            return """This user is a DESIGNER applying to HCI programs.
CRITICAL: Include portfolio-focused tasks:
- Create case study for [specific project] (tell story: problem → research → design → impact)
- Build online portfolio website (with 3-4 projects)
- Document design process (sketches, wireframes, user testing, iterations)
- Get design mentor/colleague to review portfolio

HCI programs care about: design process, user research, prototyping, impact metrics."""

        # Nurse/Doctor → Medical AI
        if any(kw in background for kw in ['nurse', 'doctor', 'healthcare']) and 'ai' in field:
            return """This user is a HEALTHCARE PROFESSIONAL applying to Medical AI / Health Tech programs.
CRITICAL: Bridge healthcare experience with technical interest:
- Write essay: "How clinical experience exposed me to AI/ML opportunities in healthcare"
- Identify specific healthcare problems they've seen that AI could solve
- Take online ML course (fast.ai, Coursera) to show technical interest
- Read recent Medical AI papers (Nature Medicine, NEJM AI) and summarize key trends

Medical AI programs want: clinical insight + technical curiosity + patient impact focus."""

        # Teacher → EdTech
        if 'teacher' in background and ('edtech' in field or 'education' in field):
            return """This user is a TEACHER/EDUCATOR applying to EdTech programs.
CRITICAL: Show teaching impact + tech interest:
- Quantify teaching impact (X students taught, Y% improvement in [metric])
- Document teaching innovations (what problems did you solve in classroom?)
- Explore EdTech tools (Khan Academy, Duolingo, Coursera) and critique their design
- Write essay: "Teaching challenges that technology could address"

EdTech programs want: classroom experience + student-centered thinking + tech savvy."""

        # Lawyer → Bioethics / Law+Tech
        if 'lawyer' in background:
            return """This user is a LAWYER applying to interdisciplinary programs.
CRITICAL: Bridge legal expertise with new field:
- Identify legal cases/issues relevant to target field (AI ethics, bioethics, etc.)
- Write essay: "How legal training prepares me for [target field]"
- Take online course in target field to show genuine interest
- Get recommendation from someone who can speak to interdisciplinary potential

Interdisciplinary programs want: depth in law + genuine curiosity in new field + bridge-building."""

        # Artist/Musician → Creative Tech
        if any(kw in background for kw in ['artist', 'musician', 'creative']):
            return """This user is a CREATIVE PROFESSIONAL applying to Creative Tech programs.
CRITICAL: Build creative tech portfolio:
- Document 3-4 projects (creative + technical components)
- Create portfolio website/blog showcasing process
- Take creative coding course (Processing, p5.js, TouchDesigner)
- Articulate how technology enhances creative practice

Creative Tech programs want: artistic vision + technical experimentation + innovation."""

        # Default guidance for other scenarios
        return f"""This user has background in {background} applying to {field}.
Focus on:
- How their {background} experience is relevant to {field}
- Specific projects/achievements that demonstrate capability
- Clear articulation of why they're transitioning to {field} (if career change)
- Evidence of genuine interest (online courses, self-study, side projects)"""

    def _parse_llm_response(self, response_text: str) -> List[Dict]:
        """
        Parse LLM JSON response into task list.

        Args:
            response_text: Raw LLM output (should be JSON array)

        Returns:
            List of task dictionaries
        """
        try:
            # Remove markdown code fences if present
            response_text = response_text.strip()
            if response_text.startswith('```'):
                response_text = response_text.split('```')[1]
                if response_text.startswith('json'):
                    response_text = response_text[4:]
                response_text = response_text.strip()

            # Parse JSON
            tasks = json.loads(response_text)

            if not isinstance(tasks, list):
                print(f"[FullLLMGenerator] ERROR: LLM returned non-list: {type(tasks)}")
                return []

            # Add metadata
            for task in tasks:
                task['source'] = 'full_llm_generator'
                task['task_category'] = 'llm_generated'

            return tasks

        except json.JSONDecodeError as e:
            print(f"[FullLLMGenerator] ERROR: JSON parsing failed: {e}")
            print(f"[FullLLMGenerator] Raw response: {response_text[:500]}...")
            return []


def create_full_llm_generator(user, user_profile, context: Dict[str, Any]) -> FullLLMGenerator:
    """
    Factory function to create FullLLMGenerator.

    Args:
        user: User instance
        user_profile: UserProfile instance
        context: Full personalization context

    Returns:
        FullLLMGenerator instance
    """
    return FullLLMGenerator(user, user_profile, context)


def generate_full_llm_tasks(
    user,
    user_profile,
    context: Dict[str, Any],
    goalspec,
    days_ahead: int = 30
) -> List[Dict]:
    """
    Convenience function to generate full LLM task list.

    Args:
        user: User instance
        user_profile: UserProfile instance
        context: Full personalization context
        goalspec: GoalSpec instance
        days_ahead: Days until deadline

    Returns:
        List of 12-18 tasks generated by LLM
    """
    generator = create_full_llm_generator(user, user_profile, context)
    return generator.generate_full_task_list(goalspec, days_ahead)
