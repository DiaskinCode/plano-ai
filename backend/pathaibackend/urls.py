"""
URL configuration for pathaibackend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.urls import include, path


def health_check(request):
    """Health check endpoint for Railway and monitoring services"""
    return JsonResponse({"status": "ok", "service": "pathAI-backend"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health_check, name="health_check"),
    path("api/auth/", include("users.urls")),
    path("api/ai/", include("ai.urls")),
    path("api/todos/", include("todos.urls")),
    path("api/vision/", include("vision.urls")),
    path("api/chat/", include("chat.urls")),
    path("api/analytics/", include("analytics.urls")),
    path("api/notifications/", include("notifications.urls")),
    path("api/onboarding/", include("onboarding.urls")),
    path("api/subscription/", include("onboarding.subscription_urls")),
    path("api/", include("community.urls")),
    path("api/social/", include("social.urls")),
    # University Recommendation System
    path("api/university-profile/", include("university_profile.urls")),
    path("api/university-recommender/", include("university_recommender.urls")),
    path("api/universities/", include("university_database.urls")),
    # Mentorship System
    path("api/", include("mentorship.urls")),
]

# Serve static files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
