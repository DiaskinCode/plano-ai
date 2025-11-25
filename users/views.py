from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.utils import timezone

from .models import User, UserProfile
from .serializers import (
    UserRegistrationSerializer,
    UserSerializer,
    UserProfileSerializer,
    OnboardingSerializer
)
from ai.performance_analyzer import performance_analyzer


class RegisterView(generics.CreateAPIView):
    """User registration endpoint"""
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = UserRegistrationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate tokens
        refresh = RefreshToken.for_user(user)

        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """User login endpoint"""
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response(
                {'error': 'Please provide both email and password'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(username=email, password=password)

        if not user:
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        refresh = RefreshToken.for_user(user)

        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        })


class ProfileView(generics.RetrieveUpdateAPIView):
    """User profile endpoint"""
    serializer_class = UserProfileSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        # Get or create profile for the authenticated user
        profile, created = UserProfile.objects.get_or_create(
            user=self.request.user,
            defaults={'name': self.request.user.username}
        )
        return profile


class OnboardingView(APIView):
    """Complete onboarding endpoint"""
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        profile = UserProfile.objects.get(user=request.user)
        serializer = OnboardingSerializer(profile, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Onboarding completed successfully',
                'profile': UserProfileSerializer(profile).data
            })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST'])
@permission_classes([permissions.IsAuthenticated])
def performance_insights(request):
    """
    GET: Retrieve cached performance insights from profile
    POST: Trigger fresh performance analysis

    Response:
    {
        "completion_rate": 0.65,
        "risk_level": "medium",
        "optimal_schedule": {...},
        "task_type_performance": {...},
        "blockers": [...],
        "strengths": [...],
        "warnings": [...],
        "recommended_actions": [...]
    }
    """
    user = request.user
    profile = user.profile

    if request.method == 'POST':
        # Trigger fresh analysis
        analysis = performance_analyzer.analyze_user_performance(user)

        # Update profile
        profile.performance_insights = analysis
        profile.last_performance_analysis = timezone.now()
        profile.save(update_fields=['performance_insights', 'last_performance_analysis'])

        return Response(analysis)

    else:
        # Return cached insights
        if not profile.performance_insights:
            # No cached data, run analysis
            analysis = performance_analyzer.analyze_user_performance(user)
            profile.performance_insights = analysis
            profile.last_performance_analysis = timezone.now()
            profile.save(update_fields=['performance_insights', 'last_performance_analysis'])

        return Response(profile.performance_insights)


@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def delete_account(request):
    """
    Delete the authenticated user's account and all associated data.
    This action is irreversible.
    """
    import logging
    logger = logging.getLogger(__name__)

    user = request.user
    logger.info(f'Delete account request for user: {user.email}')

    try:
        # Delete the user (this will cascade delete all related data)
        user_email = user.email
        user.delete()
        logger.info(f'Successfully deleted account for user: {user_email}')

        return Response({
            'message': 'Account deleted successfully'
        }, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f'Failed to delete account for user {user.email}: {str(e)}', exc_info=True)
        return Response({
            'error': f'Failed to delete account: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
