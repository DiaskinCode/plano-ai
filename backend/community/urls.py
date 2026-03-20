"""
Community URL Configuration - College Application Platform

API endpoints for community, posts, comments, voting
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CommunityViewSet, PostViewSet, CommentViewSet


# Create router and register ViewSets
router = DefaultRouter()
router.register(r'communities', CommunityViewSet, basename='community')
router.register(r'posts', PostViewSet, basename='post')
router.register(r'comments', CommentViewSet, basename='comment')

app_name = 'community'

urlpatterns = [
    path('', include(router.urls)),
]
