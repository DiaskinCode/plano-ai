from django.urls import path
from . import views

app_name = 'university_profile'

urlpatterns = [
    # Profile Management
    path('profile/', views.UniversityProfileView.as_view(), name='profile'),
    path('profile/create/', views.UniversityProfileCreateView.as_view(), name='profile-create'),
    path('profile/delete/', views.UniversityProfileDeleteView.as_view(), name='profile-delete'),
    path('profile/completion/', views.ProfileCompletionView.as_view(), name='profile-completion'),

    # Extracurricular Activities
    path('profile/extracurriculars/', views.ExtracurricularActivityListView.as_view(), name='extracurriculars-list'),
    path('profile/extracurriculars/<int:pk>/', views.ExtracurricularActivityDetailView.as_view(), name='extracurricular-detail'),
]
