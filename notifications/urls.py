from django.urls import path
from . import views

urlpatterns = [
    path('register-token/', views.register_push_token, name='register_push_token'),
    path('preferences/', views.notification_preferences, name='notification_preferences'),
    path('test/', views.send_test_notification, name='send_test_notification'),
]
