"""
Intelligent Task Agent
Autonomously researches and generates specific, actionable tasks
"""
import json
from typing import Dict, List, Any
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

from .services import AIService
from .web_search import web_search_service
from users.models import UserProfile


class TaskAgent:
    """
    Autonomous agent that:
    1. Analyzes user's milestone/vision
    2. Determines what information to search for
    3. Executes web searches
    4. Generates specific, enriched tasks
    """

    def __init__(self, user_id: int):
        self.user_id = user_id
        self.ai_service = AIService()
        self.search_service = web_search_service
        self.search_results = {}

    def plan_and_search(
        self,
        milestone: Dict,
        user_profile: UserProfile
    ) -> List[Dict]:
        """
        Main agent workflow: Plan → Search → Generate

        Args:
            milestone: Current milestone dict with title, goal, key_tasks
            user_profile: User profile with industry, location, etc.

        Returns:
            List of enriched task dicts ready for database insertion
        """
        print(f"[TaskAgent] Starting for user {self.user_id}")
        print(f"[TaskAgent] Milestone: {milestone.get('title', 'N/A')}")

        # PHASE 1: Planning - AI decides what to search for
        searches_needed = self._plan_searches(milestone, user_profile)

        if not searches_needed or not self.search_service.is_available():
            print("[TaskAgent] No searches needed or search unavailable, using direct generation")
            return self._generate_tasks_without_search(milestone, user_profile)

        # PHASE 2: Execute searches IN PARALLEL (3x faster!)
        print(f"[TaskAgent] Executing {len(searches_needed)} searches in parallel...")
        with ThreadPoolExecutor(max_workers=min(len(searches_needed), 5)) as executor:
            # Submit all searches at once
            future_to_search = {
                executor.submit(self._execute_search, search, user_profile): search
                for search in searches_needed
            }

            # Wait for all to complete
            for future in as_completed(future_to_search):
                search = future_to_search[future]
                try:
                    future.result()  # This will raise exception if search failed
                except Exception as e:
                    print(f"[TaskAgent] Search '{search.get('type')}' failed: {e}")

        # PHASE 3: Generate enriched tasks
        print("[TaskAgent] Generating enriched tasks...")
        enriched_tasks = self._generate_enriched_tasks(milestone, user_profile)

        return enriched_tasks

    def _plan_searches(
        self,
        milestone: Dict,
        user_profile: UserProfile
    ) -> List[Dict]:
        """
        PHASE 1: Agent analyzes milestone and decides what searches are needed

        Returns:
            List of search configurations
        """
        planning_prompt = f"""You are an intelligent task planning agent. Analyze this user's milestone and determine what specific information you need from the web to create ACTIONABLE, SPECIFIC tasks (not generic ones).

USER CONTEXT:
- Industry/Field: {getattr(user_profile, 'dream_career', 'N/A')}
- Country: {getattr(user_profile, 'country_of_residence', 'N/A')}
- Current Goals: {getattr(user_profile, 'future_goals', 'N/A')}

MILESTONE TO ANALYZE:
- Title: {milestone.get('title', '')}
- Goal: {milestone.get('goal', '')}
- Key Tasks: {json.dumps(milestone.get('key_tasks', []))}

INSTRUCTIONS:
Determine what you need to search for. For each key task, identify if it requires:
- LinkedIn profiles (networking tasks) → search for specific people
- Industry events (attendance tasks) → search for real events with dates
- Online courses (learning tasks) → search for specific courses/platforms
- General research (other tasks) → search for tools, resources, guides

Return ONLY searches that will help make tasks MORE SPECIFIC. Don't search if the task is already actionable.

Return JSON:
{{
  "searches": [
    {{
      "type": "linkedin",
      "query": "specific search query",
      "reason": "why this search is needed",
      "for_task": "which key task this supports"
    }},
    {{
      "type": "events",
      "query": "...",
      "reason": "...",
      "for_task": "..."
    }},
    {{
      "type": "courses",
      "query": "...",
      "reason": "...",
      "for_task": "..."
    }},
    {{
      "type": "general",
      "query": "...",
      "reason": "...",
      "for_task": "..."
    }}
  ]
}}

If NO searches are needed (tasks are already specific), return: {{"searches": []}}
"""

        try:
            system_prompt = "You are a strategic planning agent. Analyze requirements and determine optimal search strategies."
            response = self.ai_service.call_llm(
                system_prompt,
                planning_prompt,
                response_format='json'
            )

            plan = json.loads(response)
            searches = plan.get('searches', [])

            print(f"[TaskAgent] Planned {len(searches)} searches")
            for search in searches:
                print(f"  - {search['type']}: {search['query']}")

            return searches

        except Exception as e:
            print(f"[TaskAgent] Planning error: {e}")
            return []

    def _execute_search(
        self,
        search_config: Dict,
        user_profile: UserProfile
    ):
        """
        PHASE 2: Execute a single search and store results

        Args:
            search_config: Search configuration from planning phase
            user_profile: User profile for context (location, industry, etc.)
        """
        search_type = search_config['type']
        query = search_config['query']

        try:
            if search_type == 'linkedin':
                industry = getattr(user_profile, 'dream_career', '')
                country = getattr(user_profile, 'country_of_residence', '')
                results = self.search_service.search_linkedin_profiles(
                    query=query,
                    industry=industry,
                    location=country,  # Use country as location filter
                    max_results=3
                )

            elif search_type == 'events':
                industry_query = query
                country = getattr(user_profile, 'country_of_residence', '')
                results = self.search_service.search_events(
                    industry=industry_query,
                    location=country,  # Use country as location filter
                    timeframe="2025",
                    max_results=3
                )

            elif search_type == 'courses':
                results = self.search_service.search_courses(
                    topic=query,
                    level="intermediate",
                    max_results=3
                )

            else:  # general
                results = self.search_service.search_general(
                    query=query,
                    max_results=3
                )

            # Store results
            if search_type not in self.search_results:
                self.search_results[search_type] = []

            self.search_results[search_type].extend(results)

            print(f"[TaskAgent] Search '{search_type}' found {len(results)} results")

        except Exception as e:
            print(f"[TaskAgent] Search execution error ({search_type}): {e}")

    def _generate_enriched_tasks(
        self,
        milestone: Dict,
        user_profile: UserProfile
    ) -> List[Dict]:
        """
        PHASE 3: Generate specific tasks using search results

        Returns:
            List of task dicts with all fields needed for database
        """
        today = datetime.now().date()

        enrichment_prompt = f"""You are creating SPECIFIC, ACTIONABLE tasks for a user. Use the search results to make tasks concrete.

USER CONTEXT:
- Goals: {getattr(user_profile, 'future_goals', 'N/A')}
- Career: {getattr(user_profile, 'dream_career', 'N/A')}
- Country: {getattr(user_profile, 'country_of_residence', 'N/A')}

MILESTONE:
- Title: {milestone.get('title', '')}
- Goal: {milestone.get('goal', '')}
- Key Tasks: {json.dumps(milestone.get('key_tasks', []))}

SEARCH RESULTS AVAILABLE:
{json.dumps(self.search_results, indent=2)}

INSTRUCTIONS:
Create 5-10 SPECIFIC tasks for the next 30 days. Use search results to include:
- Real names from LinkedIn (e.g., "Connect with Sarah Chen, PM at Stripe")
- Actual event names and dates (e.g., "Attend TechCrunch Disrupt Oct 28-30")
- Specific course titles (e.g., "Enroll in 'Product Management' on Coursera")
- Real URLs and contact info when available

Mix of:
- Daily routine tasks (if applicable)
- One-time milestone tasks
- Networking tasks
- Learning tasks

Return JSON:
{{
  "tasks": [
    {{
      "title": "Specific task with real name/date/platform",
      "task_type": "daily_routine|one_time|networking|learning",
      "scheduled_date": "2025-10-{today.day + 1}",
      "scheduled_time": "09:00",
      "priority": 1-3,
      "duration_minutes": 30-120,
      "external_url": "https://... (if applicable)",
      "notes": "Additional context from search results"
    }}
  ]
}}

IMPORTANT:
- scheduled_date format: YYYY-MM-DD (start from today: {today})
- scheduled_time format: HH:MM (24-hour)
- priority: 3=high, 2=medium, 1=low
- Be SPECIFIC. Use actual names, dates, platforms from search results
"""

        try:
            system_prompt = "You are an expert task planner who creates specific, actionable tasks."
            response = self.ai_service.call_llm(
                system_prompt,
                enrichment_prompt,
                response_format='json'
            )

            result = json.loads(response)
            tasks = result.get('tasks', [])

            print(f"[TaskAgent] Generated {len(tasks)} enriched tasks")

            # Validate and clean tasks
            validated_tasks = []
            for task in tasks:
                if self._validate_task(task):
                    validated_tasks.append(task)

            return validated_tasks

        except Exception as e:
            print(f"[TaskAgent] Task generation error: {e}")
            return []

    def _generate_tasks_without_search(
        self,
        milestone: Dict,
        user_profile: UserProfile
    ) -> List[Dict]:
        """
        Fallback: Generate tasks without web search results

        Used when:
        - No searches are needed
        - Web search is unavailable
        - Search fails
        """
        print("[TaskAgent] Generating tasks without search (fallback)")

        today = datetime.now().date()

        prompt = f"""Create specific tasks for this milestone:

MILESTONE:
- Title: {milestone.get('title', '')}
- Goal: {milestone.get('goal', '')}
- Key Tasks: {json.dumps(milestone.get('key_tasks', []))}

USER:
- Career: {getattr(user_profile, 'dream_career', 'N/A')}
- Goals: {getattr(user_profile, 'future_goals', 'N/A')}

Create 5-8 actionable tasks for the next 30 days. Be as specific as possible given the information.

Return JSON:
{{
  "tasks": [
    {{
      "title": "...",
      "task_type": "daily_routine|one_time",
      "scheduled_date": "2025-10-{today.day + 1}",
      "scheduled_time": "09:00",
      "priority": 1-3,
      "duration_minutes": 30-120,
      "notes": "..."
    }}
  ]
}}
"""

        try:
            system_prompt = "You are a task planning expert."
            response = self.ai_service.call_llm(
                system_prompt,
                prompt,
                response_format='json'
            )

            result = json.loads(response)
            return result.get('tasks', [])

        except Exception as e:
            print(f"[TaskAgent] Fallback generation error: {e}")
            return []

    def _validate_task(self, task: Dict) -> bool:
        """Validate task has required fields"""
        required = ['title', 'scheduled_date', 'priority', 'duration_minutes']
        return all(field in task for field in required)
