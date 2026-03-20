from django.urls import path
from . import views
from .contextual_pulse_views import generate_contextual_pulse

urlpatterns = [
    # Existing analytics endpoints
    path('overview/', views.OverviewAnalyticsView.as_view(), name='analytics-overview'),
    path('time-focus/', views.TimeFocusAnalyticsView.as_view(), name='analytics-time-focus'),
    path('tasks-outcomes/', views.TasksOutcomesAnalyticsView.as_view(), name='analytics-tasks-outcomes'),
    path('milestones-path/', views.MilestonesPathAnalyticsView.as_view(), name='analytics-milestones-path'),
    path('habits-quality/', views.HabitsQualityAnalyticsView.as_view(), name='analytics-habits-quality'),
    path('streak/', views.StreakView.as_view(), name='streak'),

    # Weekly reflection endpoints
    path('weekly-reflection/', views.WeeklyReflectionView.as_view(), name='weekly-reflection'),
    path('generate-reflection/', views.GenerateReflectionView.as_view(), name='generate-reflection'),
    path('behavior-patterns/', views.BehaviorPatternsView.as_view(), name='behavior-patterns'),
    path('reflection-history/', views.ReflectionHistoryView.as_view(), name='reflection-history'),

    # Daily Pulse endpoints
    path('daily-pulse/', views.DailyPulseView.as_view(), name='daily-pulse'),
    path('daily-pulse/generate/', views.GenerateDailyPulseView.as_view(), name='generate-daily-pulse'),
    path('daily-pulse/mark-shown/', views.DailyPulseMarkShownView.as_view(), name='daily-pulse-mark-shown'),
    path('daily-pulse/send-to-chat/', views.SendDailyPulseToChatView.as_view(), name='send-daily-pulse-to-chat'),

    # Context-aware Daily Pulse (Phase 3.2)
    path('daily-pulse/contextual/', generate_contextual_pulse, name='contextual-daily-pulse'),
]
