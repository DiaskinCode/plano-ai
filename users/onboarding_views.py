"""
Onboarding API Views

New multi-category onboarding flow with web research and detailed task generation
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import User, GoalSpec, UserProfile, OnboardingProgress, OnboardingChatData
from .goalspec_serializers import GoalSpecSerializer
from .serializers import OnboardingProgressSerializer, OnboardingChatDataSerializer
from ai.path_research_agent import PathResearchAgent
from ai.university_research_agent import UniversityResearchAgent
from ai.feasibility_validator import feasibility_validator


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def research_path(request):
    """
    Phase 1: Research real options from the web

    Request:
    {
        "category": "study",
        "specifications": {
            "degree": "Masters",
            "country": "UK",
            "field": "Computer Science",
            ...
        }
    }

    Response:
    {
        "options": [
            {
                "id": "0",
                "title": "University of Edinburgh",
                "subtitle": "MSc Computer Science - £28,000/year",
                "url": "https://...",
                "details": "Deadline: Dec 15, 2025 • IELTS 7.0",
                "type": "university"
            },
            ...
        ]
    }
    """
    category = request.data.get('category')
    specifications = request.data.get('specifications', {})

    if not category:
        return Response(
            {'error': 'Category is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        # Use PathResearchAgent to search web
        agent = PathResearchAgent()
        options = agent.research_options(category, specifications)

        return Response({
            'options': options,
            'count': len(options),
        })

    except Exception as e:
        print(f"Path research error: {e}")
        return Response(
            {'error': f'Failed to research options: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_tasks(request):
    """
    Phase 3: Generate detailed tasks based on user's selected options

    Request:
    {
        "goalspecs": [
            {
                "category": "study",
                "title": "...",
                "specifications": {...},
                ...
            },
            ...
        ],
        "primary_category": "study",
        "selected_options": [
            {
                "id": "0",
                "title": "University of Edinburgh",
                "url": "https://...",
                ...
            },
            ...
        ]
    }

    Response:
    {
        "tasks_created": 15,
        "goalspecs_created": 3,
        "message": "Successfully created detailed tasks"
    }
    """
    goalspecs_data = request.data.get('goalspecs', [])
    primary_category = request.data.get('primary_category')
    selected_options = request.data.get('selected_options', [])

    if not goalspecs_data or not primary_category:
        return Response(
            {'error': 'goalspecs and primary_category are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        user = request.user
        created_goalspecs = []

        # Step 1: Create GoalSpec objects from draft data
        for gs_data in goalspecs_data:
            # Set priority weights
            if gs_data['category'] == primary_category:
                gs_data['priority_weight'] = 1.0
            else:
                gs_data['priority_weight'] = 0.3

            # Set status to active
            gs_data['status'] = 'active'

            # Set goal_type to category (required field)
            gs_data['goal_type'] = gs_data['category']

            # CRITICAL FIX: Save selected universities to specifications for Study goals
            if gs_data['category'] == 'study' and selected_options:
                # Extract university options from selected_options
                study_options = [opt for opt in selected_options if opt.get('type') == 'university']

                if study_options:
                    # Initialize specifications if not exists
                    if 'specifications' not in gs_data:
                        gs_data['specifications'] = {}

                    # Save university names for template rendering
                    gs_data['specifications']['target_universities'] = [
                        opt['title'] for opt in study_options
                    ]

                    # Save full option data for reference
                    gs_data['specifications']['selected_options'] = study_options

                    print(f"[Onboarding] Saved {len(study_options)} target universities: {gs_data['specifications']['target_universities']}")

            # CRITICAL FIX: Save career options for Career goals
            elif gs_data['category'] == 'career' and selected_options:
                # Extract career options from selected_options
                career_options = [opt for opt in selected_options if opt.get('type') in ['company', 'role', 'industry']]

                if career_options:
                    # Initialize specifications if not exists
                    if 'specifications' not in gs_data:
                        gs_data['specifications'] = {}

                    # Save career target data
                    gs_data['specifications']['target_companies'] = [
                        opt['title'] for opt in career_options if opt.get('type') == 'company'
                    ]
                    gs_data['specifications']['selected_options'] = career_options

                    print(f"[Onboarding] Saved career options: {len(career_options)} items")

            # Create GoalSpec
            serializer = GoalSpecSerializer(data=gs_data)
            if serializer.is_valid():
                goalspec = serializer.save(user=user)  # Pass user directly
                created_goalspecs.append(goalspec)
            else:
                print(f"GoalSpec validation error: {serializer.errors}")

        # Step 2: Generate DETAILED tasks using AtomicTaskAgent (Template System)
        from ai.atomic_task_agent import AtomicTaskAgent
        from todos.models import Todo

        created_tasks = []

        for goalspec in created_goalspecs:
            agent = AtomicTaskAgent(user)
            tasks = agent.generate_atomic_tasks(
                goalspec,
                days_ahead=30,
                use_templates=True   # Enable template-based generation (enhancement is always ON in Week 1)
            )

            print(f"[Onboarding] Generated {len(tasks)} tasks for goal: {goalspec.title}")

            # Step 3: Create Todo objects for this goalspec
            for task_data in tasks:
                # Template system already returns tasks in the correct format
                # Just need to ensure priority is an integer
                priority_val = task_data.get('priority', 2)
                if isinstance(priority_val, str):
                    priority_map = {'critical': 3, 'high': 3, 'medium': 2, 'low': 1}
                    priority_int = priority_map.get(priority_val, 2)
                else:
                    priority_int = priority_val

                # Parse scheduled_date (convert from string to date if needed)
                scheduled_date = task_data.get('scheduled_date')
                if isinstance(scheduled_date, str):
                    from datetime import datetime
                    scheduled_date = datetime.strptime(scheduled_date, '%Y-%m-%d').date()
                elif scheduled_date is None:
                    # Default to today if no scheduled_date provided
                    from datetime import date
                    scheduled_date = date.today()

                # Create atomic task directly from template data
                try:
                    # Prepare notes field with milestone metadata
                    notes_data = task_data.get('notes', {})
                    if isinstance(notes_data, str):
                        notes_data = {'text': notes_data}

                    # Add milestone metadata if present
                    if 'milestone_title' in task_data:
                        notes_data['milestone_title'] = task_data['milestone_title']
                    if 'milestone_index' in task_data:
                        notes_data['milestone_index'] = task_data['milestone_index']

                    todo_task = Todo.objects.create(
                        user=user,
                        goalspec=goalspec,
                        title=task_data['title'],
                        description=task_data.get('description', ''),
                        task_type=task_data.get('task_type', 'copilot'),
                        priority=priority_int,
                        scheduled_date=scheduled_date,
                        timebox_minutes=task_data.get('timebox_minutes', 60),
                        deliverable_type=task_data.get('deliverable_type', 'note'),
                        source=task_data.get('source', 'template_agent'),
                        status='ready',
                        definition_of_done=task_data.get('definition_of_done', []),
                        constraints=task_data.get('constraints', {}),
                        notes=notes_data,
                    )
                    created_tasks.append(todo_task)
                    print(f"[Onboarding] Created task: {task_data['title'][:60]}...")
                except Exception as e:
                    print(f"[Onboarding] Error creating task {task_data.get('title', 'unknown')}: {e}")
                    import traceback
                    traceback.print_exc()

        print(f"[Onboarding] Total tasks created: {len(created_tasks)}")

        # Mark onboarding as completed
        profile, created = UserProfile.objects.get_or_create(user=user)
        profile.onboarding_completed = True
        profile.save()

        return Response({
            'tasks_created': len(created_tasks),
            'goalspecs_created': len(created_goalspecs),
            'message': 'Successfully created detailed tasks',
        })

    except Exception as e:
        print(f"Task generation error: {e}")
        import traceback
        traceback.print_exc()
        return Response(
            {'error': f'Failed to generate tasks: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_active_goalspecs(request):
    """Get user's active goal specifications"""
    goalspecs = GoalSpec.objects.filter(
        user=request.user,
        status='active'
    ).order_by('-priority_weight', 'created_at')

    serializer = GoalSpecSerializer(goalspecs, many=True)
    return Response(serializer.data)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_goalspec(request, pk):
    """Delete a goal specification"""
    goalspec = get_object_or_404(GoalSpec, pk=pk, user=request.user)
    goalspec.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def research_specific_university(request):
    """
    Deep research on specific university (custom search)

    Request:
    {
        "university_name": "Stanford University",
        "program": "MSc Computer Science",
        "intake": "Sep 2026"
    }

    Response:
    {
        "id": "custom_1",
        "title": "Stanford University",
        "subtitle": "MSc CS - $55,000/year",
        "url": "https://cs.stanford.edu/admissions",
        "details": "Deadline: Dec 15, 2025 • IELTS 7.0 • GPA 3.7+",
        "type": "university",
        "deadlines": {...},
        "requirements": {...},
        "financial": {...}
    }
    """
    university_name = request.data.get('university_name')
    program = request.data.get('program', 'MSc Computer Science')
    intake = request.data.get('intake', '2026')

    if not university_name:
        return Response(
            {'error': 'university_name is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        # Use UniversityResearchAgent for deep research
        agent = UniversityResearchAgent()
        university_data = agent.research_university_program(
            university_name=university_name,
            program=program,
            intake=intake
        )

        return Response(university_data)

    except Exception as e:
        print(f"University research error: {e}")
        import traceback
        traceback.print_exc()
        return Response(
            {'error': f'Failed to research university: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def validate_goal_feasibility(request):
    """
    Validate goal feasibility before task generation.
    Provides honest assessment of goal achievability.

    Request:
    {
        "goalspec_id": 123
    }

    Response:
    {
        "feasible": true,
        "confidence": "medium",
        "warnings": ["Your IELTS score (6.5) is below Imperial's typical requirement (7.0)"],
        "recommendations": ["Retake IELTS (target: 7.0+)", "Consider universities with lower requirements"],
        "target_universities": [{"name": "Warwick", "tier": "strong", "acceptance_probability": 0.3}],
        "estimated_success_rate": 0.45
    }
    """
    goalspec_id = request.data.get('goalspec_id')

    if not goalspec_id:
        return Response(
            {'error': 'goalspec_id is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        goalspec = get_object_or_404(GoalSpec, id=goalspec_id, user=request.user)
        profile = request.user.profile

        # Validate based on category
        if goalspec.category == 'study':
            result = feasibility_validator.validate_study_goal(goalspec, profile)
        elif goalspec.category == 'career':
            result = feasibility_validator.validate_career_goal(goalspec, profile)
        elif goalspec.category == 'sport':
            result = feasibility_validator.validate_fitness_goal(goalspec, profile)
        else:
            return Response({'message': 'Feasibility validation not yet implemented for this category'})

        return Response(result)

    except Exception as e:
        print(f"Feasibility validation error: {e}")
        import traceback
        traceback.print_exc()
        return Response(
            {'error': f'Failed to validate goal: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ============================================================================
# CONVERSATIONAL ONBOARDING
# ============================================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def onboarding_chat_init(request):
    """
    Initialize conversational onboarding for a category.
    Returns initial AI greeting.

    Now using Intelligent Agent (Phase 1)

    Request:
    {
        "category": "career"  // career, study, sport, health, finance, networking
    }

    Response:
    {
        "initial_message": "Hey! I'm your AI career coach...",
        "category": "career"
    }
    """
    from ai.intelligent_onboarding_agent import IntelligentOnboardingAgent

    category = request.data.get('category')

    if not category:
        return Response(
            {'error': 'Category is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        agent = IntelligentOnboardingAgent(category)
        initial_message = agent.get_initial_message()

        return Response({
            'initial_message': initial_message,
            'category': category
        })

    except ValueError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        print(f"Chat init error: {e}")
        import traceback
        traceback.print_exc()
        return Response(
            {'error': f'Failed to initialize chat: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def onboarding_chat_send(request):
    """
    Send message in conversational onboarding.

    Now using Intelligent Agent (Phase 1):
    - Intent detection (answering vs asking questions)
    - Bidirectional conversation (user can ask questions)
    - Smart extraction (avoids repeated questions)
    - Context-aware responses

    Request:
    {
        "category": "career",
        "message": "I'm a backend engineer with 3 years experience...",
        "conversation_history": [
            {"role": "assistant", "content": "..."},
            {"role": "user", "content": "..."}
        ],
        "extracted_data": {...}  // Data extracted so far
    }

    Response:
    {
        "ai_message": "Great! A few more questions...",
        "extracted_data": {...},  // Updated data
        "is_complete": false,  // True when ready to generate plan
        "needs_confirmation": false  // True when user needs to confirm
    }
    """
    from ai.intelligent_onboarding_agent import IntelligentOnboardingAgent

    category = request.data.get('category')
    message = request.data.get('message')
    conversation_history = request.data.get('conversation_history', [])
    extracted_data = request.data.get('extracted_data', {})

    if not category or not message:
        return Response(
            {'error': 'Category and message are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        # Use Intelligent Agent (Phase 1)
        agent = IntelligentOnboardingAgent(category)
        result = agent.process_message(message, conversation_history, extracted_data)

        return Response(result)

    except Exception as e:
        print(f"Chat send error: {e}")
        import traceback
        traceback.print_exc()
        return Response(
            {'error': f'Failed to process message: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def onboarding_status(request):
    """
    Check onboarding status and return list of completed categories.

    Returns:
    {
        "needs_onboarding": false,
        "is_complete": true,
        "completed_categories": ["study", "career"]
    }
    """
    try:
        user = request.user
        profile = user.profile

        # Check if onboarding is completed
        if profile.onboarding_completed:
            return Response({
                'needs_onboarding': False,
                'is_complete': True,
                'completed_categories': []
            })

        # Get list of completed categories from OnboardingChatData
        completed_chat_data = OnboardingChatData.objects.filter(user=user)
        completed_categories = [data.category for data in completed_chat_data]

        return Response({
            'needs_onboarding': True,
            'is_complete': False,
            'completed_categories': completed_categories
        })

    except Exception as e:
        print(f"Status check error: {e}")
        import traceback
        traceback.print_exc()
        return Response(
            {'error': f'Failed to check status: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def onboarding_chat_complete(request):
    """
    Save conversational onboarding data for a category.

    This endpoint ONLY saves the data. Task generation happens later
    when user calls /finalize/ endpoint.

    Request:
    {
        "category": "study",
        "extracted_data": {...}
    }

    Response:
    {
        "status": "saved",
        "category": "study",
        "message": "Category data saved successfully"
    }
    """
    category = request.data.get('category')
    extracted_data = request.data.get('extracted_data', {})

    if not category or not extracted_data:
        return Response(
            {'error': 'Category and extracted_data are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        user = request.user

        # Save extracted data to OnboardingChatData
        chat_data, _ = OnboardingChatData.objects.update_or_create(
            user=user,
            category=category,
            defaults={'extracted_data': extracted_data, 'is_merged': False}
        )

        print(f"[OnboardingChat] Saved data for category '{category}'")

        return Response({
            'status': 'saved',
            'category': category,
            'message': f'{category.title()} category data saved successfully'
        })

    except Exception as e:
        print(f"Chat complete error: {e}")
        import traceback
        traceback.print_exc()
        return Response(
            {'error': f'Failed to save category data: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def onboarding_finalize(request):
    """
    Finalize onboarding by generating tasks for ALL completed categories.

    This is called when user clicks "Continue" on the category overview screen
    after filling out one or more categories.

    Request: (empty body)
    {}

    Response:
    {
        "status": "complete",
        "tasks_created": 15,
        "goalspecs_created": 2,
        "message": "Successfully created your personalized plan!"
    }
    """
    print("=" * 80)
    print(f"[OnboardingFinalize] REQUEST RECEIVED at {request.method}")
    print(f"[OnboardingFinalize] User authenticated: {request.user.is_authenticated}")
    print(f"[OnboardingFinalize] User: {request.user}")
    print("=" * 80)

    try:
        user = request.user
        print(f"[OnboardingFinalize] User: {user.id} - {user.email}")

        # Get all OnboardingChatData entries for this user
        all_chat_data = OnboardingChatData.objects.filter(user=user)
        print(f"[OnboardingFinalize] Total OnboardingChatData: {all_chat_data.count()}")

        chat_data_entries = all_chat_data.filter(is_merged=False)
        print(f"[OnboardingFinalize] Unmerged OnboardingChatData: {chat_data_entries.count()}")

        # Check if this is a retry after a failed finalize
        if not chat_data_entries.exists():
            # Check if there's already merged data but no tasks created
            if all_chat_data.exists():
                from todos.models import Todo
                existing_tasks = Todo.objects.filter(user=user).count()
                if existing_tasks == 0:
                    print(f"[OnboardingFinalize] Retry detected: No tasks found, resetting is_merged flags to allow retry")
                    # Reset the is_merged flags to allow retry
                    all_chat_data.update(is_merged=False)
                    chat_data_entries = all_chat_data.filter(is_merged=False)
                else:
                    print(f"[OnboardingFinalize] User already has {existing_tasks} tasks, not retrying")

            if not chat_data_entries.exists():
                print(f"[OnboardingFinalize] ERROR: No onboarding data found!")
                print(f"[OnboardingFinalize] All chat data: {list(all_chat_data.values_list('category', 'is_merged'))}")
                return Response(
                    {'error': 'No onboarding data found. Please complete at least one category first.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        print(f"[OnboardingFinalize] Found {chat_data_entries.count()} categories to process")

        # Merge all category data into UserProfile
        merge_all_chat_data_to_profile(user)

        # Create GoalSpecs from all categories
        goalspecs = create_all_goalspecs_from_chat(user)

        # Generate tasks for all goalspecs
        tasks_count = generate_tasks_for_goalspecs(user, goalspecs)

        # Mark UserProfile onboarding as completed
        profile = user.profile
        profile.onboarding_completed = True
        profile.save()

        print(f"[OnboardingFinalize] Complete! {len(goalspecs)} goalspecs, {tasks_count} tasks")

        return Response({
            'status': 'complete',
            'tasks_created': tasks_count,
            'goalspecs_created': len(goalspecs),
            'message': 'Successfully created your personalized plan!'
        })

    except Exception as e:
        print(f"Finalize error: {e}")
        import traceback
        traceback.print_exc()
        return Response(
            {'error': f'Failed to finalize onboarding: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def create_goalspec_from_chat(user, category, extracted_data):
    """
    Create or update GoalSpec from conversational data.

    Prevents duplicates by checking if a GoalSpec already exists for this user and category.

    Args:
        user: User instance
        category: Category string
        extracted_data: Dict of extracted data

    Returns:
        GoalSpec instance
    """
    # Generate title
    title = _generate_goalspec_title(category, extracted_data)

    # Map to specifications
    specifications = _map_to_specifications(category, extracted_data)

    # Map to constraints
    constraints = _map_to_constraints(category, extracted_data)

    # Map to preferences
    preferences = _map_to_preferences(category, extracted_data)

    # Check if GoalSpec already exists for this user and category
    existing = GoalSpec.objects.filter(user=user, category=category, is_active=True).first()

    if existing:
        # Update existing GoalSpec instead of creating duplicate
        existing.title = title
        existing.specifications = specifications
        existing.constraints = constraints
        existing.preferences = preferences
        existing.save()
        print(f"[OnboardingChat] Updated existing GoalSpec {existing.id} for {category}")
        return existing

    # Create new GoalSpec
    goalspec = GoalSpec.objects.create(
        user=user,
        category=category,
        title=title,
        specifications=specifications,
        constraints=constraints,
        preferences=preferences,
        is_active=True
    )

    print(f"[OnboardingChat] Created new GoalSpec {goalspec.id} for {category}")

    return goalspec


def _parse_gpa(gpa_string):
    """
    Parse GPA string to extract numeric value.

    Examples:
        "3.5/4.0" → 3.5
        "3.7/4" → 3.7
        "85%" → 85
        "3.5" → 3.5
        "3,5" → 3.5
    """
    import re
    from decimal import Decimal, InvalidOperation

    if not gpa_string:
        return None

    gpa_str = str(gpa_string).strip()

    # Remove common suffixes/prefixes
    gpa_str = gpa_str.replace('%', '').strip()

    # If format is "3.5/4.0" or "3.5/4", extract just the first number
    if '/' in gpa_str:
        gpa_str = gpa_str.split('/')[0].strip()

    # Handle European format with comma decimal separator
    gpa_str = gpa_str.replace(',', '.')

    # Extract numeric value
    match = re.search(r'(\d+\.?\d*)', gpa_str)
    if match:
        try:
            return Decimal(match.group(1))
        except InvalidOperation:
            return None

    return None


def _parse_test_scores(test_scores_data):
    """
    Parse test scores from conversational format to dict format.

    Examples:
        "IELTS 7.0" → {"ielts": 7.0}
        "IELTS 7.0, TOEFL 100" → {"ielts": 7.0, "toefl": 100}
        {"ielts": 7.0} → {"ielts": 7.0} (already dict)
        {"IELTS": 7.0} → {"ielts": 7.0} (normalize keys)
    """
    import re

    if not test_scores_data:
        return {}

    # If already a dict, normalize keys to lowercase
    if isinstance(test_scores_data, dict):
        return {k.lower(): v for k, v in test_scores_data.items()}

    # If string, parse it
    if isinstance(test_scores_data, str):
        result = {}
        test_str = test_scores_data.lower()

        # Common test patterns
        patterns = {
            'ielts': r'ielts[:\s]+(\d+\.?\d*)',
            'toefl': r'toefl[:\s]+(\d+)',
            'gre': r'gre[:\s]+(\d+)',
            'gmat': r'gmat[:\s]+(\d+)',
            'sat': r'sat[:\s]+(\d+)',
            'act': r'act[:\s]+(\d+)'
        }

        for test_name, pattern in patterns.items():
            match = re.search(pattern, test_str)
            if match:
                try:
                    score = float(match.group(1))
                    result[test_name] = score
                except ValueError:
                    continue

        return result if result else {}

    return {}


def save_to_user_profile(user, category, extracted_data):
    """
    Save conversational data to UserProfile.

    Args:
        user: User instance
        category: Category string
        extracted_data: Dict of extracted data
    """
    profile = user.profile

    if category == 'career':
        # Save career-specific fields
        if 'current_role' in extracted_data:
            profile.current_role = extracted_data['current_role']
        if 'years_experience' in extracted_data:
            profile.years_experience = extracted_data['years_experience']
        if 'tech_stack' in extracted_data:
            profile.tech_stack = extracted_data['tech_stack']
        if 'design_tools' in extracted_data:
            profile.design_tools = extracted_data['design_tools']
        if 'target_companies' in extracted_data:
            profile.target_companies = extracted_data['target_companies']
        if 'notable_achievements' in extracted_data:
            profile.notable_achievements = extracted_data['notable_achievements']
        if 'target_role' in extracted_data:
            profile.target_role = extracted_data['target_role']
        # NEW: Enhanced career data collection
        if 'work_history' in extracted_data:
            profile.work_history = extracted_data['work_history']
        if 'projects' in extracted_data:
            profile.projects = extracted_data['projects']
        if 'courses_certifications' in extracted_data:
            profile.courses_certifications = extracted_data['courses_certifications']
        if 'education_background' in extracted_data:
            profile.education_background = extracted_data['education_background']

    elif category == 'study':
        # Save study-specific fields
        if 'field_of_study' in extracted_data:
            profile.field_of_study = extracted_data['field_of_study']
        if 'degree_level' in extracted_data:
            profile.degree_level = extracted_data['degree_level']
        if 'target_country' in extracted_data:
            profile.target_country = extracted_data['target_country']
        if 'budget' in extracted_data:
            profile.budget = extracted_data['budget']
        if 'target_schools' in extracted_data:
            profile.target_schools = extracted_data['target_schools']
        if 'current_education' in extracted_data:
            profile.current_education = extracted_data['current_education']
        if 'gpa' in extracted_data:
            # Parse GPA to handle formats like "3.5/4.0" or "85%"
            parsed_gpa = _parse_gpa(extracted_data['gpa'])
            if parsed_gpa is not None:
                profile.gpa = parsed_gpa
            else:
                print(f"[OnboardingChat] WARNING: Could not parse GPA: {extracted_data['gpa']}")
        if 'test_scores' in extracted_data:
            # Parse test scores to handle string format like "IELTS 7.0" → {"ielts": 7.0}
            parsed_test_scores = _parse_test_scores(extracted_data['test_scores'])
            if parsed_test_scores:
                profile.test_scores = parsed_test_scores
                print(f"[OnboardingChat] Parsed test scores: {parsed_test_scores}")
            else:
                print(f"[OnboardingChat] WARNING: Could not parse test scores: {extracted_data['test_scores']}")
        if 'research_interests' in extracted_data:
            profile.research_interests = extracted_data['research_interests']
        if 'coding_experience' in extracted_data:
            profile.coding_experience = extracted_data['coding_experience']
        if 'why_this_field' in extracted_data:
            profile.why_this_field = extracted_data['why_this_field']

    elif category == 'sport':
        # Save sport-specific fields
        if 'fitness_goal_type' in extracted_data:
            profile.fitness_goal_type = extracted_data['fitness_goal_type']
        if 'fitness_level' in extracted_data:
            profile.fitness_level = extracted_data['fitness_level']
        if 'gym_access' in extracted_data:
            profile.gym_access = extracted_data['gym_access']
        if 'equipment' in extracted_data:
            profile.equipment = extracted_data['equipment']
        if 'injuries' in extracted_data:
            profile.injuries = extracted_data['injuries']

    # Save timeline (universal)
    if 'timeline' in extracted_data:
        profile.timeline = extracted_data['timeline']

    # Save background discovery fields (universal - for all categories)
    if 'has_startup_background' in extracted_data:
        profile.has_startup_background = extracted_data['has_startup_background']
    if 'startup_details' in extracted_data:
        profile.startup_details = extracted_data['startup_details']
    if 'has_notable_achievements' in extracted_data:
        profile.has_notable_achievements = extracted_data['has_notable_achievements']
    if 'achievement_details' in extracted_data:
        profile.achievement_details = extracted_data['achievement_details']
    if 'has_research_background' in extracted_data:
        profile.has_research_background = extracted_data['has_research_background']
    if 'research_details' in extracted_data:
        profile.research_details = extracted_data['research_details']
    if 'impressive_projects' in extracted_data:
        profile.impressive_projects = extracted_data['impressive_projects']

    profile.save()

    print(f"[OnboardingChat] Saved {category} data to UserProfile for user {user.id}")


def merge_all_chat_data_to_profile(user):
    """
    Merge all OnboardingChatData from all categories into UserProfile.

    This is called when all categories are complete and we're ready to
    generate tasks. It merges data from all categories into the user's profile.
    """
    chat_data_entries = OnboardingChatData.objects.filter(user=user, is_merged=False)

    for chat_data in chat_data_entries:
        # Use existing save_to_user_profile for each category
        save_to_user_profile(user, chat_data.category, chat_data.extracted_data)

        # Mark as merged
        chat_data.is_merged = True
        chat_data.save()

    print(f"[OnboardingChat] Merged {len(chat_data_entries)} chat data entries into UserProfile")


def create_all_goalspecs_from_chat(user):
    """
    Create GoalSpecs from all OnboardingChatData entries.

    Returns:
        List of created GoalSpec instances
    """
    # Get ALL chat data (not filtered by is_merged) because merge_all_chat_data_to_profile
    # has already marked them as merged by the time this function is called
    chat_data_entries = OnboardingChatData.objects.filter(user=user)
    goalspecs = []

    for chat_data in chat_data_entries:
        goalspec = create_goalspec_from_chat(user, chat_data.category, chat_data.extracted_data)
        goalspecs.append(goalspec)

    # FIX: Deduplicate goalspecs (in case multiple chat_data entries created same goalspec)
    unique_goalspecs = []
    seen_ids = set()
    for gs in goalspecs:
        if gs.id not in seen_ids:
            seen_ids.add(gs.id)
            unique_goalspecs.append(gs)

    if len(goalspecs) != len(unique_goalspecs):
        print(f"[OnboardingChat] Removed {len(goalspecs) - len(unique_goalspecs)} duplicate goalspecs")

    print(f"[OnboardingChat] Created {len(unique_goalspecs)} unique goalspecs from chat data")
    return unique_goalspecs


def generate_tasks_for_goalspecs(user, goalspecs):
    """
    Generate tasks for all goalspecs using AtomicTaskAgent.

    Args:
        user: User instance
        goalspecs: List of GoalSpec instances

    Returns:
        Total number of tasks created
    """
    from ai.atomic_task_agent import AtomicTaskAgent
    from todos.models import Todo
    from datetime import datetime

    total_tasks = 0

    print(f"[TASK_GEN] ========== STARTING TASK GENERATION ==========")
    print(f"[TASK_GEN] User: {user.id} - {user.email}")
    print(f"[TASK_GEN] Number of goalspecs: {len(goalspecs)}")

    for i, goalspec in enumerate(goalspecs):
        print(f"[TASK_GEN] --- Processing GoalSpec {i+1}/{len(goalspecs)} ---")
        print(f"[TASK_GEN] GoalSpec ID: {goalspec.id}")
        print(f"[TASK_GEN] GoalSpec Title: {goalspec.title}")
        print(f"[TASK_GEN] GoalSpec Category: {goalspec.category}")

        # Log profile data relevant to task generation
        profile = user.profile
        print(f"[TASK_GEN] Profile - target_role: {profile.target_role}")
        print(f"[TASK_GEN] Profile - current_role: {profile.current_role}")
        print(f"[TASK_GEN] Profile - tech_stack: {profile.tech_stack}")
        print(f"[TASK_GEN] Profile - target_companies: {profile.target_companies}")

        try:
            agent = AtomicTaskAgent(user)
            tasks = agent.generate_atomic_tasks(
                goalspec,
                days_ahead=30
            )

            print(f"[TASK_GEN] ✅ Generated {len(tasks)} tasks for goal: {goalspec.title}")

            if len(tasks) == 0:
                print(f"[TASK_GEN] ⚠️ WARNING: 0 tasks generated for {goalspec.title}!")
                print(f"[TASK_GEN] This usually means milestone generation failed or LLM returned empty response")

        except Exception as e:
            print(f"[TASK_GEN] ❌ ERROR generating tasks for {goalspec.title}: {str(e)}")
            import traceback
            traceback.print_exc()
            tasks = []

        print(f"[OnboardingChat] Generated {len(tasks)} tasks for goal: {goalspec.title}")

        # Create Todo objects
        for task_data in tasks:
            try:
                # Parse priority
                priority_val = task_data.get('priority', 2)
                if isinstance(priority_val, str):
                    priority_map = {'critical': 3, 'high': 3, 'medium': 2, 'low': 1}
                    priority_int = priority_map.get(priority_val, 2)
                else:
                    priority_int = priority_val

                # Parse scheduled_date
                scheduled_date = task_data.get('scheduled_date')
                if isinstance(scheduled_date, str):
                    scheduled_date = datetime.strptime(scheduled_date, '%Y-%m-%d').date()
                elif scheduled_date is None:
                    # Default to today if no scheduled_date provided
                    from datetime import date
                    scheduled_date = date.today()

                # FIX: Check for duplicate tasks before creating
                task_title = task_data['title'][:200]  # Limit to field max length
                existing_task = Todo.objects.filter(
                    user=user,
                    goalspec=goalspec,
                    title=task_title
                ).first()

                if existing_task:
                    print(f"[OnboardingChat] Skipping duplicate task: {task_title[:60]}...")
                    continue

                # Prepare notes field with milestone metadata
                notes_data = task_data.get('notes', {})
                if isinstance(notes_data, str):
                    notes_data = {'text': notes_data}

                # Add milestone metadata if present
                if 'milestone_title' in task_data:
                    notes_data['milestone_title'] = task_data['milestone_title']
                if 'milestone_index' in task_data:
                    notes_data['milestone_index'] = task_data['milestone_index']

                # Create task
                Todo.objects.create(
                    user=user,
                    goalspec=goalspec,
                    title=task_title,
                    description=task_data.get('description', ''),
                    task_type=task_data.get('task_type', 'copilot'),
                    priority=priority_int,
                    scheduled_date=scheduled_date,
                    timebox_minutes=task_data.get('timebox_minutes', 60),
                    deliverable_type=task_data.get('deliverable_type', 'note'),
                    source=task_data.get('source', 'template_agent'),
                    status='ready',
                    definition_of_done=task_data.get('definition_of_done', []),
                    constraints=task_data.get('constraints', {}),
                    notes=notes_data,
                )
                total_tasks += 1

            except Exception as e:
                print(f"[OnboardingChat] Error creating task {task_data.get('title', 'unknown')}: {e}")
                import traceback
                traceback.print_exc()

    print(f"[OnboardingChat] Total tasks created: {total_tasks}")
    return total_tasks


def _generate_goalspec_title(category, data):
    """Generate title from extracted data"""
    if category == 'career':
        target = data.get('target_role', 'Career Goal')
        return f"Get {target} role"
    elif category == 'study':
        degree = data.get('degree_level', 'Degree').title()
        field = data.get('field_of_study', 'Study')
        return f"{degree} in {field}"
    elif category == 'sport':
        goal = data.get('fitness_goal_type', 'fitness').replace('_', ' ').title()
        return f"{goal} Goal"
    elif category == 'health':
        goal = data.get('health_goal', 'Health Goal')
        return f"{goal}"
    elif category == 'finance':
        goal = data.get('financial_goal', 'financial').replace('_', ' ').title()
        return f"{goal}"
    elif category == 'networking':
        goal = data.get('networking_goal', 'networking').replace('_', ' ').title()
        return f"{goal}"
    else:
        return f"{category.title()} Goal"


def _map_to_specifications(category, data):
    """Map extracted data to GoalSpec specifications"""
    specs = {}

    if category == 'career':
        if 'target_role' in data:
            specs['target_role'] = data['target_role']
        if 'target_companies' in data:
            specs['target_companies'] = data['target_companies']
        if 'tech_stack' in data:
            specs['tech_stack'] = data['tech_stack']
        if 'notable_achievements' in data:
            specs['notable_achievements'] = data['notable_achievements']

    elif category == 'study':
        if 'degree_level' in data:
            specs['degree_level'] = data['degree_level']
        if 'field_of_study' in data:
            specs['field_of_study'] = data['field_of_study']
        if 'target_country' in data:
            specs['target_country'] = data['target_country']
        if 'target_schools' in data:
            specs['target_schools'] = data['target_schools']

    elif category == 'sport':
        if 'fitness_goal_type' in data:
            specs['goal_type'] = data['fitness_goal_type']
        if 'specific_fitness_target' in data:
            specs['target'] = data['specific_fitness_target']

    return specs


def _map_to_constraints(category, data):
    """Map extracted data to GoalSpec constraints"""
    constraints = {}

    if category == 'career':
        if 'location_preference' in data:
            constraints['location'] = data['location_preference']

    elif category == 'study':
        if 'budget' in data:
            constraints['budget'] = data['budget']
        if 'target_country' in data:
            constraints['country'] = data['target_country']

    if 'timeline' in data:
        constraints['timeline'] = data['timeline']

    return constraints


def _map_to_preferences(category, data):
    """Map extracted data to GoalSpec preferences"""
    prefs = {}

    if category == 'career':
        if 'salary_expectation' in data:
            prefs['salary'] = data['salary_expectation']

    elif category == 'study':
        if 'research_interests' in data:
            prefs['research'] = data['research_interests']

    return prefs

