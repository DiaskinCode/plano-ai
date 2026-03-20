from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from datetime import timedelta
from celery.result import AsyncResult
import logging

logger = logging.getLogger(__name__)

from .models import Todo, TaskCategory
from .serializers import TodoSerializer, TodoCreateSerializer, TodoListSerializer
from .task_generator import TaskGenerator
from .simple_task_generator import generate_simple_tasks

# NEW: Eligibility-first imports
from university_recommender.eligibility_checker_v2 import EligibilityCheckerV2
from university_recommender.models import UniversityShortlist
from university_database.models import University, CountryRequirement
from university_profile.models import UniversitySeekerProfile
from .eligibility_first_generator import EligibilityFirstGenerator


class TaskCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only viewset for task categories"""
    permission_classes = (permissions.IsAuthenticated,)
    queryset = TaskCategory.objects.all()

    def list(self, request, *args, **kwargs):
        """List all task categories"""
        categories = self.queryset.order_by('order')
        data = [{
            'id': cat.id,
            'name': cat.name,
            'icon': cat.icon,
            'color': cat.color,
            'description': cat.description,
            'is_application_specific': cat.is_application_specific,
            'order': cat.order,
        } for cat in categories]
        return Response(data)


class TodoViewSet(viewsets.ModelViewSet):
    """CRUD operations for todos"""
    permission_classes = (permissions.IsAuthenticated,)

    def get_serializer_class(self):
        if self.action == 'create':
            return TodoCreateSerializer
        elif self.action == 'list':
            return TodoListSerializer
        return TodoSerializer

    def get_queryset(self):
        queryset = Todo.objects.filter(user=self.request.user).select_related('category')

        # Filter by date
        filter_type = self.request.query_params.get('filter', None)
        today = timezone.now().date()

        if filter_type == 'today':
            queryset = queryset.filter(scheduled_date=today)
        elif filter_type == 'tomorrow':
            tomorrow = today + timedelta(days=1)
            queryset = queryset.filter(scheduled_date=tomorrow)
        elif filter_type == 'overdue':
            queryset = queryset.filter(scheduled_date__lt=today, status='pending')
        elif filter_type == 'upcoming':
            queryset = queryset.filter(scheduled_date__gte=today, status='pending')

        # Filter by status
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # NEW: Filter by category
        category_id = self.request.query_params.get('category', None)
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        return queryset.order_by('scheduled_date', '-priority', 'created_at')

    @action(detail=True, methods=['post'])
    def mark_done(self, request, pk=None):
        """Mark todo as done (simple)"""
        todo = self.get_object()
        todo.status = 'done'
        todo.completed_at = timezone.now()
        todo.save()
        return Response(TodoSerializer(todo).data)

    @action(detail=True, methods=['post', 'put'])
    def complete(self, request, pk=None):
        """
        Enhanced task completion with result logging
        Captures: difficulty, completion status, results, quality, time taken, notes
        """
        from .advanced_models import TaskCompletion

        todo = self.get_object()

        # Mark todo as done
        todo.status = 'done'
        todo.completed_at = timezone.now()
        todo.save()

        # Get or create completion record
        completion, created = TaskCompletion.objects.get_or_create(
            task=todo,
            user=request.user,
            defaults={
                'completed_at': timezone.now(),
            }
        )

        # Update completion with enhanced data
        completion.actual_duration_minutes = request.data.get('actual_duration_minutes')
        completion.difficulty_rating = request.data.get('difficulty_rating')
        completion.completion_reason = request.data.get('completion_reason', 'completed')
        completion.completion_status = request.data.get('completion_status', 'fully_completed')
        completion.result_type = request.data.get('result_type', 'general')
        completion.result_data = request.data.get('result_data', {})
        completion.quality_rating = request.data.get('quality_rating')
        completion.files_attached = request.data.get('files_attached', [])
        completion.time_of_day = request.data.get('time_of_day')
        completion.energy_level_at_completion = request.data.get('energy_level_at_completion')
        completion.notes = request.data.get('notes', '')
        completion.would_reschedule_to = request.data.get('would_reschedule_to')
        completion.save()

        # Unlock dependent tasks
        todo.unlock_dependents()

        return Response({
            'message': 'Task completed successfully',
            'todo': TodoSerializer(todo).data,
            'completion': {
                'id': completion.id,
                'completed_at': completion.completed_at,
                'actual_duration_minutes': completion.actual_duration_minutes,
                'difficulty_rating': completion.difficulty_rating,
                'completion_status': completion.completion_status,
                'result_type': completion.result_type,
                'result_data': completion.result_data,
                'quality_rating': completion.quality_rating,
            }
        })

    @action(detail=True, methods=['post'])
    def skip(self, request, pk=None):
        """Skip todo with reason"""
        todo = self.get_object()
        todo.status = 'skipped'
        todo.skipped_at = timezone.now()
        todo.skip_reason = request.data.get('reason', '')
        todo.save()
        return Response(TodoSerializer(todo).data)

    @action(detail=True, methods=['post'])
    def reschedule(self, request, pk=None):
        """Reschedule todo"""
        todo = self.get_object()
        todo.scheduled_date = request.data.get('new_date', todo.scheduled_date)
        todo.scheduled_time = request.data.get('new_time', todo.scheduled_time)
        todo.status = 'rescheduled'
        todo.save()
        return Response(TodoSerializer(todo).data)


class TaskStatusView(APIView):
    """Check status of background task generation"""
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, task_id):
        task_result = AsyncResult(task_id)

        response_data = {
            'task_id': task_id,
            'state': task_result.state,
        }

        if task_result.state == 'PENDING':
            response_data['status'] = 'pending'
            response_data['message'] = 'Task is waiting to start'
        elif task_result.state == 'PROGRESS':
            response_data['status'] = 'in_progress'
            response_data['progress'] = task_result.info
        elif task_result.state == 'SUCCESS':
            response_data['status'] = 'completed'
            response_data['result'] = task_result.result
        elif task_result.state == 'FAILURE':
            response_data['status'] = 'failed'
            response_data['error'] = str(task_result.info)
        else:
            response_data['status'] = task_result.state.lower()

        return Response(response_data)


# ============================================================================
# NEW: Eligibility-First Task Generation Endpoints
# ============================================================================

class CheckEligibilityView(APIView):
    """
    Check eligibility for user's shortlisted universities.

    Returns eligibility status for each university including:
    - Overall status (eligible, partially_eligible, not_eligible)
    - Blockers that prevent application
    - Gaps that need to be resolved
    - Available alternative paths (foundation, etc.)
    """
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        # Get user's profile
        try:
            profile = UniversitySeekerProfile.objects.get(user=request.user)
        except UniversitySeekerProfile.DoesNotExist:
            return Response({
                'error': 'Please complete your university profile first',
                'status': 'profile_required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get shortlisted universities
        shortlist_items = UniversityShortlist.objects.filter(user=request.user)
        if not shortlist_items.exists():
            return Response({
                'error': 'No universities in shortlist. Please add universities to your shortlist first.',
                'status': 'no_shortlist'
            }, status=status.HTTP_400_BAD_REQUEST)

        universities = [item.university for item in shortlist_items]

        # Build country requirement cache
        country_req_cache = {
            req.country: req
            for req in CountryRequirement.objects.all()
        }

        # Check eligibility
        checker = EligibilityCheckerV2(country_req_cache=country_req_cache)
        results = checker.check_eligibility_for_shortlist(profile, universities, track='direct')

        # Format response
        response_data = {
            'profile_status': 'complete',
            'overall_eligibility': profile.overall_eligibility_status or 'not_checked',
            'current_strategy': profile.education_path_strategy or '',
            'universities': [],
            'has_blockers': False,
            'has_missing_data': False,
        }

        all_blockers = []
        has_missing_data = False

        for uni_name, result in results.items():
            uni_data = {
                'short_name': uni_name,
                'name': universities[next(i for i, u in enumerate(universities) if u.short_name == uni_name)].name,
                'status': result.status,
                'can_apply_direct': result.can_apply_direct,
                'can_apply_foundation': result.can_apply_foundation,
                'foundation_available': result.foundation_available,
                'blockers': [],
                'gaps_count': len(result.gaps),
            }

            for blocker in result.blockers:
                blocker_data = {
                    'type': blocker.gap_type,
                    'title': blocker.title,
                    'description': blocker.description,
                    'current_value': blocker.current_value,
                    'required_value': blocker.required_value,
                    'is_blocker': blocker.is_blocker,
                    'alternative_path': blocker.alternative_path,
                    'resolution_tasks': blocker.resolution_tasks,
                }
                uni_data['blockers'].append(blocker_data)
                all_blockers.append(blocker)

                if blocker.gap_type == 'missing_data':
                    has_missing_data = True

            response_data['universities'].append(uni_data)

        response_data['has_blockers'] = len(all_blockers) > 0
        response_data['has_missing_data'] = has_missing_data

        # Determine if user needs to choose strategy
        structural_blockers = [
            b for b in all_blockers
            if b.gap_type == 'education_years' and not profile.education_path_strategy
        ]
        response_data['needs_strategy_choice'] = len(structural_blockers) > 0

        # ✅ Calculate coverage from RequirementInstance (not Todo!)
        from requirements.models import RequirementInstance

        instances = RequirementInstance.objects.filter(user=request.user)
        total = instances.count()

        if total == 0:
            coverage = {
                'verified_percent': 0,
                'assumed_percent': 0,
                'plan_status': 'not_generated',  # ✅ Explicit status
                'missing_count': 0
            }
        else:
            verified = instances.filter(
                verification_level__in=['official', 'vendor']
            ).count()

            assumed = instances.filter(
                verification_level='assumed'
            ).count()

            verified_percent = int((verified / total) * 100)
            assumed_percent = int(((verified + assumed) / total) * 100)
            plan_status = 'verified' if verified_percent >= 95 else 'draft'
            missing = instances.filter(status='unknown').count()

            coverage = {
                'verified_percent': verified_percent,
                'assumed_percent': assumed_percent,
                'plan_status': plan_status,
                'missing_count': missing
            }

        response_data['coverage'] = coverage  # ✅ From RequirementInstance

        return Response(response_data)


class SetStrategyAndGenerateTasksView(APIView):
    """
    Set user's education path strategy and generate tasks.

    This endpoint:
    1. Updates the user's education_path_strategy
    2. Runs eligibility check with the selected strategy
    3. Generates appropriate tasks (gap-closure OR application tasks)
    4. Validates that all tasks have dedupe_key (safety net)
    5. Returns summary of generated tasks

    Strategy options:
    - 'direct': Apply directly to universities
    - 'foundation': Apply via foundation programs
    - 'change_shortlist': User will modify their shortlist
    """
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        strategy = request.data.get('strategy')

        if not strategy:
            return Response({
                'error': 'Strategy is required',
                'valid_strategies': ['direct', 'foundation', 'change_shortlist']
            }, status=status.HTTP_400_BAD_REQUEST)

        if strategy not in ['direct', 'foundation', 'change_shortlist']:
            return Response({
                'error': f'Invalid strategy: {strategy}',
                'valid_strategies': ['direct', 'foundation', 'change_shortlist']
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get user's profile
        try:
            profile = UniversitySeekerProfile.objects.get(user=request.user)
        except UniversitySeekerProfile.DoesNotExist:
            return Response({
                'error': 'Please complete your university profile first'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get shortlisted universities
        shortlist_items = UniversityShortlist.objects.filter(user=request.user)
        if not shortlist_items.exists():
            return Response({
                'error': 'No universities in shortlist'
            }, status=status.HTTP_400_BAD_REQUEST)

        universities = [item.university for item in shortlist_items]

        # Generate tasks
        try:
            generator = EligibilityFirstGenerator(request.user)
            result = generator.generate_for_shortlist(universities, strategy=strategy)

            # Check for errors
            if result.get('status') == 'error':
                return Response(result, status=status.HTTP_400_BAD_REQUEST)

            return Response(result)

        except ValueError as e:
            # This catches the dedupe_key validation error
            return Response({
                'error': 'Task generation failed - missing dedupe_key',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            return Response({
                'error': 'Failed to generate tasks',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PlanGenerationView(APIView):
    """
    Generate admission plan from shortlist using Requirement Engine.

    POST /api/todos/plan/generate/

    Request:
    {
        "track": "direct",  # "direct" | "foundation"
        "intake": "fall_2026",
        "degree_level": "bachelor",
        "citizenship": "Kazakhstan"
    }

    Response:
    {
        "status": "success",
        "requirements_stats": {"created": 15, "total": 15},
        "tasks_stats": {"created": 12, "updated": 0, "deleted": 5, "total": 12},
        "coverage": {
            "verified_percent": 65,
            "assumed_percent": 85,
            "plan_status": "draft",
            "missing_count": 5
        },
        "deadlines": {
            "next_deadline": "2025-11-30",
            "next_deadline_university": "UC Berkeley"
        }
    }
    """
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        user = request.user

        track = request.data.get('track', 'direct')
        intake = request.data.get('intake', '')
        degree_level = request.data.get('degree_level', '')
        citizenship = request.data.get('citizenship', '')

        if track not in ['direct', 'foundation']:
            return Response(
                {'error': 'Invalid track. Must be "direct" or "foundation"'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            from .services.plan_generation import generate_admission_plan

            result = generate_admission_plan(
                user=user,
                track=track,
                intake=intake,
                degree_level=degree_level,
                citizenship=citizenship
            )

            if result['status'] == 'error':
                return Response(
                    result,
                    status=status.HTTP_400_BAD_REQUEST
                )

            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Plan generation error: {str(e)}", exc_info=True)
            return Response(
                {'error': f'Plan generation failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PersonalizePlanView(APIView):
    """
    API endpoint to provide additional context and get personalized plan enhancement.

    POST /api/todos/plan/personalize/
    Request: {"additional_context": "I won math olympiad..."}
    Response: {
        "personalized_tasks": [...],
        "alternative_paths": [...],
        "cost": 0.003
    }
    """
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        """
        Provide additional context and get LLM-powered personalization.

        This endpoint:
        1. Updates user's profile with additional_context
        2. Runs LLM enhancement to generate personalized tasks
        3. Suggests alternative paths based on eligibility gaps
        """
        user = request.user
        additional_context = request.data.get('additional_context', '').strip()

        logger.info(f"[PersonalizePlan] User {user.id} providing additional context")

        # Update profile with additional_context
        try:
            from university_profile.models import UniversitySeekerProfile
            profile = UniversitySeekerProfile.objects.get(user=user)
            profile.additional_context = additional_context
            profile.save()
            logger.info(f"[PersonalizePlan] Updated additional_context for user {user.id}")
        except UniversitySeekerProfile.DoesNotExist:
            return Response(
                {'error': 'Profile not found. Please complete your profile first.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get shortlist and requirements
        try:
            from university_recommender.models import UniversityShortlist
            from requirements.models import RequirementInstance

            shortlist = UniversityShortlist.objects.filter(user=user).select_related('university')
            requirement_instances = RequirementInstance.objects.filter(user=user)

            if shortlist.count() == 0:
                return Response(
                    {'error': 'No universities in shortlist. Please add universities first.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Build eligibility report
            missing_count = requirement_instances.filter(status='missing').count()
            eligibility_report = {
                'overall_status': 'eligible' if missing_count == 0 else 'partially_eligible',
                'critical_gaps': [
                    {'gap': r.requirement_key, 'solution': r.notes}
                    for r in requirement_instances.filter(status='missing')[:10]
                ]
            }

            # Generate LLM enhancement
            from ai.admission_plan_enhancer import AdmissionPlanEnhancer
            enhancer = AdmissionPlanEnhancer(user)

            enhancement = enhancer.enhance_plan(
                shortlist=shortlist,
                eligibility_report=eligibility_report,
                requirement_instances=requirement_instances
            )

            logger.info(
                f"[PersonalizePlan] Generated {len(enhancement.get('personalized_tasks', []))} tasks, "
                f"{len(enhancement.get('alternative_paths', []))} paths, "
                f"cost: ${enhancement.get('cost', 0):.4f}"
            )

            return Response({
                'status': 'success',
                'enhancement': enhancement,
                'message': f'Generated {len(enhancement.get("personalized_tasks", []))} personalized tasks and {len(enhancement.get("alternative_paths", []))} alternative paths'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"[PersonalizePlan] Error: {str(e)}", exc_info=True)
            return Response(
                {'error': f'Personalization failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

