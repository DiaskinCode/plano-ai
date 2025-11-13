from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os

from .services import ai_service
from users.models import UserProfile
from vision.models import Scenario, Vision, Milestone
from todos.models import Todo
from events.models import CheckInEvent, OpportunityEvent
from chat.models import ChatMessage
from users.serializers import UserProfileSerializer
from vision.serializers import ScenarioSerializer, VisionSerializer
from todos.serializers import TodoSerializer
from events.serializers import CheckInEventSerializer, OpportunityEventSerializer
import re


def extract_task_title_from_message(message: str) -> str:
    """
    Extract task title from user message as fallback when AI doesn't provide one.
    Handles common Russian task creation patterns.
    """
    message = message.strip()

    # Common Russian task creation patterns
    patterns = [
        r'запланируй\s+(?:мне\s+)?(.+)',  # "Запланируй (мне) X"
        r'создай\s+(?:задачу\s+)?(?:на\s+)?(.+)',  # "Создай (задачу) X"
        r'сделай\s+(?:таск\s+)?(?:на\s+)?(.+)',  # "Сделай (таск) X"
        r'добавь\s+(?:задачу\s+)?(.+)',  # "Добавь (задачу) X"
        r'напомни\s+(?:мне\s+)?(.+)',  # "Напомни (мне) X"
    ]

    for pattern in patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            title = match.group(1).strip()
            # Remove time/date patterns from the end
            title = re.sub(r'\s+(завтра|послезавтра|сегодня)\s*.*$', '', title, flags=re.IGNORECASE)
            title = re.sub(r'\s+в\s+\d{1,2}[:\.]?\d{0,2}\s*$', '', title)  # Remove "в 14:00"
            title = re.sub(r'\s+на\s+\d{1,2}\s*(час.*)?$', '', title, flags=re.IGNORECASE)  # Remove "на 2 часа"
            return title.strip()

    # Fallback: return first 50 chars of message (truncated)
    return message[:50]


