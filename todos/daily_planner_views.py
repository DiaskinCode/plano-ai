from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from datetime import date, datetime
from .daily_planner import DailyPlanner
from .models import Todo
from .serializers import AtomicTaskSerializer


class DailyPlannerViewSet(viewsets.ViewSet):
    """
    ViewSet for Daily Planner operations
    """
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'])
    def generate(self, request):
        """
        Generate daily plan for a specific date
        POST /api/daily-planner/generate/
        Body: { "target_date": "2025-10-15" }  # Optional, defaults to today
        """
        target_date_str = request.data.get('target_date')

        # Parse target date or use today
        if target_date_str:
            try:
                target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
            except ValueError:
                return Response(
                    {'error': 'Invalid date format. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            target_date = date.today()

        # Generate daily plan
        planner = DailyPlanner(user=request.user)
        plan = planner.generate_daily_plan(target_date=target_date)

        # Create tasks from plan
        created_tasks = planner.create_tasks_from_plan(plan)

        return Response({
            'message': f'Generated {len(created_tasks)} tasks for {target_date}',
            'target_date': target_date.isoformat(),
            'tasks_created': len(created_tasks),
            'tasks': AtomicTaskSerializer(created_tasks, many=True).data
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def preview(self, request):
        """
        Preview daily plan without creating tasks
        GET /api/daily-planner/preview/?target_date=2025-10-15
        """
        target_date_str = request.query_params.get('target_date')

        if target_date_str:
            try:
                target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
            except ValueError:
                return Response(
                    {'error': 'Invalid date format. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            target_date = date.today()

        # Generate plan without creating tasks
        planner = DailyPlanner(user=request.user)
        plan = planner.generate_daily_plan(target_date=target_date)

        return Response({
            'target_date': target_date.isoformat(),
            'total_tasks': len(plan),
            'total_minutes': sum(task['timebox_minutes'] for task in plan),
            'plan': plan
        })

    @action(detail=False, methods=['get'])
    def allocation(self, request):
        """
        Get time allocation breakdown by goals
        GET /api/daily-planner/allocation/
        """
        planner = DailyPlanner(user=request.user)

        # Get active goals
        from users.goalspec_models import GoalSpec
        active_goals = GoalSpec.objects.filter(user=request.user, is_active=True)

        # Calculate allocations
        total_daily_minutes = planner._get_total_daily_minutes()
        goal_allocations = planner._allocate_time_by_goals(active_goals, total_daily_minutes)

        allocation_data = []
        for goal, allocated_minutes in goal_allocations:
            allocation_data.append({
                'goal_id': goal.id,
                'goal_title': goal.title,
                'goal_type': goal.goal_type,
                'priority_weight': goal.priority_weight,
                'allocated_minutes': allocated_minutes,
                'percentage': round((allocated_minutes / total_daily_minutes) * 100, 1) if total_daily_minutes > 0 else 0
            })

        return Response({
            'total_daily_minutes': total_daily_minutes,
            'allocations': allocation_data
        })
