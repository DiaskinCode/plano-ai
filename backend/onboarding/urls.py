"""
URL configuration for the onboarding API.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    # Onboarding flow
    start_onboarding,
    onboarding_state,
    save_onboarding_step,
    complete_onboarding,
    # Academic data
    save_academic_profile,
    save_test_scores,
    # Plan selection & generation
    save_plan_selection,
    generate_ai_plan,
    # Analytics
    onboarding_analytics,
    # Subscription
    list_subscription_plans,
    current_subscription,
    create_checkout_session,
    cancel_subscription,
    # ViewSets
    ExtracurricularActivityViewSet,
    TargetUniversityViewSet,
)

# Create routers for ViewSets
router = DefaultRouter()
router.register(r'extracurriculars', ExtracurricularActivityViewSet, basename='extracurricular')
router.register(r'target-universities', TargetUniversityViewSet, basename='target-university')

urlpatterns = [
    # Onboarding flow
    path('start/', start_onboarding, name='onboarding-start'),
    path('state/', onboarding_state, name='onboarding-state'),
    path('step/', save_onboarding_step, name='onboarding-save-step'),
    path('complete/', complete_onboarding, name='onboarding-complete'),

    # Academic data endpoints
    path('academic-profile/', save_academic_profile, name='save-academic-profile'),
    path('test-scores/', save_test_scores, name='save-test-scores'),

    # Plan selection & generation
    path('plan-selection/', save_plan_selection, name='save-plan-selection'),
    path('generate-plan/', generate_ai_plan, name='generate-plan'),

    # Analytics
    path('analytics/', onboarding_analytics, name='onboarding-analytics'),

    # Include ViewSet URLs
    path('', include(router.urls)),
]

# Subscription URLs (separate namespace)
subscription_urls = [
    path('plans/', list_subscription_plans, name='subscription-plans'),
    path('current/', current_subscription, name='subscription-current'),
    path('create-checkout-session/', create_checkout_session, name='create-checkout'),
    path('cancel/', cancel_subscription, name='cancel-subscription'),
]
