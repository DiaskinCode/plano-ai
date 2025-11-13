"""
Intelligent Onboarding Agent - Phase 1

Hybrid AI agent that:
1. Conducts conversational onboarding
2. Answers user questions during onboarding
3. Detects intent (answering vs asking)
4. Extracts context intelligently
5. Avoids repeated questions
"""

import json
from typing import Dict, List, Optional
from ai.services import AIService


class IntelligentOnboardingAgent:
    """
    Phase 1: Intent Detection + Smart Extraction + Q&A

    Fixes the looping question bug by:
    - Detecting what user is doing (answering vs asking)
    - Not asking for data we already have
    - Answering user questions during onboarding
    """

    def __init__(self, category: str):
        """
        Initialize agent for a specific category.

        Args:
            category: One of 'career', 'study', 'sport', 'health', 'finance', 'networking'
        """
        self.category = category
        self.ai_service = AIService(provider='openai')

    def get_initial_message(self) -> str:
        """Get initial greeting for the category."""

        greetings = {
            'study': "Hey! I'm your AI study advisor. Tell me about your dream program - what do you want to study and where?",
            'career': "Hi! I'm your career coach. What role are you aiming for?",
            'sport': "Hey! Ready to crush your fitness goals? What are you working towards?",
            'health': "Hi there! I'm your wellness advisor. What's your health goal?",
            'finance': "Hey! Let's build your financial plan. What's your money goal?",
            'networking': "Hi! I'm here to expand your network. Who do you want to connect with?"
        }

        return greetings.get(self.category, "Hi! Tell me about your goal.")

    def process_message(
        self,
        user_message: str,
        conversation_history: List[Dict],
        extracted_data: Dict
    ) -> Dict:
        """
        Process user message with intent detection.

        Args:
            user_message: User's message
            conversation_history: Previous messages
            extracted_data: Data extracted so far

        Returns:
            {
                'ai_message': Response text,
                'extracted_data': Updated data,
                'is_complete': Whether onboarding is complete,
                'needs_confirmation': Whether to show confirmation
            }
        """
        # Step 0: Check if user is confirming the summary
        if extracted_data.get('needs_confirmation'):
            confirmation_words = ['yes', 'confirm', 'correct', 'looks good', 'perfect', 'yep', 'yeah', 'sure']
            if any(word in user_message.lower() for word in confirmation_words):
                print(f"[IntelligentAgent] User confirmed onboarding data")
                extracted_data['user_confirmed'] = True
                return {
                    'ai_message': "Perfect! Your plan is being created...",
                    'extracted_data': extracted_data,
                    'is_complete': True,
                    'needs_confirmation': False
                }

        # Step 1: Detect intent
        intent = self._detect_intent(user_message, conversation_history, extracted_data)

        print(f"[IntelligentAgent] Intent detected: {intent['primary_intent']}")

        # Step 2: Extract data (always runs in background)
        new_data = self._extract_data(user_message, conversation_history)

        # Merge extracted data
        for key, value in new_data.items():
            if value is not None and value != '':
                extracted_data[key] = value

        # Step 3: Generate response based on intent
        if intent['primary_intent'] == 'asking_question':
            # User is asking a question - answer it AND continue onboarding
            ai_message = self._answer_question_and_continue(
                user_message, extracted_data, conversation_history
            )
        else:
            # User is answering - acknowledge and ask next question
            ai_message = self._acknowledge_and_continue(
                user_message, extracted_data, conversation_history
            )

        # Step 4: Check if complete
        is_complete = self._is_complete(extracted_data)
        needs_confirmation = is_complete and not extracted_data.get('user_confirmed')

        if needs_confirmation:
            ai_message = self._generate_confirmation(extracted_data)
            extracted_data['needs_confirmation'] = True

        return {
            'ai_message': ai_message,
            'extracted_data': extracted_data,
            'is_complete': is_complete and extracted_data.get('user_confirmed', False),
            'needs_confirmation': needs_confirmation
        }

    def _detect_intent(
        self,
        user_message: str,
        conversation_history: List[Dict],
        extracted_data: Dict
    ) -> Dict:
        """
        Detect what user is trying to do.

        Returns:
            {
                'primary_intent': 'answering_onboarding' | 'asking_question' | 'general_chat',
                'confidence': 0.0-1.0
            }
        """
        # Get last AI message for context
        last_ai_message = ""
        for msg in reversed(conversation_history):
            if msg['role'] == 'assistant':
                last_ai_message = msg['content']
                break

        prompt = f"""Detect user's intent in this onboarding conversation.

Last AI message:
"{last_ai_message}"

User's response:
"{user_message}"

Current data collected: {json.dumps(list(extracted_data.keys()))}

Intent options:
1. answering_onboarding - User is answering AI's question
2. asking_question - User is asking AI a question
3. general_chat - Just chatting

Examples:

AI: "What universities are you interested in?"
User: "NYU, Stanford"
Intent: answering_onboarding

AI: "What universities are you interested in?"
User: "What GPA do I need for Stanford?"
Intent: asking_question

AI: "What universities are you interested in?"
User: "I'm interested in NYU Shanghai. What are the admission requirements?"
Intent: answering_onboarding (gives answer) + asking_question (asks follow-up)

Return JSON:
{{
    "primary_intent": "answering_onboarding|asking_question|general_chat",
    "has_question": true/false,
    "has_answer": true/false,
    "confidence": 0.0-1.0
}}
"""

        response = self.ai_service.call_llm(
            system_prompt="You are an intent detection system. Return only valid JSON.",
            user_prompt=prompt
        )

        try:
            intent = json.loads(response)
            return intent
        except:
            # Fallback: simple heuristic
            msg_lower = user_message.lower()
            question_words = ['what', 'how', 'when', 'where', 'why', 'which', 'who', 'can you', 'could you']
            has_question = any(q in msg_lower for q in question_words) or '?' in user_message

            return {
                'primary_intent': 'asking_question' if has_question else 'answering_onboarding',
                'has_question': has_question,
                'has_answer': not has_question,
                'confidence': 0.7
            }

    def _extract_data(
        self,
        user_message: str,
        conversation_history: List[Dict]
    ) -> Dict:
        """
        Extract user data from message.

        Returns:
            Dictionary with extracted fields
        """
        # Build extraction prompt based on category
        extraction_schema = self._get_extraction_schema()

        prompt = f"""Extract user information from this message.

Category: {self.category}

User message:
"{user_message}"

Extract any mentioned fields from this schema:
{json.dumps(extraction_schema, indent=2)}

Return JSON with ONLY the fields that are mentioned. Use null for fields not mentioned.

Example:
User: "I want to study CS at NYU and Stanford"
{{
    "field_of_study": "Computer Science",
    "target_schools": ["NYU", "Stanford"]
}}

Extract from the user message above:
"""

        response = self.ai_service.call_llm(
            system_prompt="You are a data extraction system. Return only valid JSON.",
            user_prompt=prompt
        )

        try:
            data = json.loads(response)
            # Clean null/empty values
            return {k: v for k, v in data.items() if v is not None and v != ''}
        except Exception as e:
            print(f"[IntelligentAgent] Extraction failed: {e}")
            return {}

    def _answer_question_and_continue(
        self,
        user_message: str,
        extracted_data: Dict,
        conversation_history: List[Dict]
    ) -> str:
        """
        Answer user's question AND continue onboarding.

        Returns:
            AI response that answers question + asks next onboarding question
        """
        # Determine next missing field
        next_field = self._get_next_missing_field(extracted_data)

        prompt = f"""You are an expert onboarding assistant for {self.category}.

User context (what you know):
{json.dumps(extracted_data, indent=2)}

User's question:
"{user_message}"

Your task:
1. Answer their question directly and helpfully
2. Keep answer concise (2-3 sentences max)
3. Then smoothly ask about: {next_field}

Example:
User: "What GPA do I need for Stanford?"
Response: "Stanford typically admits students with 3.7+ GPA, but with strong projects/experience, 3.5+ is competitive.

Now, what's YOUR current GPA? This helps me recommend the right universities."

Generate helpful response that answers their question AND continues onboarding:
"""

        return self.ai_service.call_llm(
            system_prompt=f"You are a helpful {self.category} advisor conducting onboarding.",
            user_prompt=prompt
        )

    def _acknowledge_and_continue(
        self,
        user_message: str,
        extracted_data: Dict,
        conversation_history: List[Dict]
    ) -> str:
        """
        Acknowledge user's answer and ask next question.

        Returns:
            AI response
        """
        # Check what we just extracted
        next_field = self._get_next_missing_field(extracted_data)

        # If no missing fields, we're done - generate confirmation
        if not next_field:
            return self._generate_confirmation(extracted_data)

        prompt = f"""You are conducting {self.category} onboarding.

What you know about user:
{json.dumps(extracted_data, indent=2)}

User just said:
"{user_message}"

Next missing field: {next_field}

Your task:
1. Acknowledge what they just shared (be specific!)
2. Ask about the next missing field: {next_field}
3. Keep it natural and conversational

Example:
User: "NYU, Stanford, and MIT"
You know: {{"target_schools": ["NYU", "Stanford", "MIT"]}}
Next field: budget

Response: "Excellent choices - NYU, Stanford, and MIT are all top-tier!

What's your budget per year? This helps me understand your financial constraints."

Generate natural response:
"""

        return self.ai_service.call_llm(
            system_prompt=f"You are a friendly {self.category} onboarding assistant.",
            user_prompt=prompt
        )

    def _get_next_missing_field(self, extracted_data: Dict) -> Optional[str]:
        """
        Get next field to ask about.

        Returns:
            Field name or None if all collected
        """
        required_fields = self._get_required_fields()

        for field in required_fields:
            if field not in extracted_data or not extracted_data[field]:
                return field

        return None

    def _get_required_fields(self) -> List[str]:
        """Get required fields for category."""

        if self.category == 'study':
            return [
                'field_of_study',
                'degree_level',
                'target_country',
                'budget',
                'timeline',
                'gpa',
                'test_scores'
            ]
        elif self.category == 'career':
            return [
                'target_role',
                'current_situation',
                'timeline',
                'years_experience'
            ]
        else:
            return ['goal_type', 'timeline']

    def _get_extraction_schema(self) -> Dict:
        """Get extraction schema for category."""

        if self.category == 'study':
            return {
                'field_of_study': 'string',
                'degree_level': 'bachelor|master|phd',
                'target_country': 'string',
                'target_schools': 'list[string]',
                'budget': 'string',
                'timeline': 'string',
                'gpa': 'string',
                'test_scores': 'dict',
                'coding_experience': 'string',
                'research_interests': 'string',
                'startup_experience': 'string',
                'work_experience': 'string',
                'sports_achievements': 'string',
                'notable_achievements': 'string',
                'extracurriculars': 'string'
            }
        elif self.category == 'career':
            return {
                'target_role': 'string',
                'current_role': 'string',
                'current_situation': 'student|employed|unemployed',
                'years_experience': 'number',
                'tech_stack': 'list[string]',
                'target_companies': 'list[string]',
                'timeline': 'string'
            }
        else:
            return {'goal_type': 'string', 'timeline': 'string'}

    def _is_complete(self, extracted_data: Dict) -> bool:
        """Check if onboarding is complete."""

        required = self._get_required_fields()

        # Check if at least 70% of required fields are filled
        filled = sum(1 for f in required if f in extracted_data and extracted_data[f])

        return filled >= len(required) * 0.7

    def _generate_confirmation(self, data: Dict) -> str:
        """Generate confirmation message."""

        if self.category == 'study':
            # Build confirmation message
            msg = f"""Perfect! Let me confirm what I have:

✓ Goal: {data.get('degree_level', 'Degree')} in {data.get('field_of_study', 'N/A')}
✓ Target: {data.get('target_country', 'N/A')}
{f"✓ Schools: {', '.join(data.get('target_schools', [])[:3])}" if data.get('target_schools') else ''}
✓ Budget: {data.get('budget', 'N/A')}/year
✓ Timeline: {data.get('timeline', 'N/A')}
{f"✓ GPA: {data.get('gpa', 'N/A')}" if data.get('gpa') else ''}"""

            # Add achievements/experience section if any exist
            achievements = []
            if data.get('startup_experience'):
                achievements.append(f"Startup: {data.get('startup_experience')}")
            if data.get('work_experience'):
                achievements.append(f"Work: {data.get('work_experience')}")
            if data.get('sports_achievements'):
                achievements.append(f"Sports: {data.get('sports_achievements')}")
            if data.get('notable_achievements'):
                achievements.append(f"Achievement: {data.get('notable_achievements')}")
            if data.get('extracurriculars'):
                achievements.append(f"Extracurriculars: {data.get('extracurriculars')}")

            if achievements:
                msg += "\n\n✨ Notable Experience:\n"
                for achievement in achievements:
                    msg += f"✓ {achievement}\n"

            msg += "\nReply 'yes' to generate your personalized plan!"
            return msg

        else:
            return f"""Great! Here's what I have:

✓ Goal: {data.get('target_role', data.get('goal_type', 'N/A'))}
✓ Timeline: {data.get('timeline', 'N/A')}

Ready to create your plan? Reply 'yes' to continue!"""
