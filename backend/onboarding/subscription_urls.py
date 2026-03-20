"""
Subscription-specific URL configuration.
"""
from django.urls import path

from .views import (
    list_subscription_plans,
    current_subscription,
    create_checkout_session,
    cancel_subscription,
)

urlpatterns = [
    path('plans/', list_subscription_plans, name='plans'),
    path('current/', current_subscription, name='current'),
    path('create-checkout-session/', create_checkout_session, name='create-checkout'),
    path('cancel/', cancel_subscription, name='cancel'),
]
