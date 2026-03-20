from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .artifact_models import TaskEvidence
from .models import Todo
from .serializers import TaskEvidenceSerializer


class TaskEvidenceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for TaskEvidence CRUD operations
    """
    permission_classes = [IsAuthenticated]
    serializer_class = TaskEvidenceSerializer

    def get_queryset(self):
        """Return evidence for the current user's tasks"""
        task_ids = Todo.objects.filter(user=self.request.user).values_list('id', flat=True)
        queryset = TaskEvidence.objects.filter(task_id__in=task_ids)

        # Filter by task_id if provided
        task_id = self.request.query_params.get('task_id')
        if task_id:
            queryset = queryset.filter(task_id=task_id)

        return queryset.order_by('-uploaded_at')

    def create(self, request, *args, **kwargs):
        """
        Create new evidence
        POST /api/task-evidence/
        Body: {
            "task": 123,  # Task ID
            "evidence_type": "note|link|photo|screenshot|file",
            "note": "...",  # For note type
            "url": "...",   # For link type
            "file": <file>  # For photo/screenshot/file types
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

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        evidence = serializer.save(uploaded_by=request.user)

        # Update task progress after evidence upload
        task.update_progress()

        return Response(
            TaskEvidenceSerializer(evidence).data,
            status=status.HTTP_201_CREATED
        )

    def destroy(self, request, *args, **kwargs):
        """Delete evidence and recalculate task progress"""
        instance = self.get_object()
        task = instance.task

        # Delete evidence
        self.perform_destroy(instance)

        # Recalculate task progress
        task.update_progress()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'])
    def by_task(self, request):
        """
        Get all evidence for a specific task
        GET /api/task-evidence/by-task/?task_id=123
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

        evidence = TaskEvidence.objects.filter(task_id=task_id).order_by('-uploaded_at')
        serializer = TaskEvidenceSerializer(evidence, many=True)

        return Response({
            'task_id': task_id,
            'task_title': task.title,
            'evidence_count': evidence.count(),
            'evidence': serializer.data
        })

    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """
        Get all evidence of a specific type for user's tasks
        GET /api/task-evidence/by-type/?evidence_type=photo
        """
        evidence_type = request.query_params.get('evidence_type')

        if not evidence_type:
            return Response(
                {'error': 'evidence_type parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Valid evidence types
        valid_types = ['note', 'link', 'photo', 'screenshot', 'file']
        if evidence_type not in valid_types:
            return Response(
                {'error': f'Invalid evidence_type. Must be one of: {", ".join(valid_types)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        task_ids = Todo.objects.filter(user=request.user).values_list('id', flat=True)
        evidence = TaskEvidence.objects.filter(
            task_id__in=task_ids,
            evidence_type=evidence_type
        ).order_by('-uploaded_at')

        serializer = TaskEvidenceSerializer(evidence, many=True)

        return Response({
            'evidence_type': evidence_type,
            'count': evidence.count(),
            'evidence': serializer.data
        })

    @action(detail=True, methods=['patch'])
    def update_note(self, request, pk=None):
        """
        Update note text for note-type evidence
        PATCH /api/task-evidence/{id}/update-note/
        Body: { "note": "Updated note text" }
        """
        evidence = self.get_object()

        if evidence.evidence_type != 'note':
            return Response(
                {'error': 'This endpoint is only for note-type evidence'},
                status=status.HTTP_400_BAD_REQUEST
            )

        note_text = request.data.get('note')
        if not note_text:
            return Response(
                {'error': 'note field is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        evidence.note = note_text
        evidence.save()

        return Response(TaskEvidenceSerializer(evidence).data)
