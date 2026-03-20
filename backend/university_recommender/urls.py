from django.urls import path
from . import views

app_name = 'university_recommender'

urlpatterns = [
    # Recommendations
    path('recommend/generate/', views.GenerateRecommendationsView.as_view(), name='generate-recommendations'),
    path('feedback/', views.SubmitFeedbackView.as_view(), name='submit-feedback'),

    # Shortlist Management
    path('shortlist/', views.UniversityShortlistView.as_view(), name='shortlist'),
    path('shortlist/remove/', views.RemoveFromShortlistView.as_view(), name='remove-from-shortlist'),

    # University Database
    path('universities/search/', views.UniversitySearchView.as_view(), name='search-universities'),

    # Analytics (admin only)
    path('analytics/', views.AnalyticsView.as_view(), name='analytics'),
]
