"""
Social URL Configuration - College Application Platform

API endpoints for social features
"""

from django.urls import path, include
from rest_framework.routers import SimpleRouter, DefaultRouter
from .views import (
    UserProfileViewSet,
    FollowViewSet,
    FollowActionViewSet,
    UserSearchViewSet,
    DirectMessageViewSet,
    BlockedUserViewSet,
)

# Create router and register ViewSets
router = DefaultRouter()
router.register(r'profile', UserProfileViewSet, basename='profile')
router.register(r'follows', FollowViewSet, basename='follow')
router.register(r'search', UserSearchViewSet, basename='user-search')
router.register(r'messages', DirectMessageViewSet, basename='message')
router.register(r'blocked', BlockedUserViewSet, basename='blocked-user')

# Simple router for follow actions (by username)
follow_router = SimpleRouter()
follow_router.register(r'follow', FollowActionViewSet, basename='follow-action')

app_name = 'social'

urlpatterns = [
    path('', include(router.urls)),
    # Follow/unfollow by username
    path('', include(follow_router.urls)),
]
