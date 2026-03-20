from django.urls import path
from .views import (
    GenerateScenariosView,
    SelectScenarioView,
    GenerateVisionView,
    IntegrateTaskView,
    EveningCheckinView,
    AnalyzeOpportunityView,
    ChatView,
    TranscribeAudioView,
    TaskAIAssistantView,
    TaskConversationHistoryView,
    GenerateTaskDescriptionView,
    CreateSubtasksFromAIView,
    GenerateAtomicTasksView
)
from .voice_views import (
    process_voice_command,
    voice_query,
    voice_capabilities,
)
from todos.views import TaskStatusView

urlpatterns = [
    path('generate_scenarios/', GenerateScenariosView.as_view(), name='generate_scenarios'),
    path('select_scenario/', SelectScenarioView.as_view(), name='select_scenario'),
    path('generate_vision/', GenerateVisionView.as_view(), name='generate_vision'),
    path('task-status/<str:task_id>/', TaskStatusView.as_view(), name='ai_task_status'),
    path('integrate_task/', IntegrateTaskView.as_view(), name='integrate_task'),
    path('evening_checkin/', EveningCheckinView.as_view(), name='evening_checkin'),
    path('analyze_opportunity/', AnalyzeOpportunityView.as_view(), name='analyze_opportunity'),
    path('chat/', ChatView.as_view(), name='chat'),
    path('transcribe_audio/', TranscribeAudioView.as_view(), name='transcribe_audio'),
    path('task-assistant/', TaskAIAssistantView.as_view(), name='task_ai_assistant'),
    path('task-conversation/<int:task_id>/', TaskConversationHistoryView.as_view(), name='task_conversation_history'),
    path('task-description/', GenerateTaskDescriptionView.as_view(), name='generate_task_description'),
    path('create-subtasks/', CreateSubtasksFromAIView.as_view(), name='create_subtasks_from_ai'),

    # Template-based task generation (Week 3 Day 15: Integration)
    path('generate-atomic-tasks/', GenerateAtomicTasksView.as_view(), name='generate_atomic_tasks'),

    # Voice interface (Phase 4.2)
    path('voice/process/', process_voice_command, name='voice_process'),
    path('voice/query/', voice_query, name='voice_query'),
    path('voice/capabilities/', voice_capabilities, name='voice_capabilities'),
]
