from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'', views.NotificationViewSet, basename='notification')
router.register(r'preferences', views.NotificationPreferenceViewSet, basename='notification-preference')

urlpatterns = [
    # Push notification endpoints (existing)
    path('register-token/', views.register_push_token, name='register_push_token'),
    path('test/', views.send_test_notification, name='send_test_notification'),

    # In-app notification endpoints (new)
    path('', include(router.urls)),
]
