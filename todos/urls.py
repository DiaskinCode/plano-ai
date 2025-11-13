from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TodoViewSet, GenerateTasksView, TaskStatusView
from .daily_planner_views import DailyPlannerViewSet
from .weekly_review_views import WeeklyReviewViewSet
from .evidence_views import TaskEvidenceViewSet
from .task_run_views import TaskRunViewSet
from .insights_views import (
    get_category_progress,
    get_skip_patterns,
    get_ai_insights,
    mark_insight_read,
    dismiss_insight,
    complete_task_with_feedback,
    suggest_smart_task,
)
from .split_views import (
    split_task,
    check_split_candidates,
    bulk_split_tasks,
)

# Main router for todos
todo_router = DefaultRouter()
todo_router.register(r'', TodoViewSet, basename='todo')

# Separate routers for other viewsets
planner_router = DefaultRouter()
planner_router.register(r'', DailyPlannerViewSet, basename='daily-planner')

review_router = DefaultRouter()
review_router.register(r'', WeeklyReviewViewSet, basename='weekly-review')

evidence_router = DefaultRouter()
evidence_router.register(r'', TaskEvidenceViewSet, basename='task-evidence')

runs_router = DefaultRouter()
runs_router.register(r'', TaskRunViewSet, basename='task-runs')

urlpatterns = [
    path('generate/', GenerateTasksView.as_view(), name='generate-tasks'),
    path('task-status/<str:task_id>/', TaskStatusView.as_view(), name='task-status'),
    path('daily-planner/', include(planner_router.urls)),
    path('weekly-review/', include(review_router.urls)),
    path('evidence/', include(evidence_router.urls)),
    path('task-runs/', include(runs_router.urls)),

    # NEW: AI Insights & Smart Suggestions
    path('insights/category-progress/', get_category_progress, name='category-progress'),
    path('insights/skip-patterns/', get_skip_patterns, name='skip-patterns'),
    path('insights/', get_ai_insights, name='ai-insights'),
    path('insights/<int:insight_id>/read/', mark_insight_read, name='mark-insight-read'),
    path('insights/<int:insight_id>/dismiss/', dismiss_insight, name='dismiss-insight'),
    path('<int:task_id>/complete-with-feedback/', complete_task_with_feedback, name='complete-with-feedback'),
    path('suggest-smart/', suggest_smart_task, name='suggest-smart-task'),

    # Task splitting (Phase 2.3)
    path('<int:task_id>/split/', split_task, name='split-task'),
    path('split/candidates/', check_split_candidates, name='split-candidates'),
    path('split/bulk/', bulk_split_tasks, name='bulk-split'),

    path('', include(todo_router.urls)),
]
