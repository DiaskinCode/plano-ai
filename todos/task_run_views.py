from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .artifact_models import TaskRun, TaskArtifact
from .models import Todo
from .serializers import TaskRunSerializer, TaskArtifactSerializer


class TaskRunViewSet(viewsets.ModelViewSet):
    """
    ViewSet for TaskRun (Let's Go sessions) CRUD operations
    """
    permission_classes = [IsAuthenticated]
    serializer_class = TaskRunSerializer

    def get_queryset(self):
        """Return runs for the current user's tasks"""
        task_ids = Todo.objects.filter(user=self.request.user).values_list('id', flat=True)
        queryset = TaskRun.objects.filter(task_id__in=task_ids)

        # Filter by task_id if provided
        task_id = self.request.query_params.get('task_id')
        if task_id:
            queryset = queryset.filter(task_id=task_id)

        return queryset.order_by('-started_at')

    def create(self, request, *args, **kwargs):
        """
        Create new Let's Go session
        POST /api/task-runs/
        Body: {
            "task_id": 123,
            "user_inputs": [],  # Optional, can be empty at start
            "ai_responses": []  # Optional, can be empty at start
        }
        """
        task_id = request.data.get('task')

        # Verify task exists and belongs to user
        try:
            task = Todo.objects.get(id=task_id, user=request.user)
        except Todo.DoesNotExist:
            return Response(
                {'error': 'Task not found or does not belong to you'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Only allow copilot tasks to have runs
        if task.task_type != 'copilot':
            return Response(
                {'error': 'Only copilot tasks can have Let\'s Go sessions'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        task_run = serializer.save()

        return Response(
            TaskRunSerializer(task_run).data,
            status=status.HTTP_201_CREATED
        )

    def update(self, request, *args, **kwargs):
        """
        Update existing session (add messages, mark completed, etc.)
        PATCH /api/task-runs/{id}/
        Body: {
            "user_inputs": [...],  # Append to existing
            "ai_responses": [...],  # Append to existing
            "completed": true,
            "duration_seconds": 300
        }
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        # If appending messages, merge with existing
        if 'user_inputs' in request.data:
            existing_inputs = instance.user_inputs or []
            new_inputs = request.data.get('user_inputs', [])
            request.data['user_inputs'] = existing_inputs + new_inputs

        if 'ai_responses' in request.data:
            existing_responses = instance.ai_responses or []
            new_responses = request.data.get('ai_responses', [])
            request.data['ai_responses'] = existing_responses + new_responses

        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        task_run = serializer.save()

        return Response(TaskRunSerializer(task_run).data)

    @action(detail=True, methods=['post'])
    def add_message(self, request, pk=None):
        """
        Add a single message exchange to the session
        POST /api/task-runs/{id}/add-message/
        Body: {
            "user_input": "My answer here",
            "ai_response": "AI's response here"
        }
        """
        task_run = self.get_object()

        user_input = request.data.get('user_input')
        ai_response = request.data.get('ai_response')

        if not user_input and not ai_response:
            return Response(
                {'error': 'Either user_input or ai_response is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Append to arrays
        if user_input:
            task_run.user_inputs.append(user_input)

        if ai_response:
            task_run.ai_responses.append(ai_response)

        task_run.interactions_count = max(
            len(task_run.user_inputs),
            len(task_run.ai_responses)
        )
        task_run.save()

        return Response(TaskRunSerializer(task_run).data)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """
        Mark session as completed and optionally attach artifact
        POST /api/task-runs/{id}/complete/
        Body: {
            "duration_seconds": 450,
            "artifact_id": 123  # Optional
        }
        """
        task_run = self.get_object()

        if task_run.completed:
            return Response(
                {'error': 'Session is already completed'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Set duration
        duration_seconds = request.data.get('duration_seconds')
        if duration_seconds:
            task_run.duration_seconds = duration_seconds

        # Attach artifact if provided
        artifact_id = request.data.get('artifact_id')
        if artifact_id:
            try:
                artifact = TaskArtifact.objects.get(id=artifact_id, task=task_run.task)
                task_run.final_artifact = artifact
            except TaskArtifact.DoesNotExist:
                return Response(
                    {'error': 'Artifact not found or does not belong to this task'},
                    status=status.HTTP_404_NOT_FOUND
                )

        # Mark completed
        task_run.completed = True
        task_run.save()

        return Response({
            'message': 'Session marked as completed',
            'task_run': TaskRunSerializer(task_run).data
        })

    @action(detail=False, methods=['get'])
    def by_task(self, request):
        """
        Get all runs for a specific task
        GET /api/task-runs/by-task/?task_id=123
        """
        task_id = request.query_params.get('task_id')

        if not task_id:
            return Response(
                {'error': 'task_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verify task belongs to user
        try:
            task = Todo.objects.get(id=task_id, user=request.user)
        except Todo.DoesNotExist:
            return Response(
                {'error': 'Task not found or does not belong to you'},
                status=status.HTTP_404_NOT_FOUND
            )

        runs = TaskRun.objects.filter(task_id=task_id).order_by('-started_at')
        serializer = TaskRunSerializer(runs, many=True)

        return Response({
            'task_id': task_id,
            'task_title': task.title,
            'total_runs': runs.count(),
            'completed_runs': runs.filter(completed=True).count(),
            'runs': serializer.data
        })

    @action(detail=False, methods=['get'])
    def recent(self, request):
        """
        Get recent Let's Go sessions across all tasks
        GET /api/task-runs/recent/?limit=10
        """
        limit = int(request.query_params.get('limit', 10))

        task_ids = Todo.objects.filter(user=request.user).values_list('id', flat=True)
        runs = TaskRun.objects.filter(task_id__in=task_ids).order_by('-started_at')[:limit]

        serializer = TaskRunSerializer(runs, many=True)

        return Response({
            'limit': limit,
            'count': runs.count(),
            'runs': serializer.data
        })

    @action(detail=True, methods=['get'])
    def transcript(self, request, pk=None):
        """
        Get formatted conversation transcript
        GET /api/task-runs/{id}/transcript/
        """
        task_run = self.get_object()

        # Build transcript with alternating user/AI messages
        transcript = []
        max_length = max(
            len(task_run.user_inputs or []),
            len(task_run.ai_responses or [])
        )

        for i in range(max_length):
            if i < len(task_run.user_inputs or []):
                transcript.append({
                    'role': 'user',
                    'message': task_run.user_inputs[i],
                    'index': i
                })

            if i < len(task_run.ai_responses or []):
                transcript.append({
                    'role': 'ai',
                    'message': task_run.ai_responses[i],
                    'index': i
                })

        return Response({
            'task_run_id': task_run.id,
            'task_title': task_run.task.title,
            'started_at': task_run.started_at,
            'completed': task_run.completed,
            'duration_seconds': task_run.duration_seconds,
            'interactions_count': task_run.interactions_count,
            'transcript': transcript
        })
