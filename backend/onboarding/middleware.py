"""
Paywall middleware for enforcing subscription requirements.

Simple paywall system without payment processing.
Checks if user has active subscription before allowing access to premium features.
"""
from django.http import JsonResponse
from rest_framework import status


class PaywallMiddleware:
    """
    Middleware to check subscription status for premium endpoints.

    Usage: Add 'onboarding.middleware.PaywallMiddleware' to MIDDLEWARE
    Or use the @require_subscription decorator on specific views.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Add paywall check to request object for views to use
        request.paywall_required = getattr(request, 'paywall_required', False)
        return self.get_response(request)


def check_subscription_status(user):
    """
    Check if user has active subscription.

    Returns:
        tuple: (has_subscription, subscription_data)
    """
    from .models import UserSubscription

    try:
        subscription = UserSubscription.objects.get(user=user)
        is_active = subscription.status == 'active'

        return is_active, {
            'has_subscription': True,
            'plan': subscription.plan.name,
            'status': subscription.status,
            'mentor_assigned': subscription.mentor_assigned is not None,
        }
    except UserSubscription.DoesNotExist:
        return False, {
            'has_subscription': False,
            'plan': None,
            'status': None,
        }


def require_subscription(view_func):
    """
    Decorator to require active subscription for view access.

    Usage:
        @require_subscription
        def my_premium_view(request):
            # Only accessible to active subscribers
            pass
    """
    def wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({
                'detail': 'Authentication required',
                'code': 'authentication_required',
            }, status=status.HTTP_401_UNAUTHORIZED)

        has_subscription, sub_data = check_subscription_status(request.user)

        if not has_subscription:
            return JsonResponse({
                'detail': 'Premium subscription required',
                'code': 'subscription_required',
                'subscription': sub_data,
                'plans': [
                    {
                        'name': 'Basic',
                        'price_monthly': 25,
                        'price_yearly': 240,
                        'features': [
                            'Full 8-month application plan',
                            '200+ personalized tasks',
                            'AI university suggestions',
                            'Progress tracking',
                            'Community access',
                        ],
                        'is_popular': False,
                    },
                    {
                        'name': 'Pro',
                        'price_monthly': 100,
                        'price_yearly': 960,
                        'features': [
                            'Everything in Basic',
                            'Personal mentor assigned',
                            'Weekly check-ins',
                            'Essay reviews',
                            'Priority support',
                        ],
                        'is_popular': True,
                    },
                    {
                        'name': 'Premium',
                        'price_monthly': 200,
                        'price_yearly': 1920,
                        'features': [
                            'Everything in Pro',
                            'Dedicated mentor',
                            'Unlimited support',
                            'Application review',
                            'Interview preparation',
                        ],
                        'is_popular': False,
                    },
                ],
            }, status=status.HTTP_402_PAYMENT_REQUIRED)

        # Add subscription info to request for use in view
        request.subscription = sub_data
        return view_func(request, *args, **kwargs)

    return wrapped_view


def get_preview_limit(view_func):
    """
    Decorator to allow preview of limited content for non-subscribers.

    Shows first 25 tasks (Month 1) for free, full plan requires subscription.
    """
    def wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({
                'detail': 'Authentication required',
            }, status=status.HTTP_401_UNAUTHORIZED)

        has_subscription, sub_data = check_subscription_status(request.user)

        # Add flag to request for view to check
        request.is_preview_mode = not has_subscription
        request.subscription = sub_data

        return view_func(request, *args, **kwargs)

    return wrapped_view