class GenerateScenariosView(APIView):
    """Generate success scenarios based on onboarding data"""
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        profile = UserProfile.objects.get(user=request.user)

        if not profile.onboarding_completed:
            return Response(
                {'error': 'Please complete onboarding first'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get profile data
        profile_data = UserProfileSerializer(profile).data

        # Generate scenarios using AI
        try:
            scenarios_data = ai_service.generate_scenarios(request.user.id, profile_data)

            if not scenarios_data:
                return Response(
                    {'error': 'AI did not generate any scenarios. Please try again.'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            # Save scenarios to database
            scenarios = []
            for idx, scenario_data in enumerate(scenarios_data[:3]):  # Max 3 scenarios
                plan_type = 'main' if idx == 0 else f'plan_{"b" if idx == 1 else "c"}'

                # Validate scenario data
                title = scenario_data.get('title', f'Scenario {idx + 1}')
                description = scenario_data.get('description', 'No description provided')
                pros = scenario_data.get('pros', [])
                cons = scenario_data.get('cons', [])

                # Ensure pros and cons are lists
                if not isinstance(pros, list):
                    pros = []
                if not isinstance(cons, list):
                    cons = []

                scenario = Scenario.objects.create(
                    user=request.user,
                    title=title,
                    description=description,
                    pros=pros,
                    cons=cons,
                    plan_type=plan_type
                )
                scenarios.append(scenario)

            return Response({
                'scenarios': ScenarioSerializer(scenarios, many=True).data
            })

        except Exception as e:
            import traceback
            print(f"Error generating scenarios: {str(e)}")
            print(traceback.format_exc())
            return Response(
                {'error': f'Failed to generate scenarios: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SelectScenarioView(APIView):
    """Select a scenario as main plan"""
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        scenario_id = request.data.get('scenario_id')

        if not scenario_id:
            return Response({'error': 'scenario_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Reset all selections
        Scenario.objects.filter(user=request.user).update(is_selected=False)

        # Set new selection
        Scenario.objects.filter(id=scenario_id, user=request.user).update(is_selected=True)

        return Response({'message': 'Scenario selected successfully'})


class GenerateVisionView(APIView):
    """Generate detailed vision from selected scenario"""
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        scenario_id = request.data.get('scenario_id')

        try:
            scenario = Scenario.objects.get(id=scenario_id, user=request.user)
        except Scenario.DoesNotExist:
            return Response({'error': 'Scenario not found'}, status=status.HTTP_404_NOT_FOUND)

        # Import here to avoid circular import
        from todos.tasks import generate_vision_task

        # Start background task
        task = generate_vision_task.delay(request.user.id, scenario_id)

        return Response({
            'message': 'Vision generation started',
            'task_id': task.id,
            'status': 'pending',
            'status_url': f'/api/ai/task-status/{task.id}/'
        })


class GenerateVisionViewOld(APIView):
    """DEPRECATED: Old synchronous vision generation - kept for reference"""
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        scenario_id = request.data.get('scenario_id')

        try:
            scenario = Scenario.objects.get(id=scenario_id, user=request.user)
        except Scenario.DoesNotExist:
            return Response({'error': 'Scenario not found'}, status=status.HTTP_404_NOT_FOUND)

        scenario_data = ScenarioSerializer(scenario).data

        try:
            # Generate vision using AI
            vision_data = ai_service.generate_vision(request.user.id, scenario_data)

            # Deactivate old visions
            Vision.objects.filter(user=request.user).update(is_active=False)

            # Create vision
            from datetime import datetime, timedelta
            vision = Vision.objects.create(
                user=request.user,
                scenario=scenario,
                title=vision_data.get('title', ''),
                summary=vision_data.get('summary', ''),
                horizon_start=vision_data.get('horizon_start'),
                horizon_end=vision_data.get('horizon_end'),
                monthly_milestones=vision_data.get('monthly_milestones', [])
            )

            # Create milestones from monthly milestones JSON
            monthly_milestones = vision_data.get('monthly_milestones', [])
            milestone_objects = []  # Store created milestone objects

            for idx, monthly in enumerate(monthly_milestones):
                month_str = monthly.get('month')
                if month_str:
                    try:
                        due_date = datetime.strptime(f"{month_str}-15", "%Y-%m-%d").date()
                        # Use title if present, otherwise use goal, otherwise generic name
                        milestone_title = monthly.get('title') or monthly.get('goal', f'Month {idx + 1}')
                        milestone_obj = Milestone.objects.create(
                            vision=vision,
                            title=milestone_title,
                            description=monthly.get('goal', ''),
                            due_date=due_date
                        )
                        milestone_objects.append(milestone_obj)
                    except:
                        pass

            # Generate tasks for ALL milestones across the entire vision
            if monthly_milestones and milestone_objects:
                total_tasks_created = 0
                today = datetime.now().date()

                for milestone_idx, milestone_obj in enumerate(milestone_objects):
                    milestone_data = monthly_milestones[milestone_idx]
                    # AI returns 'tasks' field, not 'key_tasks'
                    tasks = milestone_data.get('tasks', milestone_data.get('key_tasks', []))

                    # Calculate date range for this milestone
                    milestone_end = milestone_obj.due_date

                    # For first milestone: start from today
                    # For later milestones: start from previous milestone's due date
                    if milestone_idx == 0:
                        milestone_start = today
                    else:
                        prev_milestone = milestone_objects[milestone_idx - 1]
                        milestone_start = prev_milestone.due_date + timedelta(days=1)

                    # Calculate available days for this milestone
                    days_available = (milestone_end - milestone_start).days
                    if days_available <= 0:
                        continue  # Skip if milestone is in the past

                    task_count = len(tasks)

                    if task_count > 0:
                        for task_idx, task in enumerate(tasks):
                            # Distribute tasks evenly across the milestone period
                            day_offset = (task_idx * days_available) // task_count
                            task_date = milestone_start + timedelta(days=day_offset)

                            # Determine priority based on position
                            if task_idx < task_count // 3:
                                priority = 3  # First third: High
                            elif task_idx < (2 * task_count) // 3:
                                priority = 2  # Middle third: Medium
                            else:
                                priority = 1  # Last third: Low

                            Todo.objects.create(
                                user=request.user,
                                vision=vision,
                                milestone=milestone_obj,  # Link to this specific milestone
                                title=task,
                                scheduled_date=task_date,
                                priority=priority,
                                estimated_duration_minutes=60,  # Default 1 hour
                                source='ai_generated'
                            )
                            total_tasks_created += 1

                print(f"Created {total_tasks_created} tasks across {len(milestone_objects)} milestones for user {request.user.id}")

            # Note: TaskGenerator is disabled during vision creation
            # since we already created tasks for all milestones above.
            # TaskGenerator can be used later for monthly regeneration.

            return Response({
                'vision': VisionSerializer(vision).data,
                'tasks_generated': total_tasks_created if monthly_milestones and milestone_objects else 0
            })

        except Exception as e:
            return Response(
                {'error': f'Failed to generate vision: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class IntegrateTaskView(APIView):
    """Integrate user task into plan"""
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        task_text = request.data.get('task')

        if not task_text:
            return Response({'error': 'task is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Get AI recommendations
            recommendation = ai_service.integrate_user_task(request.user.id, task_text)

            # Create todo with recommendations
            todo = Todo.objects.create(
                user=request.user,
                title=task_text,
                scheduled_date=recommendation.get('recommended_date'),
                scheduled_time=recommendation.get('recommended_time'),
                priority=recommendation.get('priority', 2),
                estimated_duration_minutes=recommendation.get('estimated_duration_minutes'),
                source='integrated'
            )

            return Response({
                'todo': TodoSerializer(todo).data,
                'reasoning': recommendation.get('reasoning', '')
            })

        except Exception as e:
            return Response(
                {'error': f'Failed to integrate task: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class EveningCheckinView(APIView):
    """Process evening check-in"""
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        try:
            # Process with AI
            ai_response = ai_service.process_checkin(request.user.id, request.data)

            # Mark completed tasks as done based on AI parsing
            completed_task_ids = ai_response.get('completed_task_ids', [])
            tasks_marked_done = 0

            for task_id in completed_task_ids:
                try:
                    todo = Todo.objects.get(id=task_id, user=request.user)
                    if todo.status != 'done':
                        todo.status = 'done'
                        todo.completed_at = request.data.get('date')
                        todo.save()
                        tasks_marked_done += 1
                except Todo.DoesNotExist:
                    print(f"Task {task_id} not found for user {request.user.id}")
                    continue

            # Create check-in event
            checkin = CheckInEvent.objects.create(
                user=request.user,
                date=request.data.get('date'),
                completed_tasks=completed_task_ids,
                completed_tasks_text=request.data.get('completed_tasks_text', ''),
                missed_tasks=request.data.get('missed_tasks', []),
                missed_tasks_text=request.data.get('missed_tasks_text', ''),
                missed_reason=request.data.get('missed_reason', ''),
                new_opportunities=request.data.get('new_opportunities', ''),
                ai_response=ai_response.get('supportive_message', ''),
                ai_recommendations=ai_response.get('recommendations', {})
            )

            return Response({
                'checkin': CheckInEventSerializer(checkin).data,
                'ai_response': ai_response,
                'tasks_marked_done': tasks_marked_done
            })

        except Exception as e:
            import traceback
            print(f"Check-in error: {str(e)}")
            print(traceback.format_exc())
            return Response(
                {'error': f'Failed to process check-in: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AnalyzeOpportunityView(APIView):
    """Analyze new opportunity"""
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        title = request.data.get('title')
        description = request.data.get('description')

        if not title or not description:
            return Response(
                {'error': 'title and description are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Analyze with AI
            analysis = ai_service.analyze_opportunity(
                request.user.id,
                f"{title}: {description}"
            )

            # Create opportunity event
            opportunity = OpportunityEvent.objects.create(
                user=request.user,
                title=title,
                description=description,
                date_occurred=request.data.get('date_occurred'),
                ai_impact_assessment=analysis.get('impact_assessment', 'medium'),
                ai_recommendation=analysis.get('recommendation_text', ''),
                requires_vision_change=analysis.get('requires_vision_change', False)
            )

            return Response({
                'opportunity': OpportunityEventSerializer(opportunity).data,
                'analysis': analysis
            })

        except Exception as e:
            return Response(
                {'error': f'Failed to analyze opportunity: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ChatView(APIView):
    """Chat with AI coach"""
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        message = request.data.get('message')
        conversation_id = request.data.get('conversation_id')

        if not message:
            return Response({'error': 'message is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            from chat.models import ChatConversation

            # DEBUG logging
            print(f"[DEBUG CHAT] Received conversation_id: {conversation_id} (type: {type(conversation_id)})")
            print(f"[DEBUG CHAT] Request data: {request.data}")

            # Get or create conversation
            if conversation_id:
                conversation = ChatConversation.objects.get(id=conversation_id, user=request.user)
            else:
                # Create new conversation
                conversation = ChatConversation.objects.create(
                    user=request.user,
                    title='New Chat'
                )

            # Save user message
            user_msg = ChatMessage.objects.create(
                conversation=conversation,
                user=request.user,
                role='user',
                content=message
            )

            # Fetch conversation history (last 20 messages for context)
            previous_messages = conversation.messages.order_by('created_at')[:20]
            conversation_history = []
            for msg in previous_messages:
                # Don't include the message we just created
                if msg.id != user_msg.id:
                    conversation_history.append({
                        "role": msg.role,
                        "content": msg.content
                    })

            # Get AI response with conversation history
            ai_response_data = ai_service.chat_response(
                request.user.id,
                message,
                conversation_history=conversation_history
            )

            # DEBUG: Log AI response to see what's actually being returned
            print(f"[DEBUG] AI Response Data: {ai_response_data}")

            ai_text = ai_response_data.get('response', '')
            tasks_to_create = ai_response_data.get('create_tasks', [])
            tasks_to_update = ai_response_data.get('update_tasks', [])
            completed_task_ids = ai_response_data.get('completed_task_ids', [])

            # DEBUG: Log task arrays
            print(f"[DEBUG] Tasks to create: {tasks_to_create}")
            print(f"[DEBUG] Tasks to update: {tasks_to_update}")
            print(f"[DEBUG] Tasks to complete: {completed_task_ids}")

            # Update tasks (reschedule)
            tasks_updated = 0
            from datetime import datetime
            for update_data in tasks_to_update:
                try:
                    task_id = update_data.get('task_id')
                    todo = Todo.objects.get(id=task_id, user=request.user)

                    if 'scheduled_date' in update_data:
                        todo.scheduled_date = update_data['scheduled_date']
                    if 'scheduled_time' in update_data:
                        try:
                            from datetime import time
                            time_str = update_data['scheduled_time']
                            hour, minute = map(int, time_str.split(':'))
                            todo.scheduled_time = time(hour=hour, minute=minute)
                        except:
                            pass

                    todo.save()
                    tasks_updated += 1
                except Todo.DoesNotExist:
                    print(f"Task {task_id} not found for user {request.user.id}")
                    continue

            # Mark completed tasks as done
            tasks_marked_done = 0
            for task_id in completed_task_ids:
                try:
                    todo = Todo.objects.get(id=task_id, user=request.user)
                    if todo.status != 'done':
                        todo.status = 'done'
                        todo.completed_at = datetime.now()
                        todo.save()
                        tasks_marked_done += 1
                except Todo.DoesNotExist:
                    print(f"Task {task_id} not found for user {request.user.id}")
                    continue

            # Save AI message
            ai_msg = ChatMessage.objects.create(
                conversation=conversation,
                user=request.user,
                role='assistant',
                content=ai_text
            )

            # Auto-generate title from first message
            if not conversation.auto_titled and conversation.messages.count() >= 2:
                # Use first user message as title (truncated)
                conversation.title = message[:50]
                conversation.auto_titled = True
                conversation.save()

            # Create tasks if AI suggested any
            created_tasks = []
            if tasks_to_create:
                from datetime import datetime, timedelta
                from django.utils import timezone
                import pytz

                # Get user's timezone for accurate "today" calculation
                user_tz_str = request.user.timezone if request.user.timezone else 'UTC'
                try:
                    user_tz = pytz.timezone(user_tz_str)
                    current_time_local = timezone.now().astimezone(user_tz)
                except:
                    current_time_local = timezone.now()

                today = current_time_local.date()

                for task_data in tasks_to_create:
                    # DEBUG: Log individual task data
                    print(f"[DEBUG] Creating task from data: {task_data}")
                    print(f"[DEBUG] Task title: '{task_data.get('title', 'MISSING!')}'")

                    # Get title with smart fallback
                    title = task_data.get('title', '').strip()
                    if not title:
                        # AI didn't provide a title, try to extract from user message
                        title = extract_task_title_from_message(message)
                        print(f"[WARNING] AI didn't provide task title. Extracted from message: '{title}'")

                    # Parse scheduled time if provided
                    scheduled_time = None
                    if 'scheduled_time' in task_data:
                        try:
                            from datetime import time
                            time_str = task_data['scheduled_time']
                            hour, minute = map(int, time_str.split(':'))
                            scheduled_time = time(hour=hour, minute=minute)
                        except:
                            pass

                    todo = Todo.objects.create(
                        user=request.user,
                        title=title,
                        priority=task_data.get('priority', 2),
                        estimated_duration_minutes=task_data.get('duration_minutes', 60),
                        scheduled_date=today,
                        scheduled_time=scheduled_time,
                        source='integrated'
                    )
                    created_tasks.append(TodoSerializer(todo).data)

            return Response({
                'response': ai_text,
                'message_id': ai_msg.id,
                'conversation_id': conversation.id,
                'conversation_title': conversation.title,
                'tasks_created': len(created_tasks),
                'tasks': created_tasks,
                'tasks_updated': tasks_updated,
                'tasks_marked_done': tasks_marked_done
            })

        except Exception as e:
            import traceback
            print(f"Chat error: {str(e)}")
            print(traceback.format_exc())
            return Response(
                {'error': f'Chat failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TranscribeAudioView(APIView):
    """Transcribe audio to text"""
    permission_classes = (permissions.IsAuthenticated,)
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        if 'audio' not in request.FILES:
            return Response({'error': 'audio file is required'}, status=status.HTTP_400_BAD_REQUEST)

        audio_file = request.FILES['audio']

        try:
            # Save temporarily
            file_name = f'temp_audio_{request.user.id}.m4a'
            path = default_storage.save(file_name, ContentFile(audio_file.read()))
            full_path = default_storage.path(path)

            # Transcribe
            transcription = ai_service.transcribe_audio(full_path)

            # Clean up
            default_storage.delete(path)

            return Response({'transcription': transcription})

        except Exception as e:
            return Response(
                {'error': f'Transcription failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TaskAIAssistantView(APIView):
    """
    AI assistant for task-specific questions
    Provides detailed links, contacts, and instructions
    """
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        task_id = request.data.get('task_id')
        question = request.data.get('question')
        conversation_id = request.data.get('conversation_id')  # Optional: for continuing existing conversation
        mode = request.data.get('mode', 'clarify')  # clarify, expand, or research

        print(f"\n{'*'*80}")
        print(f"[TASK AI VIEW] Request received")
        print(f"[TASK AI VIEW] User: {request.user.username}")
        print(f"[TASK AI VIEW] Task ID: {task_id}")
        print(f"[TASK AI VIEW] Question: {question}")
        print(f"[TASK AI VIEW] Mode: {mode}")
        print(f"[TASK AI VIEW] Conversation ID: {conversation_id}")
        print(f"{'*'*80}\n")

        if not task_id:
            return Response({'error': 'task_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        if not question:
            return Response({'error': 'question is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            from chat.models import ChatConversation, ChatMessage

            # Get task details
            task = Todo.objects.get(id=task_id, user=request.user)
            print(f"[TASK AI VIEW] Task found: {task.title}")

            # Get or create task-specific conversation
            if conversation_id:
                try:
                    conversation = ChatConversation.objects.get(
                        id=conversation_id,
                        user=request.user,
                        task=task
                    )
                    print(f"[TASK AI VIEW] Using existing conversation {conversation_id}")
                except ChatConversation.DoesNotExist:
                    print(f"[TASK AI VIEW] Conversation {conversation_id} not found, creating new one")
                    conversation = ChatConversation.objects.create(
                        user=request.user,
                        task=task,
                        title=f"AI Assistant: {task.title[:50]}"
                    )
            else:
                # Create new task-specific conversation
                conversation = ChatConversation.objects.create(
                    user=request.user,
                    task=task,
                    title=f"AI Assistant: {task.title[:50]}"
                )
                print(f"[TASK AI VIEW] Created new conversation {conversation.id}")

            # Save user message
            user_msg = ChatMessage.objects.create(
                conversation=conversation,
                user=request.user,
                role='user',
                content=question
            )

            # Fetch conversation history from database (last 20 messages)
            previous_messages = conversation.messages.order_by('created_at')[:20]
            conversation_history = []
            for msg in previous_messages:
                # Don't include the message we just created
                if msg.id != user_msg.id:
                    conversation_history.append({
                        "role": msg.role,
                        "content": msg.content
                    })

            print(f"[TASK AI VIEW] Loaded {len(conversation_history)} messages from history")

            # Get AI response with task-specific assistance
            ai_response = ai_service.task_specific_assistance(
                user_id=request.user.id,
                task=task,
                question=question,
                conversation_history=conversation_history,
                mode=mode
            )

            # Save AI message
            ai_msg = ChatMessage.objects.create(
                conversation=conversation,
                user=request.user,
                role='assistant',
                content=ai_response.get('response'),
                context_used={
                    'links': ai_response.get('links', []),
                    'contacts': ai_response.get('contacts', []),
                    'steps': ai_response.get('steps', []),
                    'mode': mode
                }
            )

            print(f"[TASK AI VIEW] AI response saved, sending to client")
            return Response({
                'response': ai_response.get('response'),
                'links': ai_response.get('links', []),
                'contacts': ai_response.get('contacts', []),
                'steps': ai_response.get('steps', []),
                'can_expand': ai_response.get('can_expand', False),
                'conversation_id': conversation.id,  # Return conversation ID for future requests
                'message_id': ai_msg.id,
            })

        except Todo.DoesNotExist:
            return Response(
                {'error': 'Task not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            import traceback
            print(f"Task AI assistant error: {str(e)}")
            print(traceback.format_exc())
            return Response(
                {'error': f'AI assistant failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TaskConversationHistoryView(APIView):
    """Get conversation history for a specific task"""
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, task_id):
        """Get the conversation for a specific task"""
        try:
            from chat.models import ChatConversation, ChatMessage
            from chat.serializers import ChatMessageListSerializer

            task = Todo.objects.get(id=task_id, user=request.user)

            # Get task-specific conversation (most recent one if multiple exist)
            conversation = ChatConversation.objects.filter(
                user=request.user,
                task=task
            ).first()

            if not conversation:
                return Response({
                    'conversation_id': None,
                    'messages': [],
                    'message': 'No conversation found for this task'
                })

            # Get all messages in conversation
            messages = conversation.messages.all()
            serializer = ChatMessageListSerializer(messages, many=True)

            # Extract links, contacts, steps from context_used for frontend compatibility
            formatted_messages = []
            for msg_data in serializer.data:
                msg = {
                    'role': msg_data['role'],
                    'content': msg_data['content'],
                    'created_at': msg_data['created_at']
                }

                # Get context from the ChatMessage to extract links, contacts, steps
                msg_obj = messages.get(id=msg_data['id'])
                context = msg_obj.context_used if hasattr(msg_obj, 'context_used') else {}

                if msg_data['role'] == 'assistant' and context:
                    msg['links'] = context.get('links', [])
                    msg['contacts'] = context.get('contacts', [])
                    msg['steps'] = context.get('steps', [])
                    msg['mode'] = context.get('mode', 'clarify')

                formatted_messages.append(msg)

            return Response({
                'conversation_id': conversation.id,
                'messages': formatted_messages,
                'message_count': len(formatted_messages)
            })

        except Todo.DoesNotExist:
            return Response(
                {'error': 'Task not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            import traceback
            print(f"Error fetching task conversation: {str(e)}")
            print(traceback.format_exc())
            return Response(
                {'error': f'Failed to fetch conversation: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CreateSubtasksFromAIView(APIView):
    """Create subtasks from AI response steps"""
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        parent_task_id = request.data.get('parent_task_id')
        steps = request.data.get('steps', [])

        if not parent_task_id:
            return Response({'error': 'parent_task_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        if not steps:
            return Response({'error': 'steps are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            from datetime import datetime, timedelta

            parent_task = Todo.objects.get(id=parent_task_id, user=request.user)

            created_subtasks = []
            today = datetime.now().date()

            # Use parent task's scheduled date or today as base
            base_date = parent_task.scheduled_date if parent_task.scheduled_date else today

            for idx, step in enumerate(steps):
                # Create subtask with scheduled_date (required field)
                subtask = Todo.objects.create(
                    user=request.user,
                    title=step if isinstance(step, str) else step.get('text', f'Step {idx + 1}'),
                    description=f'Subtask generated from AI suggestion for: {parent_task.title}',
                    task_type='manual',
                    timebox_minutes=30,  # Default 30 min
                    deliverable_type='other',
                    priority=parent_task.priority,
                    status='ready',  # Changed from 'pending' to 'ready'
                    scheduled_date=base_date,  # REQUIRED FIELD
                    goalspec=parent_task.goalspec,
                    parent_task_id=parent_task_id,
                )
                created_subtasks.append(subtask)

            from todos.serializers import TodoSerializer
            return Response({
                'message': f'Created {len(created_subtasks)} subtasks',
                'subtasks': TodoSerializer(created_subtasks, many=True).data
            })

        except Todo.DoesNotExist:
            return Response(
                {'error': 'Parent task not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            import traceback
            print(f"Create subtasks error: {str(e)}")
            print(traceback.format_exc())
            return Response(
                {'error': f'Failed to create subtasks: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GenerateTaskDescriptionView(APIView):
    """Generate AI description for a task"""
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        task_id = request.data.get('task_id')

        if not task_id:
            return Response({'error': 'task_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            task = Todo.objects.get(id=task_id, user=request.user)

            # Generate description if it doesn't exist or is empty
            if not task.description:
                description = ai_service.generate_task_description(request.user.id, task)
                task.description = description
                task.save()

            return Response({
                'description': task.description,
                'task': TodoSerializer(task).data
            })

        except Todo.DoesNotExist:
            return Response(
                {'error': 'Task not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            import traceback
            print(f"Generate task description error: {str(e)}")
            print(traceback.format_exc())
            return Response(
                {'error': f'Failed to generate description: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GenerateAtomicTasksView(APIView):
    """
    Generate atomic tasks using template-based system.

    NEW: Uses AtomicTaskAgent with template system for zero hallucinations
    and 7-8/10 personalization on Day 1.
    """
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        goalspec_id = request.data.get('goalspec_id')
        days_ahead = request.data.get('days_ahead', 30)
        use_templates = request.data.get('use_templates', True)  # Default: enabled
        enhance = request.data.get('enhance', False)  # Default: disabled (opt-in)

        if not goalspec_id:
            return Response({'error': 'goalspec_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            from users.goalspec_models import GoalSpec
            from .atomic_task_agent import AtomicTaskAgent

            # Get goalspec
            goalspec = GoalSpec.objects.get(id=goalspec_id, user=request.user)

            # IDEMPOTENCY CHECK: Check if tasks already exist for this goalspec
            existing_tasks = Todo.objects.filter(
                user=request.user,
                goalspec=goalspec,
                source='template_agent'
            )

            if existing_tasks.exists():
                existing_count = existing_tasks.count()
                print(f"[GenerateAtomicTasksView] Found {existing_count} existing tasks for goal: {goalspec.title}")

                # Return existing tasks instead of generating duplicates
                return Response({
                    'tasks': TodoSerializer(existing_tasks, many=True).data,
                    'count': existing_count,
                    'message': f'Found {existing_count} existing tasks for this goal',
                    'already_generated': True,
                    'using_templates': use_templates,
                    'enhanced': enhance
                })

            # Initialize agent
            agent = AtomicTaskAgent(request.user)

            print(f"[GenerateAtomicTasksView] Generating tasks for goal: {goalspec.title}")
            print(f"[GenerateAtomicTasksView] use_templates={use_templates}, enhance={enhance}")

            # Generate tasks
            tasks = agent.generate_atomic_tasks(
                goalspec,
                days_ahead=days_ahead,
                use_templates=use_templates,
                enhance=enhance
            )

            if not tasks or len(tasks) == 0:
                print(f"[GenerateAtomicTasksView] No tasks generated - template matching failed")
                return Response({
                    'error': 'No tasks could be generated for this goal. Please check the goal specifications.',
                    'count': 0
                }, status=status.HTTP_400_BAD_REQUEST)

            # Save tasks to database
            created_tasks = []
            for task_data in tasks:
                # Parse scheduled_date (convert from string to date if needed)
                scheduled_date = task_data.get('scheduled_date')
                if isinstance(scheduled_date, str):
                    from datetime import datetime
                    scheduled_date = datetime.strptime(scheduled_date, '%Y-%m-%d').date()

                # Create Todo from task_data
                todo = Todo.objects.create(
                    user=request.user,
                    goalspec=goalspec,
                    title=task_data['title'],
                    description=task_data.get('description', ''),
                    task_type=task_data.get('task_type', 'copilot'),
                    timebox_minutes=task_data.get('timebox_minutes', 60),
                    priority=task_data.get('priority', 2),
                    deliverable_type=task_data.get('deliverable_type', 'note'),
                    scheduled_date=scheduled_date,
                    status='ready',
                    source=task_data.get('source', 'template_agent'),
                    definition_of_done=task_data.get('definition_of_done', []),
                    constraints=task_data.get('constraints', {}),
                    notes=task_data.get('notes', '')
                )
                created_tasks.append(todo)

            print(f"[GenerateAtomicTasksView] Created {len(created_tasks)} tasks")

            return Response({
                'tasks': TodoSerializer(created_tasks, many=True).data,
                'count': len(created_tasks),
                'using_templates': use_templates,
                'enhanced': enhance,
                'message': f'Generated {len(created_tasks)} atomic tasks'
            })

        except GoalSpec.DoesNotExist:
            return Response(
                {'error': 'GoalSpec not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            import traceback
            print(f"Generate atomic tasks error: {str(e)}")
            print(traceback.format_exc())
            return Response(
                {'error': f'Failed to generate tasks: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
