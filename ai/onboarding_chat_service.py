"""
Onboarding Chat Service

Handles conversational onboarding for all categories using AI extraction.
"""

import json
from typing import Dict, List, Tuple
from ai.services import AIService
from ai.onboarding_prompts import (
    INITIAL_MESSAGES,
    SYSTEM_PROMPTS,
    EXTRACTION_FUNCTION,
    REQUIRED_DATA,
    OPTIONAL_DATA
)


class OnboardingChatService:
    """
    Service for conversational onboarding.

    Handles:
    1. Initial greeting
    2. Natural conversation with user
    3. Data extraction via OpenAI function calling
    4. Completeness checking
    5. Confirmation generation
    """

    def __init__(self, category: str):
        """
        Initialize service for a specific category.

        Args:
            category: One of 'career', 'study', 'sport', 'health', 'finance', 'networking'
        """
        if category not in REQUIRED_DATA:
            raise ValueError(f"Invalid category: {category}. Must be one of {list(REQUIRED_DATA.keys())}")

        self.category = category
        self.ai_service = AIService()
        self.required_fields = REQUIRED_DATA[category]
        self.optional_fields = OPTIONAL_DATA[category]

    def get_initial_message(self) -> str:
        """
        Get category-specific greeting message.

        Returns:
            Initial AI greeting for the category
        """
        return INITIAL_MESSAGES[self.category]

    def process_message(
        self,
        message: str,
        conversation_history: List[Dict],
        extracted_data: Dict
    ) -> Dict:
        """
        Process user message and return AI response.

        Args:
            message: User's message text
            conversation_history: Previous messages [{'role': 'user/assistant', 'content': '...'}]
            extracted_data: Data extracted so far

        Returns:
            {
                'ai_message': AI's response text,
                'extracted_data': Updated extracted data,
                'is_complete': Whether onboarding is complete,
                'needs_confirmation': Whether user needs to confirm
            }
        """
        # Add user message to history
        conversation_history.append({'role': 'user', 'content': message})

        # Check if user is confirming
        if extracted_data.get('needs_confirmation'):
            if self._is_confirmation(message):
                extracted_data['user_confirmed'] = True
                return {
                    'ai_message': 'Perfect! Creating your personalized plan...',
                    'extracted_data': extracted_data,
                    'is_complete': True,
                    'needs_confirmation': False
                }
            else:
                # User wants to edit
                extracted_data['needs_confirmation'] = False
                extracted_data['user_confirmed'] = False
                return {
                    'ai_message': 'No problem! What would you like to change?',
                    'extracted_data': extracted_data,
                    'is_complete': False,
                    'needs_confirmation': False
                }

        # Call LLM to continue conversation and extract data
        try:
            system_prompt = SYSTEM_PROMPTS[self.category]

            # Build messages for OpenAI (don't add system to messages, pass it separately)
            messages = conversation_history

            # Call OpenAI with function calling (required to force extraction on every message)
            response = self.ai_service.call_llm(
                system_prompt=system_prompt,
                messages=messages,
                functions=[EXTRACTION_FUNCTION],
                function_call='required'
            )

            # Extract data from function call if present
            if isinstance(response, dict) and 'tool_calls' in response:
                try:
                    for tool_call in response['tool_calls']:
                        function_args = tool_call['function'].get('arguments', '{}')
                        if isinstance(function_args, str):
                            new_data = json.loads(function_args)
                        else:
                            new_data = function_args

                        # Clean the extracted data (remove N/A values, fix parsing errors)
                        new_data = self._clean_extracted_data(new_data)

                        # Update extracted_data with new fields
                        for key, value in new_data.items():
                            if value is not None and value != '':
                                extracted_data[key] = value

                        print(f"[OnboardingChat] Extracted new data: {list(new_data.keys())}")

                        # Validate that background keywords triggered extraction
                        self._validate_background_extraction(message, extracted_data)

                except json.JSONDecodeError as e:
                    print(f"[OnboardingChat] Failed to parse function args: {e}")

            # Get AI's text response
            if isinstance(response, dict):
                ai_message = response.get('content', '')
            elif isinstance(response, str):
                ai_message = response
            else:
                ai_message = "I understand. Please tell me more."

            # If AI didn't provide a message (happens with function_call='required'),
            # generate an intelligent follow-up based on what we're missing
            if not ai_message or len(ai_message.strip()) == 0:
                ai_message = self._generate_follow_up_question(extracted_data)

            # Check if we have sufficient data
            is_sufficient, missing = self._check_sufficiency(extracted_data)

            # If NOT sufficient, generate explicit follow-up questions for missing fields
            if not is_sufficient and len(missing) > 0:
                # Generate targeted questions for missing required fields
                follow_up = self._generate_missing_fields_questions(extracted_data, missing)
                if follow_up:
                    print(f"[OnboardingChat] Data insufficient - asking for missing fields: {missing}")
                    return {
                        'ai_message': follow_up,
                        'extracted_data': extracted_data,
                        'is_complete': False,
                        'needs_confirmation': False
                    }

            # If sufficient and not yet confirmed, validate conversation before confirmation
            if is_sufficient and not extracted_data.get('user_confirmed'):
                # CRITICAL: Validate that conversation mentions were extracted
                validation_result = self._validate_conversation_extraction(conversation_history, extracted_data)

                if not validation_result['valid']:
                    # Don't confirm yet - ask clarifying question about missed background
                    print(f"[OnboardingChat] Blocking confirmation - background validation failed")
                    return {
                        'ai_message': validation_result['prompt'],
                        'extracted_data': extracted_data,
                        'is_complete': False,
                        'needs_confirmation': False
                    }

                # Validation passed - generate confirmation
                confirmation = self._generate_confirmation(extracted_data)
                extracted_data['needs_confirmation'] = True
                return {
                    'ai_message': confirmation,
                    'extracted_data': extracted_data,
                    'is_complete': False,
                    'needs_confirmation': True
                }

            # Otherwise continue conversation
            return {
                'ai_message': ai_message,
                'extracted_data': extracted_data,
                'is_complete': False,
                'needs_confirmation': False
            }

        except Exception as e:
            print(f"[OnboardingChat] Error processing message: {e}")
            import traceback
            traceback.print_exc()

            # Fallback response
            return {
                'ai_message': "I'm having trouble understanding. Could you share a bit more detail about your goal?",
                'extracted_data': extracted_data,
                'is_complete': False,
                'needs_confirmation': False
            }

    def _generate_missing_fields_questions(self, data: Dict, missing_fields: List[str]) -> str:
        """
        Generate explicit follow-up questions for missing required fields.

        Args:
            data: Currently extracted data
            missing_fields: List of missing field names

        Returns:
            Formatted question string or None
        """
        # Filter out the meta field
        actual_missing = [f for f in missing_fields if f != 'need_at_least_2_optional_fields']

        if len(actual_missing) == 0:
            return None

        # Acknowledge what we have
        intro = "Great start!"
        if self.category == 'study':
            if data.get('target_country'):
                intro = f"Perfect! You want to study in {data['target_country']}."
            if data.get('gpa'):
                intro += f" Your GPA is {data.get('gpa')}."
            if data.get('test_scores'):
                intro += f" Test scores: {data.get('test_scores')}."

        # Map field names to human-readable questions
        field_questions = {
            # Study fields
            'degree_level': "What degree are you pursuing? (Bachelor's, Master's, PhD, etc.)",
            'field_of_study': "In what field/major? (e.g., Computer Science, Business, Engineering)",
            'budget': "What's your budget per year? (e.g., '$30,000', '£20,000')",
            'timeline': "When do you want to start? (e.g., 'Fall 2026', 'September 2025')",
            'gpa': "What's your current GPA? (e.g., '3.5/4.0', '85%')",
            'test_scores': "Do you have test scores? (SAT, IELTS, TOEFL, GRE - or planning to take them)",
            'target_schools': "Any specific universities you're interested in?",

            # Career fields
            'current_situation': "What's your current situation? (student/employed/unemployed)",
            'goal_type': "What's your career goal? (first job/switch role/promotion/career change)",
            'target_role': "What role are you targeting?",
            'work_history': "What companies have you worked at? (roles and key accomplishments)",
            'projects': "What have you built? (side projects, portfolio pieces with metrics)",
            'courses_certifications': "Any relevant courses or certifications? (AWS, bootcamps, etc.)",
            'education_background': "What's your educational background? (degrees, schools)",

            # Sport fields
            'fitness_goal_type': "What's your fitness goal? (lose weight/build muscle/run marathon/etc.)",
            'fitness_level': "What's your current fitness level? (beginner/intermediate/advanced)",

            # Health fields
            'health_goal': "What's your health goal?",
            'current_health_status': "What's your current health status?",

            # Finance fields
            'financial_goal': "What's your financial goal? (save money/invest/reduce debt/etc.)",
            'target_amount': "What's your target amount?",

            # Networking fields
            'networking_goal': "What's your networking goal?",
            'industry': "What industry are you in?"
        }

        # Generate questions for missing fields (max 3 at a time)
        questions = []
        for field in actual_missing[:3]:
            if field in field_questions:
                questions.append(f"• {field_questions[field]}")

        if len(questions) == 0:
            return None

        questions_text = '\n'.join(questions)

        return f"""{intro}

A few more details I need:

{questions_text}

The more I know, the better plan I can create!"""

    def _generate_follow_up_question(self, data: Dict) -> str:
        """
        Generate an intelligent follow-up question based on what data we have.
        This is used when OpenAI doesn't provide a text response (function_call='required').

        Args:
            data: Extracted data so far

        Returns:
            Follow-up question string
        """
        # Check what's missing
        missing_required = [f for f in self.required_fields if f not in data or not data[f]]

        # Category-specific follow-ups
        if self.category == 'career':
            if 'target_role' not in data or not data['target_role']:
                return "Got it! What role are you aiming for?"
            if 'timeline' not in data or not data['timeline']:
                return "Perfect! When do you want to achieve this goal?"
            if 'current_situation' not in data or not data['current_situation']:
                return "Thanks! Are you currently employed, studying, or looking for your first job?"

            # PROACTIVELY ask about work history, projects, courses, education
            if 'work_history' not in data or not data['work_history']:
                return "Great! Now let's capture your work history. What companies have you worked at? Tell me about your roles and what you accomplished there."
            if 'projects' not in data or not data['projects']:
                return "What have you built? Any side projects, open-source contributions, or portfolio pieces? (Include metrics if you have them - users, revenue, stars, etc.)"
            if 'courses_certifications' not in data or not data['courses_certifications']:
                return "Any relevant courses, certifications, or training programs you've completed? (e.g., AWS Certified, bootcamps, online courses)"
            if 'education_background' not in data or not data['education_background']:
                return "What's your educational background? (Degrees, schools, graduation years)"

            return "Great! Tell me more about your target companies or any other preferences."

        elif self.category == 'study':
            if 'field_of_study' not in data or not data['field_of_study']:
                return "Excellent! What field or subject do you want to study?"
            if 'target_country' not in data or not data['target_country']:
                return "Perfect! Which country or region are you considering for studying?"
            if 'gpa' not in data or not data['gpa']:
                return "Got it! What's your current GPA or grade average?"
            if 'test_scores' not in data or not data['test_scores']:
                return "Great! Do you have SAT/IELTS/TOEFL scores? Or are you planning to take them?"
            if 'timeline' not in data or not data['timeline']:
                return "Perfect! When are you planning to start? (e.g., Fall 2026)"
            if 'budget' not in data or not data['budget']:
                # Check if field requires coding - ask about that first
                field = data.get('field_of_study', '').lower()
                if any(keyword in field for keyword in ['ai', 'ml', 'computer', 'cs', 'software', 'engineering']):
                    if 'coding_experience' not in data or not data['coding_experience']:
                        return "Awesome! For tech fields, coding experience matters. Do you have programming background?"
                return "Thanks! What's your budget range per year?"

            # Budget validation check
            budget_str = str(data.get('budget', '')).lower()
            target_country = str(data.get('target_country', '')).lower()
            if budget_str and target_country == 'us':
                # Extract number from budget
                import re
                numbers = re.findall(r'\d+', budget_str.replace(',', ''))
                if numbers:
                    budget_num = int(numbers[0])
                    if budget_num < 15000:
                        return "⚠️ Quick note: US universities typically cost $30k-60k/year. With a ${}k budget, are you looking for full scholarships or considering community college → transfer pathway?".format(budget_num // 1000)

            return "Great! Tell me more about your target universities or any specific preferences."

        elif self.category == 'sport':
            if 'fitness_goal_type' not in data or not data['fitness_goal_type']:
                return "Awesome! What specific fitness goal do you have in mind?"
            if 'timeline' not in data or not data['timeline']:
                return "Perfect! What's your target timeframe?"
            return "Great! Tell me more about your current fitness level and any constraints."

        elif self.category == 'health':
            if 'fitness_goal_type' not in data or not data['fitness_goal_type']:
                return "Excellent! What health goal are you working towards?"
            if 'timeline' not in data or not data['timeline']:
                return "Got it! When do you want to achieve this?"
            return "Perfect! Tell me about your current health situation and any medical considerations."

        elif self.category == 'finance':
            if 'goal_type' not in data or not data['goal_type']:
                return "Great! What financial goal do you have? (saving, investing, debt reduction, etc.)"
            if 'timeline' not in data or not data['timeline']:
                return "Perfect! What's your timeline for this goal?"
            return "Excellent! Share more details about your financial situation and target."

        elif self.category == 'networking':
            if 'goal_type' not in data or not data['goal_type']:
                return "Awesome! What networking goal do you have? (expand network, find mentor, etc.)"
            if 'timeline' not in data or not data['timeline']:
                return "Got it! What's your timeframe?"
            return "Great! Tell me about your current network and who you want to connect with."

        # Generic fallback
        return "I understand. Tell me more about your goal and when you'd like to achieve it."

    def _validate_background_extraction(self, message: str, data: Dict):
        """
        Validate that background keywords in message triggered proper extraction.
        Logs warnings if keywords are detected but not extracted.

        Args:
            message: User's message text
            data: Currently extracted data
        """
        msg_lower = message.lower()

        # Startup/entrepreneurship keywords
        startup_keywords = ['startup', 'founder', 'co-founder', 'started', 'company', 'business',
                           'launched', 'my app', 'my product', 'my agency']
        has_startup_mention = any(kw in msg_lower for kw in startup_keywords)

        if has_startup_mention and not data.get('has_startup_background'):
            print(f"⚠️  [OnboardingChat] WARNING: Startup keywords detected but not extracted!")
            print(f"   Message: {message[:150]}")
            print(f"   Keywords found: {[kw for kw in startup_keywords if kw in msg_lower]}")

        # Work experience/achievements keywords
        work_keywords = ['engineer at', 'worked at', 'developer at', 'designer at',
                        'built', 'created', 'developed', 'users', 'customers', 'clients']
        has_work_mention = any(kw in msg_lower for kw in work_keywords)

        if has_work_mention:
            has_extracted = (data.get('has_notable_achievements') or
                           data.get('achievement_details') or
                           data.get('impressive_projects'))
            if not has_extracted:
                print(f"⚠️  [OnboardingChat] WARNING: Work/achievement keywords detected but not extracted!")
                print(f"   Message: {message[:150]}")
                print(f"   Keywords found: {[kw for kw in work_keywords if kw in msg_lower]}")

        # Research keywords
        research_keywords = ['research', 'paper', 'published', 'professor', 'lab', 'thesis']
        has_research_mention = any(kw in msg_lower for kw in research_keywords)

        if has_research_mention and not data.get('has_research_background'):
            print(f"⚠️  [OnboardingChat] WARNING: Research keywords detected but not extracted!")
            print(f"   Message: {message[:150]}")
            print(f"   Keywords found: {[kw for kw in research_keywords if kw in msg_lower]}")

    def _validate_conversation_extraction(self, history: List[Dict], data: Dict) -> Dict:
        """
        Validate extraction against full conversation history.
        Returns validation result with prompt if invalid.

        Args:
            history: Full conversation history
            data: Extracted data

        Returns:
            {'valid': True} or {'valid': False, 'prompt': '...'}
        """
        # Combine all user messages
        user_text = ' '.join([m['content'].lower() for m in history if m['role'] == 'user'])

        # Check for startup/entrepreneurship mentions
        startup_keywords = ['startup', 'founder', 'co-founder', 'started', 'company', 'business',
                           'launched', 'my app', 'my product', 'my agency']
        has_startup_mention = any(kw in user_text for kw in startup_keywords)

        if has_startup_mention and not data.get('has_startup_background'):
            print(f"🚨 [OnboardingChat] CRITICAL: Conversation mentions startup but not extracted!")
            return {
                'valid': False,
                'prompt': "Wait - you mentioned a startup/company earlier! Let me make sure I got this right:\n\n• What exactly did you build/found?\n• How many users or customers do you have?\n• What's your role?\n\nThis is REALLY important for your plan - startup experience is extremely valuable!"
            }

        # Check for work experience mentions
        work_keywords = ['engineer at', 'worked at', 'developer at', 'designer at']
        has_work_mention = any(kw in user_text for kw in work_keywords)

        if has_work_mention:
            has_extracted = (data.get('has_notable_achievements') or
                           data.get('achievement_details') or
                           data.get('impressive_projects'))
            if not has_extracted:
                print(f"🚨 [OnboardingChat] CRITICAL: Conversation mentions work but not extracted!")
                return {
                    'valid': False,
                    'prompt': "Hold on - you mentioned working at a company! Tell me more:\n\n• What company and your role?\n• What did you work on?\n• Any impact metrics? (users, performance, scale)\n\nThis experience will strengthen your application significantly!"
                }

        # Check for project/building mentions with metrics
        project_keywords = ['built', 'created', 'developed', 'users', 'customers', 'clients']
        has_project_mention = any(kw in user_text for kw in project_keywords)

        if has_project_mention:
            has_extracted = (data.get('impressive_projects') or
                           data.get('achievement_details') or
                           data.get('has_notable_achievements'))
            if not has_extracted:
                print(f"🚨 [OnboardingChat] CRITICAL: Conversation mentions projects/users but not extracted!")
                return {
                    'valid': False,
                    'prompt': "Wait - you mentioned building something! This could be really valuable:\n\n• What did you build?\n• How many users/customers?\n• Any interesting metrics or results?\n\nLet me capture this properly!"
                }

        # Check for research mentions
        research_keywords = ['research', 'paper', 'published', 'professor', 'lab']
        has_research_mention = any(kw in user_text for kw in research_keywords)

        if has_research_mention and not data.get('has_research_background'):
            print(f"🚨 [OnboardingChat] CRITICAL: Conversation mentions research but not extracted!")
            return {
                'valid': False,
                'prompt': "You mentioned research experience! Tell me about it:\n\n• What field of research?\n• Any publications?\n• Working with any professors?\n\nResearch experience is highly valued!"
            }

        return {'valid': True}

    def _clean_extracted_data(self, data: Dict) -> Dict:
        """
        Clean up extraction errors like N/A values and parsing artifacts.

        Args:
            data: Extracted data dictionary

        Returns:
            Cleaned data dictionary
        """
        cleaned = {}

        for key, value in data.items():
            # Handle lists (fix N/A parsing bug)
            if isinstance(value, list):
                # Remove N/A artifacts: ['N', '/', 'A'] or ['N/A']
                cleaned_list = [
                    v for v in value
                    if v not in ['N', 'A', '/', 'N/A', 'n/a', 'NA', 'na', '', None]
                ]
                if len(cleaned_list) == 0:
                    cleaned[key] = None  # Empty list → None
                else:
                    cleaned[key] = cleaned_list

            # Handle strings (convert N/A to None)
            elif isinstance(value, str):
                stripped = value.strip()
                if stripped.upper() in ['N/A', 'NA', 'N / A', '']:
                    cleaned[key] = None
                else:
                    cleaned[key] = value

            # Keep other types as-is
            else:
                cleaned[key] = value

        return cleaned

    def _check_sufficiency(self, data: Dict) -> Tuple[bool, List[str]]:
        """
        Check if we have enough data to create a plan.

        Args:
            data: Extracted data so far

        Returns:
            (is_sufficient, missing_fields)
        """
        missing = []

        # Check all required fields
        for field in self.required_fields:
            value = data.get(field)
            # Reject if: missing, empty, None, or "N/A"
            if not value or value in ['N/A', 'n/a', 'NA', 'na', 'N / A']:
                missing.append(field)
                print(f"[OnboardingChat] Missing required field: {field} (value: {value})")

        # Check we have at least 2 optional fields (excluding N/A values)
        optional_count = sum(
            1 for field in self.optional_fields
            if field in data and data[field] and data[field] not in ['N/A', 'n/a', 'NA', 'na', 'N / A']
        )

        if optional_count < 2:
            missing.append('need_at_least_2_optional_fields')
            print(f"[OnboardingChat] Only {optional_count} optional fields (need 2)")

        is_sufficient = len(missing) == 0
        print(f"[OnboardingChat] Sufficiency check: {is_sufficient} (missing: {missing})")

        return (is_sufficient, missing)

    def _generate_confirmation(self, data: Dict) -> str:
        """
        Generate confirmation message for user to review.

        Args:
            data: Extracted data

        Returns:
            Confirmation message text
        """
        if self.category == 'career':
            return self._career_confirmation(data)
        elif self.category == 'study':
            return self._study_confirmation(data)
        elif self.category == 'sport':
            return self._sport_confirmation(data)
        elif self.category == 'health':
            return self._health_confirmation(data)
        elif self.category == 'finance':
            return self._finance_confirmation(data)
        elif self.category == 'networking':
            return self._networking_confirmation(data)
        else:
            return self._generic_confirmation(data)

    def _add_background_section(self, data: Dict) -> list:
        """
        Generate background discovery section for confirmation.
        Returns list of lines to add to confirmation message.
        """
        lines = []
        has_background = False

        if data.get('has_startup_background') and data.get('startup_details'):
            lines.append("\n⭐ EXCEPTIONAL BACKGROUND:")
            lines.append(f"  • Startup: {data['startup_details']}")
            has_background = True

        if data.get('has_research_background') and data.get('research_details'):
            if not has_background:
                lines.append("\n⭐ EXCEPTIONAL BACKGROUND:")
                has_background = True
            lines.append(f"  • Research: {data['research_details']}")

        if data.get('has_notable_achievements') and data.get('achievement_details'):
            if not has_background:
                lines.append("\n⭐ EXCEPTIONAL BACKGROUND:")
                has_background = True
            lines.append(f"  • Achievements: {data['achievement_details']}")

        if data.get('impressive_projects'):
            if not has_background:
                lines.append("\n⭐ EXCEPTIONAL BACKGROUND:")
                has_background = True
            for project in data['impressive_projects'][:2]:
                lines.append(f"  • Project: {project}")

        # Add competitive advantage note if background exists
        if has_background:
            lines.append("\n🎯 YOUR COMPETITIVE ADVANTAGE:")
            if data.get('has_startup_background'):
                lines.append("  Your entrepreneurship experience is highly valuable.")
            if data.get('impressive_projects'):
                lines.append("  Building real products shows exceptional ability.")
            if data.get('has_research_background'):
                lines.append("  Research experience demonstrates deep expertise.")

        return lines

    def _career_confirmation(self, data: Dict) -> str:
        """Generate career confirmation"""
        lines = ["Perfect! Let me confirm what I've gathered:\n"]

        if data.get('current_role'):
            lines.append(f"✓ Current: {data['current_role']}")
            if data.get('years_experience'):
                lines[-1] += f" with {data['years_experience']} years experience"

        # Work history (show companies, not full details)
        if data.get('work_history'):
            companies = []
            for job in data['work_history'][:3]:
                if isinstance(job, dict) and job.get('company'):
                    company_str = job['company']
                    if job.get('role'):
                        company_str += f" ({job['role']})"
                    companies.append(company_str)
                elif isinstance(job, str):
                    companies.append(job)
            if companies:
                lines.append(f"✓ Work history: {', '.join(companies)}")

        # Education background
        if data.get('education_background'):
            edu_list = []
            for edu in data['education_background'][:2]:
                if isinstance(edu, dict):
                    edu_str = edu.get('degree', '')
                    if edu.get('institution'):
                        edu_str += f" - {edu['institution']}"
                    edu_list.append(edu_str)
                elif isinstance(edu, str):
                    edu_list.append(edu)
            if edu_list:
                lines.append(f"✓ Education: {', '.join(edu_list)}")

        # Courses and certifications
        if data.get('courses_certifications'):
            certs = data['courses_certifications'][:4]
            if isinstance(certs, list):
                certs_str = ', '.join([c if isinstance(c, str) else str(c) for c in certs])
                lines.append(f"✓ Courses & Certs: {certs_str}")

        # Projects with metrics
        if data.get('projects'):
            project_strs = []
            for proj in data['projects'][:2]:
                if isinstance(proj, dict):
                    proj_str = proj.get('name', '')
                    if proj.get('metrics'):
                        proj_str += f" ({proj['metrics']})"
                    project_strs.append(proj_str)
                elif isinstance(proj, str):
                    project_strs.append(proj)
            if project_strs:
                lines.append(f"✓ Projects: {', '.join(project_strs)}")

        if data.get('tech_stack'):
            tech = ', '.join(data['tech_stack'][:5])
            lines.append(f"✓ Tech stack: {tech}")
        elif data.get('design_tools'):
            tools = ', '.join(data['design_tools'][:5])
            lines.append(f"✓ Design tools: {tools}")

        if data.get('target_role'):
            lines.append(f"✓ Goal: {data['target_role']}")
            if data.get('target_companies'):
                companies = ', '.join(data['target_companies'][:3])
                lines[-1] += f" at {companies}"

        if data.get('timeline'):
            lines.append(f"✓ Timeline: {data['timeline']}")

        if data.get('notable_achievements'):
            lines.append(f"✓ Notable work: {data['notable_achievements'][0]}")

        # Background discovery fields (CRITICAL - show prominently)
        has_background = False
        if data.get('has_startup_background') and data.get('startup_details'):
            lines.append(f"\n⭐ STARTUP BACKGROUND:")
            lines.append(f"  • {data['startup_details']}")
            has_background = True

        if data.get('has_notable_achievements') and data.get('achievement_details'):
            lines.append(f"\n⭐ ACHIEVEMENTS:")
            lines.append(f"  • {data['achievement_details']}")
            has_background = True

        if data.get('impressive_projects'):
            lines.append(f"\n⭐ IMPRESSIVE PROJECTS:")
            for project in data['impressive_projects'][:3]:
                lines.append(f"  • {project}")
            has_background = True

        # Show competitive advantage if background exists
        if has_background:
            lines.append("\n🎯 YOUR COMPETITIVE ADVANTAGE:")
            if data.get('has_startup_background'):
                lines.append("  Your entrepreneurship experience is HIGHLY valuable for career transitions.")
            if data.get('impressive_projects') or data.get('achievement_details'):
                lines.append("  Building real products/achieving results shows exceptional ability.")

        lines.append("\nDoes this look right? Reply 'yes' to generate your plan, or correct any details.")

        return '\n'.join(lines)

    def _study_confirmation(self, data: Dict) -> str:
        """Generate study confirmation"""
        lines = ["Great! Here's what I have:\n"]

        if data.get('degree_level') and data.get('field_of_study'):
            lines.append(f"✓ Goal: {data['degree_level'].title()} in {data['field_of_study']}")

        if data.get('target_country'):
            lines.append(f"✓ Target country: {data['target_country']}")

        if data.get('budget'):
            lines.append(f"✓ Budget: {data['budget']}/year")

        if data.get('timeline'):
            lines.append(f"✓ Timeline: {data['timeline']}")

        if data.get('current_education'):
            lines.append(f"✓ Background: {data['current_education']}")
            if data.get('gpa'):
                lines[-1] += f", GPA {data['gpa']}"

        if data.get('target_schools'):
            schools = ', '.join(data['target_schools'][:3])
            lines.append(f"✓ Target schools: {schools}")

        # Background discovery fields (CRITICAL for admissions - show prominently)
        has_background = False
        if data.get('has_startup_background') and data.get('startup_details'):
            lines.append(f"\n⭐ EXCEPTIONAL BACKGROUND:")
            lines.append(f"  • Startup: {data['startup_details']}")
            has_background = True

        if data.get('has_research_background') and data.get('research_details'):
            if not has_background:
                lines.append(f"\n⭐ EXCEPTIONAL BACKGROUND:")
                has_background = True
            lines.append(f"  • Research: {data['research_details']}")

        if data.get('has_notable_achievements') and data.get('achievement_details'):
            if not has_background:
                lines.append(f"\n⭐ EXCEPTIONAL BACKGROUND:")
                has_background = True
            lines.append(f"  • Achievements: {data['achievement_details']}")

        if data.get('impressive_projects'):
            if not has_background:
                lines.append(f"\n⭐ EXCEPTIONAL BACKGROUND:")
                has_background = True
            for project in data['impressive_projects'][:2]:
                lines.append(f"  • Project: {project}")

        # Show competitive advantage if background exists (CRITICAL for study applications)
        if has_background:
            lines.append("\n🎯 YOUR COMPETITIVE ADVANTAGE:")
            gpa_str = data.get('gpa', '').lower()
            if data.get('has_startup_background'):
                lines.append("  Your entrepreneurship/founder experience is EXTREMELY valuable for admissions.")
                if '3.3' in gpa_str or '3.2' in gpa_str or '3.1' in gpa_str:
                    lines.append("  This can significantly compensate for GPA and make you competitive for top schools!")
            if data.get('impressive_projects'):
                lines.append("  Building real products with users shows exceptional technical ability.")
            if data.get('has_research_background'):
                lines.append("  Research experience is highly valued, especially for graduate programs.")
            lines.append("  Your application will focus on what makes you unique, not just grades.")

        lines.append("\nLook good? Reply 'yes' to build your plan, or let me know what to change.")

        return '\n'.join(lines)

    def _sport_confirmation(self, data: Dict) -> str:
        """Generate sport confirmation"""
        lines = ["Awesome! Let me confirm:\n"]

        if data.get('fitness_goal_type'):
            goal = data['fitness_goal_type'].replace('_', ' ').title()
            lines.append(f"✓ Goal: {goal}")

        if data.get('fitness_level'):
            lines.append(f"✓ Current level: {data['fitness_level'].title()}")

        if data.get('timeline'):
            lines.append(f"✓ Timeline: {data['timeline']}")

        if data.get('gym_access'):
            lines.append(f"✓ Gym access: {'Yes' if data['gym_access'] else 'No'}")

        if data.get('equipment'):
            equip = ', '.join(data['equipment'][:3])
            lines.append(f"✓ Equipment: {equip}")

        if data.get('specific_fitness_target'):
            lines.append(f"✓ Target: {data['specific_fitness_target']}")

        # Add background discovery section
        lines.extend(self._add_background_section(data))

        lines.append("\nReady to build your training plan? Reply 'yes' or make any corrections.")

        return '\n'.join(lines)

    def _health_confirmation(self, data: Dict) -> str:
        """Generate health confirmation"""
        lines = ["Great! Here's your health plan summary:\n"]

        if data.get('health_goal'):
            lines.append(f"✓ Goal: {data['health_goal']}")

        if data.get('current_health_status'):
            lines.append(f"✓ Current status: {data['current_health_status']}")

        if data.get('timeline'):
            lines.append(f"✓ Timeline: {data['timeline']}")

        # Add background discovery section
        lines.extend(self._add_background_section(data))

        lines.append("\nReady to create your wellness plan? Reply 'yes' to continue.")

        return '\n'.join(lines)

    def _finance_confirmation(self, data: Dict) -> str:
        """Generate finance confirmation"""
        lines = ["Perfect! Your financial plan:\n"]

        if data.get('financial_goal'):
            goal = data['financial_goal'].replace('_', ' ').title()
            lines.append(f"✓ Goal: {goal}")

        if data.get('target_amount'):
            lines.append(f"✓ Target amount: {data['target_amount']}")

        if data.get('timeline'):
            lines.append(f"✓ Timeline: {data['timeline']}")

        if data.get('current_savings'):
            lines.append(f"✓ Current savings: {data['current_savings']}")

        # Add background discovery section
        lines.extend(self._add_background_section(data))

        lines.append("\nReady to build your financial plan? Reply 'yes' to proceed.")

        return '\n'.join(lines)

    def _networking_confirmation(self, data: Dict) -> str:
        """Generate networking confirmation"""
        lines = ["Excellent! Your networking plan:\n"]

        if data.get('networking_goal'):
            goal = data['networking_goal'].replace('_', ' ').title()
            lines.append(f"✓ Goal: {goal}")

        if data.get('industry'):
            lines.append(f"✓ Industry: {data['industry']}")

        if data.get('timeline'):
            lines.append(f"✓ Timeline: {data['timeline']}")

        if data.get('target_connections'):
            lines.append(f"✓ Target connections: {data['target_connections']}")

        # Add background discovery section
        lines.extend(self._add_background_section(data))

        lines.append("\nReady to build your networking plan? Reply 'yes' to start!")

        return '\n'.join(lines)

    def _generic_confirmation(self, data: Dict) -> str:
        """Fallback confirmation"""
        return """Great! I have enough information to create your personalized plan.

Reply 'yes' to proceed, or let me know if you want to change anything."""

    def _is_confirmation(self, message: str) -> bool:
        """Check if message is a confirmation"""
        message_lower = message.lower().strip()

        confirmations = ['yes', 'yeah', 'yep', 'sure', 'correct', 'right', 'ok', 'okay', 'good', 'perfect', 'да', 'давай', 'го']

        return any(conf in message_lower for conf in confirmations)
