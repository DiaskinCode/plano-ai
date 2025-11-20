"""
User Story Extractor

Extracts narrative stories from user context for better personalization in prompts.
Converts dry facts into compelling stories that the AI can reference.

Phase 3: Quality Improvements
"""

import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class UserStoryExtractor:
    """
    Extract narrative stories from user profile and goalspec.

    Converts dry facts like:
        "work_experience: Financial analyst at Forte Finance"

    Into narrative stories like:
        "Built 21 financial reports for 4 large national companies as analyst at Forte Finance"

    These stories help the AI generate more personalized tasks that BUILD ON
    the user's actual experiences rather than giving generic advice.
    """

    def __init__(self):
        """Initialize with OpenAI service"""
        from ai.services import AIService

        self.ai_service = AIService(provider='openai')
        logger.info("[UserStoryExtractor] Initialized")

    def extract_stories(self, user_profile, goalspec) -> Dict[str, str]:
        """
        Extract 5 narrative stories from user's profile and goalspec.

        Args:
            user_profile: UserProfile instance
            goalspec: GoalSpec instance

        Returns:
            Dictionary with 5 stories:
            {
                "work_story": "Built 21 financial reports for 4 large companies...",
                "achievement_story": "Created DCF models that helped evaluate $50M investment",
                "network_story": "Worked directly with CFOs of 4 national companies",
                "challenge_story": "Strong financial analysis but no audit experience",
                "aspiration_story": "Wants to transition from reporting to audit at KPMG"
            }
        """
        logger.info(f"[UserStoryExtractor] Extracting stories for goal: {goalspec.title}")

        # Build context from profile and goalspec
        context = self._build_context(user_profile, goalspec)

        # Generate stories using LLM
        prompt = self._build_extraction_prompt(context, goalspec)

        try:
            response = self.ai_service.call_llm(
                system_prompt="You are an expert at extracting compelling narratives from user profiles. Return only valid JSON.",
                user_prompt=prompt,
                response_format="json"
            )

            stories = self._parse_stories(response)

            if stories:
                logger.info(f"[UserStoryExtractor] ✅ Extracted {len(stories)} stories")
                for key, story in stories.items():
                    logger.info(f"  {key}: {story[:60]}...")
            else:
                logger.warning("[UserStoryExtractor] No stories extracted, using defaults")
                stories = self._get_default_stories(context, goalspec)

            return stories

        except Exception as e:
            logger.error(f"[UserStoryExtractor] Failed to extract stories: {e}")
            return self._get_default_stories(context, goalspec)

    def _build_context(self, user_profile, goalspec) -> Dict[str, Any]:
        """Build context dictionary from profile and goalspec"""

        specs = goalspec.specifications or {}

        context = {
            # From profile
            'background': getattr(user_profile, 'background', ''),
            'work_experience_summary': getattr(user_profile, 'work_experience_summary', ''),
            'education_summary': getattr(user_profile, 'education_summary', ''),
            'notable_achievements': getattr(user_profile, 'notable_achievements', ''),
            'current_company': getattr(user_profile, 'current_company', ''),
            'current_role': getattr(user_profile, 'current_role', ''),

            # From goalspec specifications
            'target_role': specs.get('target_role', ''),
            'target_companies': specs.get('target_companies', ''),
            'target_schools': specs.get('target_schools', []),
            'field_of_study': specs.get('field_of_study', ''),
            'gpa': specs.get('gpa', ''),
            'test_scores': specs.get('test_scores', ''),
            'tech_stack': specs.get('tech_stack', ''),
            'years_experience': specs.get('years_experience', ''),
            'budget': specs.get('budget', ''),
            'timeline': specs.get('timeline', ''),
            'research_interests': specs.get('research_interests', ''),

            # Goal info
            'goal_title': goalspec.title,
            'goal_category': goalspec.category,
        }

        return context

    def _build_extraction_prompt(self, context: Dict[str, Any], goalspec) -> str:
        """Build prompt for story extraction"""

        prompt = f"""Extract narrative stories from this user's profile.

USER PROFILE:
=============
{json.dumps(context, indent=2, default=str)}

GOAL:
=====
{goalspec.title} ({goalspec.category})

TASK:
=====
Extract 5 specific, compelling stories from this profile:

1. **work_story** - What they've actually DONE (with specific numbers, companies, projects)
   Example: "Built 21 financial reports for 4 large national companies as analyst at Forte Finance"

2. **achievement_story** - Something impressive they accomplished
   Example: "Created DCF models that helped evaluate $50M investment decision"

3. **network_story** - People/companies they've worked with
   Example: "Worked directly with CFOs of 4 national companies"

4. **challenge_story** - Gap they need to overcome for their goal
   Example: "Strong financial analysis background but no audit experience or CPA"

5. **aspiration_story** - Where they want to go (combine goal + context)
   Example: "Wants to transition from financial reporting to audit at KPMG Big 4"

RULES:
======
- Be SPECIFIC with numbers, names, companies, projects
- If information is missing, make reasonable inferences from what's available
- Don't make up fake numbers/names - use what's provided or be vague
- Each story should be 1-2 sentences max
- Stories should be usable in task prompts like "Using YOUR experience of [story]..."

Return ONLY valid JSON:
{{
    "work_story": "specific work experience with numbers/projects",
    "achievement_story": "key accomplishment with impact",
    "network_story": "who they've worked with",
    "challenge_story": "gap between current state and goal",
    "aspiration_story": "their specific goal with context"
}}
"""
        return prompt

    def _parse_stories(self, response: str) -> Dict[str, str]:
        """Parse JSON response into stories dictionary"""

        try:
            # Clean response
            response = response.strip()
            if response.startswith('```'):
                lines = response.split('\n')
                json_lines = [l for l in lines if not l.startswith('```')]
                response = '\n'.join(json_lines)

            data = json.loads(response)

            # Validate required keys
            required_keys = ['work_story', 'achievement_story', 'network_story',
                           'challenge_story', 'aspiration_story']

            stories = {}
            for key in required_keys:
                if key in data and data[key]:
                    stories[key] = str(data[key])
                else:
                    stories[key] = ""

            return stories

        except json.JSONDecodeError as e:
            logger.error(f"[UserStoryExtractor] JSON parsing failed: {e}")
            return {}

    def _get_default_stories(self, context: Dict[str, Any], goalspec) -> Dict[str, str]:
        """Generate default stories when extraction fails"""

        work = context.get('work_experience_summary', '') or context.get('background', '')
        achievement = context.get('notable_achievements', '')
        company = context.get('current_company', '')
        role = context.get('current_role', '')
        target = context.get('target_role', '') or goalspec.title
        target_companies = context.get('target_companies', '')

        return {
            'work_story': work or f"Experience in {goalspec.category}",
            'achievement_story': achievement or "Professional experience in the field",
            'network_story': f"Work experience at {company}" if company else "Professional network",
            'challenge_story': f"Transitioning from {role} to {target}" if role and target else "Building new skills",
            'aspiration_story': f"Goal: {goalspec.title}" + (f" at {target_companies}" if target_companies else ""),
        }


def create_story_extractor() -> UserStoryExtractor:
    """Factory function to create UserStoryExtractor instance"""
    return UserStoryExtractor()
