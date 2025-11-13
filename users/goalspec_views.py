from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .goalspec_models import GoalSpec
from .goalspec_serializers import (
    GoalSpecSerializer,
    GoalSpecCreateSerializer,
    GoalSpecListSerializer
)


class GoalSpecViewSet(viewsets.ModelViewSet):
    """
    ViewSet for GoalSpec CRUD operations
    """
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return GoalSpecCreateSerializer
        elif self.action == 'list':
            return GoalSpecListSerializer
        return GoalSpecSerializer

    def get_queryset(self):
        """Return goals for the current user"""
        return GoalSpec.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        """Create a new goal spec"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Validate constraints based on goal type
        goal = serializer.save()

        return Response(
            GoalSpecSerializer(goal).data,
            status=status.HTTP_201_CREATED
        )

    def update(self, request, *args, **kwargs):
        """Update a goal spec"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark a goal as completed"""
        goal = self.get_object()
        goal.completed = True
        goal.is_active = False
        goal.save()

        return Response({
            'message': 'Goal marked as completed',
            'goal': GoalSpecSerializer(goal).data
        })

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a goal"""
        goal = self.get_object()
        goal.is_active = True
        goal.completed = False
        goal.save()

        return Response({
            'message': 'Goal activated',
            'goal': GoalSpecSerializer(goal).data
        })

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate a goal without marking it completed"""
        goal = self.get_object()
        goal.is_active = False
        goal.save()

        return Response({
            'message': 'Goal deactivated',
            'goal': GoalSpecSerializer(goal).data
        })

    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get all active goals"""
        active_goals = self.get_queryset().filter(is_active=True, completed=False)
        serializer = GoalSpecSerializer(active_goals, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def validate_constraints(self, request, pk=None):
        """Validate goal constraints"""
        goal = self.get_object()
        is_valid, message = goal.validate_constraints()

        return Response({
            'valid': is_valid,
            'message': message
        })

    @action(detail=False, methods=['get'])
    def with_statistics(self, request):
        """
        Get all active goals with task statistics
        Returns goals grouped by category with progress data
        """
        from todos.models import Todo
        from django.db.models import Count, Q

        active_goals = self.get_queryset().filter(is_active=True, completed=False)

        # Build response with statistics
        goals_data = []
        for goal in active_goals:
            # Get task counts for this goal
            total_tasks = Todo.objects.filter(
                user=request.user,
                goalspec=goal
            ).count()

            completed_tasks = Todo.objects.filter(
                user=request.user,
                goalspec=goal,
                status='done'
            ).count()

            # Calculate progress percentage
            progress = 0
            if total_tasks > 0:
                progress = round((completed_tasks / total_tasks) * 100)

            # Determine status based on progress
            if progress >= 70:
                status = 'on_track'
            elif progress >= 30:
                status = 'at_risk'
            else:
                status = 'stalled'

            goals_data.append({
                'id': goal.id,
                'category': goal.category,
                'title': goal.title,
                'description': goal.description,
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks,
                'progress': progress,
                'status': status,
                'priority_weight': goal.priority_weight,
                'target_date': goal.target_date,
            })

        # Group by category
        grouped = {}
        for goal in goals_data:
            category = goal['category']
            if category not in grouped:
                grouped[category] = []
            grouped[category].append(goal)

        return Response({
            'goals': goals_data,
            'grouped': grouped,
            'total_goals': len(goals_data)
        })

    @action(detail=False, methods=['get'])
    def with_milestones(self, request):
        """
        Get all active goals with their milestones and tasks grouped hierarchically.

        Returns structure:
        {
            "goals": [
                {
                    "id": 1,
                    "title": "Get into MIT CS Master's",
                    "description": "...",
                    "category": "study",
                    "progress": 45,
                    "milestones": [
                        {
                            "title": "Research and shortlist programs",
                            "index": 1,
                            "total_tasks": 6,
                            "completed_tasks": 3,
                            "progress": 50,
                            "tasks": [
                                {
                                    "id": 123,
                                    "title": "Visit MIT EECS website...",
                                    "status": "done",
                                    "timebox_minutes": 30,
                                    ...
                                },
                                ...
                            ]
                        },
                        ...
                    ]
                },
                ...
            ]
        }
        """
        from todos.models import Todo
        from todos.serializers import TodoSerializer
        from collections import defaultdict

        active_goals = self.get_queryset().filter(is_active=True, completed=False)

        goals_data = []
        for goal in active_goals:
            # Get all tasks for this goal
            tasks = Todo.objects.filter(
                user=request.user,
                goalspec=goal
            ).order_by('scheduled_date', 'created_at')

            # Group tasks by milestone
            milestones_map = defaultdict(list)
            tasks_without_milestone = []

            for task in tasks:
                # Get milestone metadata from notes field
                milestone_title = None
                milestone_index = None

                if isinstance(task.notes, dict):
                    milestone_title = task.notes.get('milestone_title')
                    milestone_index = task.notes.get('milestone_index')

                # If milestone metadata exists, group by it
                if milestone_title is not None and milestone_index is not None:
                    milestone_key = (milestone_index, milestone_title)
                    milestones_map[milestone_key].append(task)
                else:
                    # Tasks without milestone metadata
                    tasks_without_milestone.append(task)

            # Build milestones array
            milestones = []
            for (index, title), milestone_tasks in sorted(milestones_map.items()):
                total_tasks = len(milestone_tasks)
                completed_tasks = sum(1 for t in milestone_tasks if t.status == 'done')
                milestone_progress = round((completed_tasks / total_tasks) * 100) if total_tasks > 0 else 0

                milestones.append({
                    'title': title,
                    'index': index,
                    'total_tasks': total_tasks,
                    'completed_tasks': completed_tasks,
                    'progress': milestone_progress,
                    'tasks': TodoSerializer(milestone_tasks, many=True).data
                })

            # Add tasks without milestone as a separate group if any exist
            if tasks_without_milestone:
                total_tasks_no_milestone = len(tasks_without_milestone)
                completed_tasks_no_milestone = sum(1 for t in tasks_without_milestone if t.status == 'done')
                milestone_progress_no_milestone = round((completed_tasks_no_milestone / total_tasks_no_milestone) * 100) if total_tasks_no_milestone > 0 else 0

                milestones.append({
                    'title': 'Other Tasks',
                    'index': 999,  # Put at the end
                    'total_tasks': total_tasks_no_milestone,
                    'completed_tasks': completed_tasks_no_milestone,
                    'progress': milestone_progress_no_milestone,
                    'tasks': TodoSerializer(tasks_without_milestone, many=True).data
                })

            # Calculate overall goal progress
            total_tasks = tasks.count()
            completed_tasks = tasks.filter(status='done').count()
            goal_progress = round((completed_tasks / total_tasks) * 100) if total_tasks > 0 else 0

            goals_data.append({
                'id': goal.id,
                'title': goal.title,
                'description': goal.description,
                'category': goal.category,
                'target_date': goal.target_date,
                'priority_weight': goal.priority_weight,
                'progress': goal_progress,
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks,
                'milestones': milestones
            })

        return Response({
            'goals': goals_data,
            'total_goals': len(goals_data)
        })
