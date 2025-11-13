from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from datetime import timedelta
from celery.result import AsyncResult

from .models import Todo
from .serializers import TodoSerializer, TodoCreateSerializer, TodoListSerializer
from .task_generator import TaskGenerator
from .simple_task_generator import generate_simple_tasks


class TodoViewSet(viewsets.ModelViewSet):
    """CRUD operations for todos"""
    permission_classes = (permissions.IsAuthenticated,)

    def get_serializer_class(self):
        if self.action == 'create':
            return TodoCreateSerializer
        elif self.action == 'list':
            return TodoListSerializer
        return TodoSerializer

    def get_queryset(self):
        queryset = Todo.objects.filter(user=self.request.user)

        # Filter by date
        filter_type = self.request.query_params.get('filter', None)
        today = timezone.now().date()

        if filter_type == 'today':
            queryset = queryset.filter(scheduled_date=today)
        elif filter_type == 'tomorrow':
            tomorrow = today + timedelta(days=1)
            queryset = queryset.filter(scheduled_date=tomorrow)
        elif filter_type == 'overdue':
            queryset = queryset.filter(scheduled_date__lt=today, status='pending')
        elif filter_type == 'upcoming':
            queryset = queryset.filter(scheduled_date__gte=today, status='pending')

        # Filter by status
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        return queryset.order_by('scheduled_date', '-priority', 'created_at')

    @action(detail=True, methods=['post'])
    def mark_done(self, request, pk=None):
        """Mark todo as done"""
        todo = self.get_object()
        todo.status = 'done'
        todo.completed_at = timezone.now()
        todo.save()
        return Response(TodoSerializer(todo).data)

    @action(detail=True, methods=['post'])
    def skip(self, request, pk=None):
        """Skip todo with reason"""
        todo = self.get_object()
        todo.status = 'skipped'
        todo.skipped_at = timezone.now()
        todo.skip_reason = request.data.get('reason', '')
        todo.save()
        return Response(TodoSerializer(todo).data)

    @action(detail=True, methods=['post'])
    def reschedule(self, request, pk=None):
        """Reschedule todo"""
        todo = self.get_object()
        todo.scheduled_date = request.data.get('new_date', todo.scheduled_date)
        todo.scheduled_time = request.data.get('new_time', todo.scheduled_time)
        todo.status = 'rescheduled'
        todo.save()
        return Response(TodoSerializer(todo).data)


class GenerateTasksView(APIView):
    """Generate tasks for current month from vision"""
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        # Import here to avoid circular import
        from .tasks import generate_monthly_tasks_task

        # Start background task
        task = generate_monthly_tasks_task.delay(request.user.id)

        return Response({
            'message': 'Task generation started',
            'task_id': task.id,
            'status': 'pending',
            'status_url': f'/api/todos/task-status/{task.id}/'
        })


class TaskStatusView(APIView):
    """Check status of background task generation"""
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, task_id):
        task_result = AsyncResult(task_id)

        response_data = {
            'task_id': task_id,
            'state': task_result.state,
        }

        if task_result.state == 'PENDING':
            response_data['status'] = 'pending'
            response_data['message'] = 'Task is waiting to start'
        elif task_result.state == 'PROGRESS':
            response_data['status'] = 'in_progress'
            response_data['progress'] = task_result.info
        elif task_result.state == 'SUCCESS':
            response_data['status'] = 'completed'
            response_data['result'] = task_result.result
        elif task_result.state == 'FAILURE':
            response_data['status'] = 'failed'
            response_data['error'] = str(task_result.info)
        else:
            response_data['status'] = task_result.state.lower()

        return Response(response_data)
