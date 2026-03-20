"""
API views for the structured onboarding flow.
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Q

from .models import (
    OnboardingState,
    SubscriptionPlan,
    UserSubscription,
    TargetUniversity,
    ExtracurricularActivity,
    OnboardingSnapshot,
)
from .serializers import (
    OnboardingStateSerializer,
    SubscriptionPlanSerializer,
    UserSubscriptionSerializer,
    TargetUniversitySerializer,
    ExtracurricularActivitySerializer,
    OnboardingSnapshotSerializer,
    StartOnboardingSerializer,
    SaveStepSerializer,
    AcademicProfileSerializer,
    TestScoresSerializer,
    PlanSelectionSerializer,
    GeneratePlanSerializer,
    CreateCheckoutSessionSerializer,
    CancelSubscriptionSerializer,
)

User = get_user_model()


# ==================== Onboarding Flow Views ====================

@api_view(['POST'])
@permission_classes([permissions.AllowAny])  # Allow during onboarding
def start_onboarding(request):
    """
    Initialize onboarding for a new user.

    POST /api/onboarding/start/
    """
    try:
        # For guest/unauthenticated users, return success without database state
        if not request.user.is_authenticated:
            return Response({
                'detail': 'Onboarding started successfully (guest mode)',
                'current_step': 0,
                'data': {},
            }, status=status.HTTP_200_OK)
        # Check if onboarding already exists
        onboarding_state, created = OnboardingState.objects.get_or_create(
            user=request.user,
            defaults={
                'current_step': 0,
                'selected_language': 'en',
                'data': {},
            }
        )

        if not created:
            return Response({
                'detail': 'Onboarding already started',
                'current_step': onboarding_state.current_step,
                'data': onboarding_state.data,
            }, status=status.HTTP_200_OK)

        serializer = OnboardingStateSerializer(onboarding_state)
        return Response({
            'detail': 'Onboarding started successfully',
            'onboarding': serializer.data,
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({
            'detail': f'Error starting onboarding: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'PUT'])
@permission_classes([permissions.AllowAny])  # Allow during onboarding
def onboarding_state(request):
    """
    Get or update current onboarding state.

    GET /api/onboarding/state/
    PUT /api/onboarding/state/
    """
    try:
        # For guest/unauthenticated users, return empty state or stored AsyncStorage data
        if not request.user.is_authenticated:
            if request.method == 'GET':
                # Return empty state for guest users
                return Response({
                    'current_step': 0,
                    'selected_language': 'en',
                    'data': {},
                }, status=status.HTTP_200_OK)
            else:
                # Don't allow saving state for unauthenticated users
                return Response({
                    'detail': 'Please complete authentication first'
                }, status=status.HTTP_401_UNAUTHORIZED)

        onboarding_state = OnboardingState.objects.get(user=request.user)
        serializer = OnboardingStateSerializer(onboarding_state)

        if request.method == 'GET':
            return Response(serializer.data, status=status.HTTP_200_OK)

        elif request.method == 'PUT':
            # Update selected language or other fields
            data = request.data.get('data', {})
            onboarding_state.data.update(data)

            if 'selected_language' in request.data:
                onboarding_state.selected_language = request.data['selected_language']

            onboarding_state.save()
            return Response(OnboardingStateSerializer(onboarding_state).data, status=status.HTTP_200_OK)

    except OnboardingState.DoesNotExist:
        return Response({
            'detail': 'Onboarding not found. Please start onboarding first.'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'detail': f'Error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def save_onboarding_step(request):
    """
    Save data for a specific onboarding step.

    POST /api/onboarding/step/
    Body: {
        "step": 3,
        "data": {"name": "John", "username": "john123"},
        "time_spent_seconds": 45,
        "mark_complete": true
    }
    """
    try:
        serializer = SaveStepSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        step = serializer.validated_data['step']
        data = serializer.validated_data['data']
        time_spent = serializer.validated_data['time_spent_seconds']
        mark_complete = serializer.validated_data['mark_complete']

        # Get or create onboarding state
        onboarding_state, created = OnboardingState.objects.get_or_create(
            user=request.user,
            defaults={
                'current_step': step,
                'data': {},
            }
        )

        # Update the data for this step
        onboarding_state.data[f'step_{step}'] = data
        onboarding_state.data['last_updated'] = timezone.now().isoformat()

        # Update current step
        if step > onboarding_state.current_step:
            onboarding_state.current_step = step

        # Mark step as complete if requested
        if mark_complete and step not in onboarding_state.completed_steps:
            onboarding_state.completed_steps.append(step)

        onboarding_state.save()

        # Create snapshot for analytics
        OnboardingSnapshot.objects.create(
            user=request.user,
            step=step,
            data=data,
            time_spent_seconds=time_spent
        )

        return Response({
            'detail': 'Step saved successfully',
            'current_step': onboarding_state.current_step,
            'completed_steps': onboarding_state.completed_steps,
            'progress_percentage': onboarding_state.get_progress_percentage(),
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'detail': f'Error saving step: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def complete_onboarding(request):
    """
    Mark onboarding as complete.

    POST /api/onboarding/complete/
    """
    try:
        onboarding_state = OnboardingState.objects.get(user=request.user)
        onboarding_state.is_onboarding_complete = True
        onboarding_state.current_step = 13
        if 13 not in onboarding_state.completed_steps:
            onboarding_state.completed_steps.append(13)
        onboarding_state.save()

        return Response({
            'detail': 'Onboarding completed successfully',
            'onboarding': OnboardingStateSerializer(onboarding_state).data,
        }, status=status.HTTP_200_OK)

    except OnboardingState.DoesNotExist:
        return Response({
            'detail': 'Onboarding not found'
        }, status=status.HTTP_404_NOT_FOUND)


# ==================== Academic Profile Endpoints ====================

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def save_academic_profile(request):
    """
    Save academic profile data (Step 4).

    POST /api/onboarding/academic-profile/
    """
    try:
        serializer = AcademicProfileSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Get onboarding state
        onboarding_state = OnboardingState.objects.get(user=request.user)

        # Save to onboarding data
        onboarding_state.data['academic_profile'] = serializer.validated_data
        onboarding_state.save()

        return Response({
            'detail': 'Academic profile saved successfully',
            'data': serializer.validated_data,
        }, status=status.HTTP_200_OK)

    except OnboardingState.DoesNotExist:
        return Response({
            'detail': 'Onboarding not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def save_test_scores(request):
    """
    Save test scores (Step 5).

    POST /api/onboarding/test-scores/
    """
    try:
        serializer = TestScoresSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Get onboarding state
        onboarding_state = OnboardingState.objects.get(user=request.user)

        # Save to onboarding data
        onboarding_state.data['test_scores'] = serializer.validated_data
        onboarding_state.save()

        return Response({
            'detail': 'Test scores saved successfully',
            'data': serializer.validated_data,
        }, status=status.HTTP_200_OK)

    except OnboardingState.DoesNotExist:
        return Response({
            'detail': 'Onboarding not found'
        }, status=status.HTTP_404_NOT_FOUND)


# ==================== Extracurriculars Endpoints ====================

class ExtracurricularActivityViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing extracurricular activities.
    """
    serializer_class = ExtracurricularActivitySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ExtracurricularActivity.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Auto-set user and save priority
        max_priority = ExtracurricularActivity.objects.filter(
            user=self.request.user
        ).count()
        serializer.save(user=self.request.user, priority_order=max_priority + 1)

    @action(detail=False, methods=['get'])
    def all(self, request):
        """Get all extracurriculars for the user"""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


