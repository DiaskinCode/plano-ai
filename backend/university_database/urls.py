"""
University Database URL Configuration
"""

from django.urls import path

from . import views

app_name = "university_database"

urlpatterns = [
    path(
        "featured/",
        views.FeaturedUniversitiesView.as_view(),
        name="featured-universities",
    ),
]
