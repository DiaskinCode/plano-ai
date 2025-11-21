"""
AI Service Layer - Integration with OpenAI/Anthropic
"""
import json
import os
import re
import hashlib
from typing import Dict, Any, Optional, List
from django.conf import settings
from django.core.cache import cache

from .context import build_user_state_snapshot, format_snapshot_for_prompt
from . import prompts
from . import prompts_ru


class AIService:
    """AI Service for PathAI using OpenAI or Anthropic"""

    def __init__(self, provider: str = 'openai'):
        self.provider = provider.lower()

        if self.provider == 'openai':
            import openai
            self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            self.model = 'gpt-4o'  # Upgraded from gpt-4o-mini for better personalization
        elif self.provider == 'anthropic':
            import anthropic
            self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
            self.model = 'claude-3-5-sonnet-latest'  # Use latest stable version
        else:
            raise ValueError(f"Unsupported AI provider: {provider}")

    def _get_prompts_module(self, user_id: int):
        """Get appropriate prompts module based on user language"""
        from users.models import User, UserProfile
        try:
            user = User.objects.get(id=user_id)
            profile = UserProfile.objects.get(user=user)
            language = profile.preferred_language

            if language == 'ru':
                return prompts_ru
            else:
                return prompts
        except:
            return prompts  # Default to English

    def _call_openai(self, system_prompt: str, user_prompt: str = None, response_format: str = 'text', messages: list = None, functions: list = None, function_call: str = 'auto'):
        """Call OpenAI API

        Args:
            system_prompt: System prompt for the AI
            user_prompt: Single user prompt (legacy, optional)
            response_format: 'text' or 'json'
            messages: Full conversation history (new format)
            functions: List of function definitions for function calling
            function_call: 'auto', 'none', or specific function name
        """
        if messages is None:
            # Legacy single-message format
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        else:
            # New multi-message format with conversation history
            messages = [{"role": "system", "content": system_prompt}] + messages

        # Build request parameters
        params = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7
        }

        # Add function calling if provided
        if functions:
            params["tools"] = [{"type": "function", "function": func} for func in functions]
            if function_call == 'auto':
                params["tool_choice"] = "auto"
            elif function_call == 'required':
                params["tool_choice"] = "required"

        # Add response format if JSON
        if response_format == 'json' and not functions:
            params["response_format"] = {"type": "json_object"}

        response = self.client.chat.completions.create(**params)

        # Handle function calling response
        if functions and response.choices[0].message.tool_calls:
            # Return both the message and function call
            return {
                'content': response.choices[0].message.content or '',
                'tool_calls': [
                    {
                        'function': {
                            'name': tool_call.function.name,
                            'arguments': tool_call.function.arguments
                        }
                    }
                    for tool_call in response.choices[0].message.tool_calls
                ]
            }

        return response.choices[0].message.content or ''

    def _call_anthropic(self, system_prompt: str, user_prompt: str = None, response_format: str = 'text', messages: list = None) -> str:
        """Call Anthropic API

        Args:
            system_prompt: System prompt for the AI
            user_prompt: Single user prompt (legacy, optional)
            response_format: 'text' or 'json' (not used for Anthropic but kept for compatibility)
            messages: Full conversation history (new format)
        """
        if messages is None:
            # Legacy single-message format
            messages = [
                {"role": "user", "content": user_prompt}
            ]

        message = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            system=system_prompt,
            messages=messages
        )

        return message.content[0].text

    def call_llm(self, system_prompt: str, user_prompt: str = None, response_format: str = 'text', messages: list = None, functions: list = None, function_call: str = 'auto'):
        """Call LLM based on provider

        Args:
            system_prompt: System prompt for the AI
            user_prompt: Single user prompt (legacy, optional)
            response_format: 'text' or 'json'
            messages: Full conversation history (new format)
            functions: List of function definitions for function calling (OpenAI only)
            function_call: 'auto', 'none', or specific function name (OpenAI only)
        """
        if self.provider == 'openai':
            return self._call_openai(system_prompt, user_prompt, response_format, messages, functions, function_call)
        elif self.provider == 'anthropic':
            return self._call_anthropic(system_prompt, user_prompt, response_format, messages)

    def generate_scenarios(self, user_id: int, user_profile_data: Dict) -> list:
        """Generate success scenarios based on user profile (with Redis caching)"""

        # Create cache key from profile characteristics
        cache_key_data = f"{user_profile_data.get('dream_career', '')}" \
                        f"_{user_profile_data.get('country_of_residence', '')}" \
                        f"_{user_profile_data.get('target_timeline', '')}"
        cache_key = f"scenarios_{hashlib.md5(cache_key_data.encode()).hexdigest()}"

        # Try to get from cache first
        cached_scenarios = cache.get(cache_key)
        if cached_scenarios:
            print(f"[AIService] Using cached scenarios for {cache_key_data}")
            return cached_scenarios

        # Not in cache, generate new scenarios
        snapshot = build_user_state_snapshot(user_id)
        context_str = format_snapshot_for_prompt(snapshot)

        # Add profile data to context
        profile_info = f"""
Name: {user_profile_data.get('name', 'User')}
Age: {user_profile_data.get('age', 'N/A')}
Current Situation: {user_profile_data.get('current_situation', '')}
Future Goals: {user_profile_data.get('future_goals', '')}
Dream Career: {user_profile_data.get('dream_career', '')}
Budget: {user_profile_data.get('budget_range', '')}
Timeline: {user_profile_data.get('target_timeline', '')}
"""

        p = self._get_prompts_module(user_id)
        user_prompt = p.get_scenario_generation_prompt(profile_info + "\n" + context_str)
        system_prompt = p.get_system_prompt(snapshot['user_meta'].get('coach_character', 'supportive'))

        response = self.call_llm(system_prompt, user_prompt, response_format='json')

        try:
            data = json.loads(response)

            # Handle different response formats
            if isinstance(data, list):
                scenarios = data
            elif isinstance(data, dict):
                # Check if response has 'scenarios' key
                if 'scenarios' in data:
                    scenarios = data['scenarios']
                else:
                    # Single scenario object
                    scenarios = [data]
            else:
                scenarios = []

            # Ensure each scenario has required fields
            validated_scenarios = []
            for scenario in scenarios:
                if isinstance(scenario, dict):
                    # Ensure pros and cons are lists
                    if 'pros' not in scenario or not isinstance(scenario['pros'], list):
                        scenario['pros'] = []
                    if 'cons' not in scenario or not isinstance(scenario['cons'], list):
                        scenario['cons'] = []
                    validated_scenarios.append(scenario)

            # Cache the results for 1 hour
            cache.set(cache_key, validated_scenarios, 3600)
            print(f"[AIService] Cached scenarios for {cache_key_data}")

            return validated_scenarios
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            print(f"Response was: {response}")
            return []

    def generate_vision(self, user_id: int, scenario_data: Dict) -> Dict:
        """Generate detailed vision from selected scenario"""
        snapshot = build_user_state_snapshot(user_id)
        context_str = format_snapshot_for_prompt(snapshot)

        scenario_str = f"""
Title: {scenario_data.get('title', '')}
Description: {scenario_data.get('description', '')}
"""

        p = self._get_prompts_module(user_id)
        user_prompt = p.get_vision_generation_prompt(scenario_str, context_str)
        system_prompt = p.get_system_prompt(snapshot['user_meta'].get('coach_character', 'supportive'))

        response = self.call_llm(system_prompt, user_prompt, response_format='json')

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {}

    def integrate_user_task(self, user_id: int, task_description: str) -> Dict:
        """Find optimal slot for user's task"""
        snapshot = build_user_state_snapshot(user_id)
        context_str = format_snapshot_for_prompt(snapshot)

        user_prompt = get_task_integration_prompt(task_description, context_str)
        system_prompt = get_system_prompt(snapshot['user_meta'].get('coach_character', 'supportive'))

        response = self.call_llm(system_prompt, user_prompt, response_format='json')

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {}

    def process_checkin(self, user_id: int, checkin_data: Dict) -> Dict:
        """Process evening check-in and generate recommendations"""
        snapshot = build_user_state_snapshot(user_id)
        context_str = format_snapshot_for_prompt(snapshot)

        checkin_str = f"""
Completed: {checkin_data.get('completed_tasks_text', '')}
Missed: {checkin_data.get('missed_tasks_text', '')}
Reason: {checkin_data.get('missed_reason', '')}
New Opportunities: {checkin_data.get('new_opportunities', '')}
"""

        user_prompt = get_checkin_prompt(checkin_str, context_str)
        system_prompt = get_system_prompt(snapshot['user_meta'].get('coach_character', 'supportive'))

        response = self.call_llm(system_prompt, user_prompt, response_format='json')

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {}

    def analyze_opportunity(self, user_id: int, opportunity_text: str) -> Dict:
        """Analyze new opportunity and suggest action"""
        snapshot = build_user_state_snapshot(user_id)
        context_str = format_snapshot_for_prompt(snapshot)

        user_prompt = get_opportunity_analysis_prompt(opportunity_text, context_str)
        system_prompt = get_system_prompt(snapshot['user_meta'].get('coach_character', 'supportive'))

        response = self.call_llm(system_prompt, user_prompt, response_format='json')

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {}

    def chat_response(self, user_id: int, user_message: str, conversation_history: list = None) -> Dict[str, Any]:
        """Generate chat response with optional task creation and completion detection

        Args:
            user_id: User ID
            user_message: Current user message
            conversation_history: List of previous messages in format [{"role": "user/assistant", "content": "..."}]
        """
        snapshot = build_user_state_snapshot(user_id)
        context_str = format_snapshot_for_prompt(snapshot)

        p = self._get_prompts_module(user_id)
        system_prompt = p.get_system_prompt(snapshot['user_meta'].get('coach_character', 'supportive'))

        # Add context to system prompt
        system_prompt_with_context = f"{system_prompt}\n\nCurrent user context:\n{context_str}"

        if conversation_history:
            # Build message history for multi-turn conversation
            messages = []
            for msg in conversation_history:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

            # Add current message with task detection instructions
            current_message_with_instructions = f"""{user_message}

IMPORTANT: Analyze this message and respond in JSON format with:
{{
    "response": "your conversational response",
    "create_tasks": [
        {{
            "title": "task title",
            "scheduled_time": "HH:MM format - MUST calculate based on current time from context!",
            "priority": 1-3,
            "duration_minutes": estimated duration
        }}
    ],
    "update_tasks": [list of task updates if user requests rescheduling],
    "completed_task_ids": [list of task IDs if user reports completion]
}}

CRITICAL for scheduled_time calculation:
- Check the "Current Time" in the context above
- For relative times like "через час" (in 1 hour), ADD to current time
- Example: If current time is 06:41 and user says "через час", return "07:41"
- DO NOT return arbitrary times - always calculate from current time!"""

            messages.append({
                "role": "user",
                "content": current_message_with_instructions
            })

            response_text = self.call_llm(system_prompt_with_context, messages=messages, response_format='json')
        else:
            # Legacy single-message format (fallback)
            user_prompt = p.get_chat_response_prompt(user_message, context_str)
            response_text = self.call_llm(system_prompt, user_prompt, response_format='json')

        try:
            response_data = json.loads(response_text)
            return {
                'response': response_data.get('response', response_text),
                'create_tasks': response_data.get('create_tasks', []),
                'update_tasks': response_data.get('update_tasks', []),
                'completed_task_ids': response_data.get('completed_task_ids', [])
            }
        except json.JSONDecodeError:
            # Fallback if AI didn't return JSON
            return {
                'response': response_text,
                'create_tasks': [],
                'update_tasks': [],
                'completed_task_ids': []
            }

    def transcribe_audio(self, audio_file_path: str) -> str:
        """Transcribe audio using Whisper"""
        if self.provider != 'openai':
            raise ValueError("Audio transcription only available with OpenAI")

        with open(audio_file_path, 'rb') as audio_file:
            transcript = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )

        return transcript.text

    def generate_daily_headline(self, vision_title: str, user_id: int = None) -> str:
        """Generate a short motivational headline from vision title"""
        p = self._get_prompts_module(user_id) if user_id else prompts
        user_prompt = p.get_daily_headline_prompt(vision_title)

        # Adjust system prompt based on language
        if user_id:
            try:
                from users.models import User, UserProfile
                user = User.objects.get(id=user_id)
                profile = UserProfile.objects.get(user=user)
                if profile.preferred_language == 'ru':
                    system_prompt = "Вы лаконичный мотивационный писатель. Создавайте короткие, вдохновляющие утверждения о личности."
                else:
                    system_prompt = "You are a concise motivational writer. Generate short, inspiring identity statements."
            except:
                system_prompt = "You are a concise motivational writer. Generate short, inspiring identity statements."
        else:
            system_prompt = "You are a concise motivational writer. Generate short, inspiring identity statements."

        response = self.call_llm(system_prompt, user_prompt, response_format='text')

        # Clean up the response - remove quotes, extra whitespace, etc.
        headline = response.strip().strip('"').strip("'").strip()

        return headline

    def generate_task_description(self, user_id: int, task) -> str:
        """
        Generate a rich description for a task
        Includes: what to do, where to do it, how long it takes, what you need
        """
        p = self._get_prompts_module(user_id)

        # Build task context
        task_context = f"""
Task Title: {task.title}
Task Type: {task.task_type}
Estimated Time: {task.timebox_minutes} minutes
Deliverable: {task.deliverable_type}
Priority: {task.priority}
"""

        # Add goalspec context if available
        if task.goalspec:
            task_context += f"""
Related Goal: {task.goalspec.title}
Goal Category: {task.goalspec.category}
Goal Specifications: {task.goalspec.specifications}
"""

        user_prompt = f"""Generate a detailed, actionable description for this task:

{task_context}

Provide a description that includes:
1. What exactly needs to be done
2. Where to do it (specific websites, locations, or platforms)
3. What information or materials are needed
4. Any important tips or considerations

Keep it concise but informative (2-4 sentences)."""

        system_prompt = "You are a helpful task management assistant. Generate clear, actionable task descriptions."

        description = self.call_llm(system_prompt, user_prompt, response_format='text')

        return description.strip()

    def _extract_urls_from_text(self, text: str) -> List[Dict[str, str]]:
        """
        Extract URLs from plain text as fallback when AI doesn't structure links properly.
        Returns list of link objects with title, url, and description.
        """
        if not text:
            return []

        links = []

        # Common patterns for finding URLs and their context
        # Pattern 1: Full URLs with https://
        url_pattern = r'https?://[^\s\)\]]+[a-zA-Z0-9/]'

        # Pattern 2: Domain names mentioned without https:// (like "ielts.org", "britishcouncil.org")
        domain_pattern = r'(?:^|\s)([a-z0-9-]+\.[a-z]{2,}(?:\.[a-z]{2,})?(?:/[^\s\)]*)?)'

        # Extract full URLs first
        found_urls = re.findall(url_pattern, text, re.IGNORECASE)
        for url in found_urls:
            # Clean up URL (remove trailing punctuation)
            url = url.rstrip('.,;:!?')

            # Try to extract title from context (text before the URL)
            context_match = re.search(rf'([^.!?]*?){re.escape(url)}', text)
            title = "Link"
            if context_match:
                context = context_match.group(1).strip()
                # Extract last few words as title
                words = context.split()
                if words:
                    title = ' '.join(words[-3:]) if len(words) >= 3 else context

            links.append({
                'title': title or url.split('//')[1].split('/')[0],
                'url': url,
                'description': ''
            })

        # Extract domain names mentioned without https://
        domain_matches = re.findall(domain_pattern, text, re.IGNORECASE)
        for domain in domain_matches:
            # Skip if already added as full URL
            if any(domain in link['url'] for link in links):
                continue

            # Clean domain name
            domain = domain.strip()

            # Convert to full URL
            url = f"https://{domain}" if not domain.startswith('http') else domain

            # Extract title from context
            title = domain.split('.')[0].upper() if '.' in domain else domain

            links.append({
                'title': title,
                'url': url,
                'description': ''
            })

        # Remove duplicates based on URL
        seen_urls = set()
        unique_links = []
        for link in links:
            if link['url'] not in seen_urls:
                seen_urls.add(link['url'])
                unique_links.append(link)

        return unique_links[:10]  # Limit to 10 links to avoid clutter

    def task_specific_assistance(self, user_id: int, task, question: str, conversation_history: list = None, mode: str = 'clarify') -> dict:
        """
        Provide task-specific AI assistance with detailed links, contacts, and instructions

        Args:
            user_id: User ID
            task: Task object
            question: User's question about the task
            conversation_history: Previous conversation context
            mode: Response mode - 'clarify' (quick, ≤100 words), 'expand' (generate subtasks), 'research' (full details)

        Returns:
            dict with response, links, contacts, steps, and can_expand flag
        """
        print(f"\n{'='*80}")
        print(f"[AI SERVICE] task_specific_assistance called")
        print(f"[AI SERVICE] Task ID: {task.id}, Title: {task.title}")
        print(f"[AI SERVICE] Question: {question}")
        print(f"[AI SERVICE] Mode: {mode}")
        print(f"[AI SERVICE] Conversation history length: {len(conversation_history) if conversation_history else 0}")
        print(f"{'='*80}\n")

        p = self._get_prompts_module(user_id)

        # Build comprehensive task context
        task_context = f"""
Task: {task.title}
Description: {task.description or 'No description'}
Type: {task.task_type}
Time Required: {task.timebox_minutes} minutes
Deliverable: {task.deliverable_type}
"""

        # Add goalspec context for better recommendations
        if task.goalspec:
            task_context += f"""

Related Goal: {task.goalspec.title}
Category: {task.goalspec.category}
Specifications: {task.goalspec.specifications}
"""

        print(f"[AI SERVICE] Task context:\n{task_context}")

        # Mode-specific system prompts
        if mode == 'clarify':
            system_prompt = """You are a quick-answer task assistant. Provide BRIEF, FOCUSED answers (≤100 words).

Your response should be:
- CONCISE: Get to the point immediately
- DIRECT: Answer the specific question asked
- MINIMAL: Don't over-explain unless asked

Always respond in JSON format:
{
    "response": "Brief, focused answer (≤100 words)",
    "links": [],
    "contacts": [],
    "steps": []
}

If the question needs more detail, keep the response short but indicate that full research is available."""

        elif mode == 'expand':
            system_prompt = """You are a task breakdown assistant. Generate actionable subtasks and step-by-step plans.

Focus on:
1. Breaking down the task into CONCRETE, ACTIONABLE subtasks
2. Providing a clear sequence of steps
3. Identifying key deliverables at each step

Always respond in JSON format:
{
    "response": "Overview of the task breakdown approach",
    "links": [
        {"title": "Resource Name", "url": "https://example.com", "description": "Why this is useful"}
    ],
    "contacts": [],
    "steps": [
        "Specific actionable step 1",
        "Specific actionable step 2",
        "Specific actionable step 3"
    ]
}

Each step should be something the user can immediately act on."""

        else:  # research mode
            system_prompt = """You are a comprehensive research assistant. Provide DETAILED, THOROUGH answers with all relevant information.

CRITICAL: You MUST return ONLY valid JSON. NO additional text before or after the JSON.

When users ask about tasks, provide:
1. SPECIFIC, ACTIONABLE links (real URLs to official websites, portals, application forms)
2. CONTACT INFORMATION (emails, phone numbers, support links)
3. STEP-BY-STEP instructions
4. EXACT requirements and deadlines
5. Additional context and recommendations

JSON FORMAT (strict schema):
{
    "response": "Your comprehensive answer in natural language",
    "links": [
        {"title": "Short Name", "url": "https://full-url.com", "description": "What this link is for"}
    ],
    "contacts": [
        {"type": "email", "value": "contact@example.com", "label": "Who to contact"}
    ],
    "steps": [
        "Step 1: Action to take",
        "Step 2: Next action"
    ]
}

IMPORTANT RULES:
1. DO NOT mention URLs in "response" text like "ielts.org" or "britishcouncil.org"
2. ALWAYS put URLs in the "links" array with proper structure
3. Each link MUST have: "title" (name of resource), "url" (full https:// link), "description" (purpose)
4. The "response" field should be conversational text WITHOUT raw URLs

EXAMPLE for "Where to get IELTS mock tests?":
{
    "response": "Для получения mock tests используйте следующие ресурсы: 1) Официальный сайт IELTS - раздел 'Prepare for your test'. 2) Британский совет - предлагает бесплатные образцы тестов. 3) Cambridge English - книги с тестами и онлайн-материалы. 4) IELTS Liz - практические тесты и советы. 5) YouTube - каналы с видео-симуляциями тестов. Изучите эти источники, чтобы практиковаться.",
    "links": [
        {"title": "IELTS Official - Practice Tests", "url": "https://www.ielts.org/for-test-takers/how-to-prepare", "description": "Официальные материалы для подготовки к IELTS"},
        {"title": "British Council - Free Practice", "url": "https://www.britishcouncil.org/exam/ielts/prepare", "description": "Бесплатные образцы тестов от Британского совета"},
        {"title": "Cambridge IELTS Books", "url": "https://www.cambridgeenglish.org/exams-and-tests/ielts/", "description": "Официальные книги Cambridge с тестами"},
        {"title": "IELTS Liz Practice Tests", "url": "https://ieltsliz.com/", "description": "Практические тесты и советы от IELTS Liz"}
    ],
    "contacts": [],
    "steps": []
}

Be specific and ALWAYS structure links properly in the JSON."""

        # Build messages for conversation
        messages = []
        if conversation_history:
            for msg in conversation_history:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

        # Current question with context
        current_message = f"""Task Context:
{task_context}

User Question: {question}

Provide detailed, actionable assistance including specific links, contact information, and step-by-step instructions."""

        messages.append({
            "role": "user",
            "content": current_message
        })

        # Get AI response
        print(f"[AI SERVICE] Calling LLM with {len(messages)} messages...")
        response_text = self.call_llm(system_prompt, messages=messages, response_format='json')
        print(f"[AI SERVICE] Raw AI response received ({len(response_text)} chars)")
        print(f"[AI SERVICE] First 500 chars of response: {response_text[:500]}")

        try:
            response_data = json.loads(response_text)
            print(f"[AI SERVICE] Successfully parsed JSON response")
            print(f"[AI SERVICE] Response keys: {response_data.keys()}")
            result = {
                'response': response_data.get('response', ''),
                'links': response_data.get('links', []),
                'contacts': response_data.get('contacts', []),
                'steps': response_data.get('steps', []),
                'can_expand': mode == 'clarify'  # Only clarify mode can expand to research
            }

            # Fallback: If links array is empty but response text mentions URLs, extract them
            if not result['links'] and result['response']:
                extracted_links = self._extract_urls_from_text(result['response'])
                if extracted_links:
                    print(f"[AI SERVICE] WARNING: AI didn't structure links properly. Extracted {len(extracted_links)} URLs from response text")
                    result['links'] = extracted_links

            print(f"[AI SERVICE] Returning result with {len(result['links'])} links, {len(result['contacts'])} contacts, {len(result['steps'])} steps")
            return result
        except json.JSONDecodeError as e:
            # Fallback if not JSON
            print(f"[AI SERVICE] ERROR: JSON parsing failed: {e}")
            print(f"[AI SERVICE] Returning plain text fallback")

            # Try to extract URLs from plain text
            extracted_links = self._extract_urls_from_text(response_text)

            return {
                'response': response_text,
                'links': extracted_links,
                'contacts': [],
                'steps': [],
                'can_expand': mode == 'clarify'
            }


# Singleton instance
ai_service = AIService(provider='openai' if settings.OPENAI_API_KEY else 'anthropic')