# ==================== Target Universities Endpoints ====================

class TargetUniversityViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing target universities.
    """
    serializer_class = TargetUniversitySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return TargetUniversity.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Auto-set user and save priority
        max_priority = TargetUniversity.objects.filter(
            user=self.request.user
        ).count()
        serializer.save(user=self.request.user, priority_order=max_priority + 1)

    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """
        Bulk create target universities from AI suggestions.

        POST /api/onboarding/target-universities/bulk_create/
        Body: {
            "universities": [
                {
                    "university_name": "MIT",
                    "category": "reach",
                    ...
                }
            ]
        }
        """
        universities_data = request.data.get('universities', [])

        if not universities_data:
            return Response({
                'detail': 'No universities provided'
            }, status=status.HTTP_400_BAD_REQUEST)

        created_universities = []
        for uni_data in universities_data:
            uni_data['user'] = request.user.id
            serializer = self.get_serializer(data=uni_data)
            if serializer.is_valid():
                serializer.save()
                created_universities.append(serializer.data)

        return Response({
            'detail': f'Created {len(created_universities)} universities',
            'universities': created_universities,
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def selected(self, request):
        """Get only selected universities"""
        queryset = self.get_queryset().filter(is_selected=True)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)



# ==================== Plan Selection & Generation ====================

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def save_plan_selection(request):
    """
    Save selected plan types (Step 8).

    POST /api/onboarding/plan-selection/
    """
    try:
        serializer = PlanSelectionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Get onboarding state
        onboarding_state = OnboardingState.objects.get(user=request.user)

        # Save to onboarding data
        onboarding_state.data['plan_selection'] = serializer.validated_data

        # Calculate estimated tasks and timeline
        selected_plans = serializer.validated_data.get('selected_plans', [])
        estimated_tasks = 0
        estimated_months = 0

        if 'university' in selected_plans:
            estimated_tasks += 120
            estimated_months = max(estimated_months, 8)

        if 'exam_prep' in selected_plans:
            exam_types = serializer.validated_data.get('exam_types', [])
            estimated_tasks += len(exam_types) * 80
            estimated_months = max(estimated_months, 6)

        if 'language_tests' in selected_plans:
            test_types = serializer.validated_data.get('language_test_types', [])
            estimated_tasks += len(test_types) * 60
            estimated_months = max(estimated_months, 4)

        onboarding_state.data['plan_estimates'] = {
            'estimated_tasks': estimated_tasks,
            'estimated_months': estimated_months,
        }

        onboarding_state.save()

        return Response({
            'detail': 'Plan selection saved successfully',
            'data': serializer.validated_data,
            'estimates': onboarding_state.data['plan_estimates'],
        }, status=status.HTTP_200_OK)

    except OnboardingState.DoesNotExist:
        return Response({
            'detail': 'Onboarding not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def generate_ai_plan(request):
    """
    Trigger AI plan generation (Step 9).

    POST /api/onboarding/generate-plan/
    Body: {
        "include_timeline": true,
        "include_tasks": true,
        "include_milestones": true,
        "start_date": "2025-01-15",
        "exam_types": ["SAT", "IELTS"]
    }
    """
    try:
        from ai.onboarding_services import PlanGenerator
        from .middleware import check_subscription_status

        serializer = GeneratePlanSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Get or create onboarding state
        onboarding_state, created = OnboardingState.objects.get_or_create(
            user=request.user,
            defaults={
                'current_step': 0,
                'completed_steps': [],
                'data': {},
                'selected_language': 'en',
                'is_onboarding_complete': False,
            }
        )

        if created:
            print(f"[GeneratePlan] Created new OnboardingState for user {request.user.email}")

        # If onboarding state is empty, try to get data from request body (frontend local storage)
        if not onboarding_state.data or 'academic_profile' not in onboarding_state.data:
            frontend_data = request.data.get('onboardingData', {})
            if frontend_data:
                print(f"[GeneratePlan] Using frontend data for plan generation")
                onboarding_state.data = frontend_data
                onboarding_state.save()

        # Check if prerequisites are met
        if 'academic_profile' not in onboarding_state.data:
            return Response({
                'detail': 'Academic profile required'
            }, status=status.HTTP_400_BAD_REQUEST)

        if 'suggested_universities' not in onboarding_state.data:
            return Response({
                'detail': 'Please select target universities first'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Extract student profile
        academic_profile = onboarding_state.data.get('academic_profile', {})
        test_scores = onboarding_state.data.get('test_scores', {})

        student_profile = {
            'gpa': academic_profile.get('gpa'),
            'sat_score': test_scores.get('sat_score'),
            'act_score': test_scores.get('act_score'),
            'toefl_score': test_scores.get('toefl_score'),
            'ielts_score': test_scores.get('ielts_score'),
            'ib_score': test_scores.get('ib_score'),
        }

        # Get target universities from selected/suggested ones
        suggested_unis = onboarding_state.data.get('suggested_universities', {})

        # Check if it's in flat array format (from frontend) or nested format (backend)
        target_universities = []
        if isinstance(suggested_unis, list):
            # Flat array format from frontend - each uni has 'category' field
            for uni in suggested_unis:
                if isinstance(uni, dict):
                    target_universities.append({
                        'university_name': uni.get('name') or uni.get('university_name'),
                        'category': uni.get('category', 'target'),
                        'deadline': uni.get('deadline') or uni.get('application_deadline'),
                        'tuition': uni.get('tuition') or uni.get('tuition_per_year'),
                    })
        else:
            # Nested format from backend - reach/target/safety categories
            for category in ['reach', 'target', 'safety']:
                for uni in suggested_unis.get(category, []):
                    target_universities.append({
                        'university_name': uni.get('university_name'),
                        'category': category,
                        'deadline': uni.get('application_deadline'),
                        'tuition': uni.get('tuition_per_year'),
                    })

        if not target_universities:
            return Response({
                'detail': 'No target universities selected'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Build plan options
        plan_options = {
            'include_timeline': serializer.validated_data.get('include_timeline', True),
            'include_tasks': serializer.validated_data.get('include_tasks', True),
            'include_milestones': serializer.validated_data.get('include_milestones', True),
            'start_date': serializer.validated_data.get('start_date', timezone.now().isoformat()),
            'exam_types': serializer.validated_data.get('exam_types', ['SAT']),
        }

        # Generate the plan
        generator = PlanGenerator()
        plan = generator.generate_plan(
            student_profile=student_profile,
            target_universities=target_universities,
            plan_options=plan_options,
        )

        # Check subscription status for paywall
        has_subscription, sub_data = check_subscription_status(request.user)

        if not has_subscription:
            # Preview mode: Show only Month 1 (first ~25 tasks)
            month_1_tasks = [t for t in plan.get('tasks', []) if t.get('month') == 1]
            month_1_milestones = [m for m in plan.get('milestones', []) if m.get('month') == 1]

            preview_plan = {
                **plan,
                'tasks': month_1_tasks,
                'milestones': month_1_milestones,
                'is_preview': True,
                'visible_months': 1,
                'total_tasks_in_preview': len(month_1_tasks),
                'total_tasks_hidden': len(plan.get('tasks', [])) - len(month_1_tasks),
            }

            # Save preview to onboarding state
            onboarding_state.data['generated_plan'] = preview_plan
            onboarding_state.data['plan_generation'] = {
                'status': 'preview',
                'started_at': timezone.now().isoformat(),
                'completed_at': timezone.now().isoformat(),
                **plan_options,
            }
            onboarding_state.save()

            return Response({
                'detail': 'Plan preview generated (Month 1 only)',
                'plan': preview_plan,
                'paywall': {
                    'is_preview': True,
                    'has_subscription': False,
                    'message': 'Subscribe to unlock the full 8-month plan with 200+ tasks',
                    'plans': [
                        {
                            'name': 'Basic',
                            'price_monthly': 25,
                            'features': ['Full 8-month plan', '200+ tasks', 'AI suggestions', 'Progress tracking'],
                            'is_popular': False,
                        },
                        {
                            'name': 'Pro',
                            'price_monthly': 100,
                            'features': ['Everything in Basic', 'Personal mentor', 'Weekly check-ins', 'Essay reviews'],
                            'is_popular': True,
                        },
                        {
                            'name': 'Premium',
                            'price_monthly': 200,
                            'features': ['Everything in Pro', 'Dedicated support', 'Application review', 'Interview prep'],
                            'is_popular': False,
                        },
                    ],
                },
            }, status=status.HTTP_200_OK)

        # Full plan for subscribers
        plan['is_preview'] = False
        plan['visible_months'] = 8

        # Save generated plan to onboarding state
        onboarding_state.data['generated_plan'] = plan
        onboarding_state.data['plan_generation'] = {
            'status': 'completed',
            'started_at': timezone.now().isoformat(),
            'completed_at': timezone.now().isoformat(),
            **plan_options,
        }
        onboarding_state.save()

        return Response({
            'detail': 'Plan generated successfully',
            'plan': plan,
            'subscription': sub_data,
        }, status=status.HTTP_200_OK)

    except OnboardingState.DoesNotExist:
        return Response({
            'detail': 'Onboarding not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'detail': f'Error generating plan: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== Subscription Endpoints ====================

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def list_subscription_plans(request):
    """
    List all available subscription plans.

    GET /api/subscription/plans/
    """
    try:
        plans = SubscriptionPlan.objects.filter(is_active=True)
        serializer = SubscriptionPlanSerializer(plans, many=True)
        return Response({
            'plans': serializer.data,
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'detail': f'Error fetching plans: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def current_subscription(request):
    """
    Get current user's subscription.

    GET /api/subscription/current/
    """
    try:
        subscription = UserSubscription.objects.get(user=request.user)
        serializer = UserSubscriptionSerializer(subscription)
        return Response(serializer.data, status=status.HTTP_200_OK)

    except UserSubscription.DoesNotExist:
        return Response({
            'detail': 'No active subscription found',
            'has_subscription': False,
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_checkout_session(request):
    """
    Simple subscription activation (no payment processing).

    POST /api/subscription/create-checkout-session/
    Body: {
        "plan_name": "pro",
        "billing_cycle": "monthly"
    }
    """
    try:
        serializer = CreateCheckoutSessionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        plan_name = serializer.validated_data['plan_name'].lower()
        billing_cycle = serializer.validated_data['billing_cycle']

        # Map plan names to database names
        plan_mapping = {
            'basic': 'basic',
            'pro': 'pro',
            'premium': 'premium',
        }

        if plan_name not in plan_mapping:
            return Response({
                'detail': f'Invalid plan name. Choose from: {", ".join(plan_mapping.keys())}'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get or create the plan
        plan, created = SubscriptionPlan.objects.get_or_create(
            name=plan_mapping[plan_name],
            defaults={
                'name': plan_mapping[plan_name],
                'price_monthly': 25 if plan_name == 'basic' else (100 if plan_name == 'pro' else 200),
                'price_yearly': 240 if plan_name == 'basic' else (960 if plan_name == 'pro' else 1920),
                'features': {
                    'basic': ['Full plan', 'AI suggestions', 'Community'],
                    'pro': ['Everything in Basic', 'Mentor', 'Weekly check-ins'],
                    'premium': ['Everything in Pro', 'Dedicated support', 'Application review'],
                }[plan_name],
                'is_popular': plan_name == 'pro',
                'order': 1 if plan_name == 'basic' else (2 if plan_name == 'pro' else 3),
            }
        )

        # Create or update subscription
        subscription, created = UserSubscription.objects.get_or_create(
            user=request.user,
            defaults={
                'plan': plan,
                'status': 'active',
            }
        )

        if not created:
            # Update existing subscription
            subscription.plan = plan
            subscription.status = 'active'
            subscription.cancel_at_period_end = False
            subscription.save()

        return Response({
            'detail': 'Subscription activated successfully',
            'subscription': UserSubscriptionSerializer(subscription).data,
            'plan': SubscriptionPlanSerializer(plan).data,
            'message': 'Subscription activated (demo mode - no payment processed)',
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'detail': f'Error activating subscription: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def cancel_subscription(request):
    """
    Cancel user's subscription.

    POST /api/subscription/cancel/
    """
    try:
        serializer = CancelSubscriptionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        subscription = UserSubscription.objects.get(user=request.user)

        # TODO: Integrate with Stripe
        # For now, just update the status
        if serializer.validated_data['cancel_at_period_end']:
            subscription.cancel_at_period_end = True
            subscription.status = 'canceled'
        else:
            subscription.status = 'canceled'

        subscription.save()

        return Response({
            'detail': 'Subscription canceled successfully',
            'subscription': UserSubscriptionSerializer(subscription).data,
        }, status=status.HTTP_200_OK)

    except UserSubscription.DoesNotExist:
        return Response({
            'detail': 'Subscription not found'
        }, status=status.HTTP_404_NOT_FOUND)


# ==================== Analytics & Recovery ====================

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def onboarding_analytics(request):
    """
    Get onboarding analytics for the user.

    GET /api/onboarding/analytics/
    """
    try:
        onboarding_state = OnboardingState.objects.get(user=request.user)
        snapshots = OnboardingSnapshot.objects.filter(user=request.user)

        total_time_seconds = sum(s.time_spent_seconds for s in snapshots)

        return Response({
            'current_step': onboarding_state.current_step,
            'completed_steps': onboarding_state.completed_steps,
            'progress_percentage': onboarding_state.get_progress_percentage(),
            'total_time_seconds': total_time_seconds,
            'total_time_minutes': round(total_time_seconds / 60, 2),
            'snapshot_count': snapshots.count(),
            'started_at': onboarding_state.created_at,
            'last_updated': onboarding_state.updated_at,
        }, status=status.HTTP_200_OK)

    except OnboardingState.DoesNotExist:
        return Response({
            'detail': 'Onboarding not found'
        }, status=status.HTTP_404_NOT_FOUND)
