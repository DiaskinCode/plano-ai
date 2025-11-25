from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.routers import DefaultRouter
from .views import RegisterView, LoginView, ProfileView, OnboardingView, performance_insights, delete_account
from .goalspec_views import GoalSpecViewSet
from .onboarding_views import (
    research_path,
    generate_tasks,
    get_active_goalspecs,
    delete_goalspec,
    research_specific_university,
    validate_goal_feasibility,
    onboarding_chat_init,
    onboarding_chat_send,
    onboarding_chat_complete,
    onboarding_finalize,
    onboarding_status,
)
from .interventions_views import (
    check_intervention,
    apply_intervention,
    dismiss_intervention,
)

router = DefaultRouter()
router.register(r'goalspecs', GoalSpecViewSet, basename='goalspec')

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('delete-account/', delete_account, name='delete_account'),
    path('onboarding/', OnboardingView.as_view(), name='onboarding'),
    # New onboarding endpoints
    path('onboarding/research-path/', research_path, name='research_path'),
    path('onboarding/research-university/', research_specific_university, name='research_specific_university'),
    path('onboarding/generate-tasks/', generate_tasks, name='generate_tasks'),
    path('onboarding/active-goalspecs/', get_active_goalspecs, name='active_goalspecs'),
    path('onboarding/goalspec/<int:pk>/delete/', delete_goalspec, name='delete_goalspec'),
    path('onboarding/validate-feasibility/', validate_goal_feasibility, name='validate_feasibility'),
    # Conversational onboarding
    path('onboarding/status/', onboarding_status, name='onboarding_status'),
    path('onboarding/chat/init/', onboarding_chat_init, name='onboarding_chat_init'),
    path('onboarding/chat/send/', onboarding_chat_send, name='onboarding_chat_send'),
    path('onboarding/chat/complete/', onboarding_chat_complete, name='onboarding_chat_complete'),
    path('onboarding/finalize/', onboarding_finalize, name='onboarding_finalize'),
    # Performance insights
    path('performance/', performance_insights, name='performance_insights'),
    # Adaptive Coach interventions
    path('coach/check-intervention/', check_intervention, name='check_intervention'),
    path('coach/apply-intervention/', apply_intervention, name='apply_intervention'),
    path('coach/dismiss-intervention/', dismiss_intervention, name='dismiss_intervention'),
    path('', include(router.urls)),
]
