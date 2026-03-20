from django.urls import path
from . import views

urlpatterns = [
    path('', views.VisionListView.as_view(), name='vision-list'),
    path('analytics/', views.VisionAnalyticsView.as_view(), name='vision-analytics'),
    path('daily-headline/', views.DailyHeadlineView.as_view(), name='daily-headline'),
    path('<int:pk>/', views.VisionDetailView.as_view(), name='vision-detail'),
    path('<int:vision_id>/milestones/', views.MilestoneListView.as_view(), name='milestone-list'),
    path('milestones/<int:pk>/', views.MilestoneUpdateView.as_view(), name='milestone-update'),
    path('milestones/<int:pk>/schedule/', views.MilestoneScheduleTasksView.as_view(), name='milestone-schedule'),
    path('milestones/<int:pk>/add-buffer/', views.MilestoneAddBufferView.as_view(), name='milestone-add-buffer'),
    path('milestones/<int:pk>/mark-risk/', views.MilestoneMarkRiskView.as_view(), name='milestone-mark-risk'),
]
