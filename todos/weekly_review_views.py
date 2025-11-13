from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from datetime import date, datetime, timedelta
from .weekly_review import WeeklyReview


class WeeklyReviewViewSet(viewsets.ViewSet):
    """
    ViewSet for Weekly Review operations
    """
    permission_classes = [IsAuthenticated]

    def list(self, request):
        """
        Get weekly review for a specific week
        GET /api/weekly-review/?week_start=2025-10-13
        """
        week_start_str = request.query_params.get('week_start')

        # Parse week start or calculate last Monday
        if week_start_str:
            try:
                week_start = datetime.strptime(week_start_str, '%Y-%m-%d').date()
            except ValueError:
                return Response(
                    {'error': 'Invalid date format. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            # Get last Monday
            today = date.today()
            days_since_monday = today.weekday()
            week_start = today - timedelta(days=days_since_monday)

        # Generate review
        reviewer = WeeklyReview(user=request.user)
        review_data = reviewer.generate_review(week_start=week_start)

        return Response(review_data)

    @action(detail=False, methods=['post'])
    def generate(self, request):
        """
        Generate weekly review (same as list, but with POST for clarity)
        POST /api/weekly-review/generate/
        Body: { "week_start": "2025-10-13" }  # Optional
        """
        week_start_str = request.data.get('week_start')

        if week_start_str:
            try:
                week_start = datetime.strptime(week_start_str, '%Y-%m-%d').date()
            except ValueError:
                return Response(
                    {'error': 'Invalid date format. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            # Get last Monday
            today = date.today()
            days_since_monday = today.weekday()
            week_start = today - timedelta(days=days_since_monday)

        # Generate review
        reviewer = WeeklyReview(user=request.user)
        review_data = reviewer.generate_review(week_start=week_start)

        return Response(review_data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def formatted(self, request):
        """
        Get formatted weekly review as markdown
        GET /api/weekly-review/formatted/?week_start=2025-10-13
        """
        week_start_str = request.query_params.get('week_start')

        if week_start_str:
            try:
                week_start = datetime.strptime(week_start_str, '%Y-%m-%d').date()
            except ValueError:
                return Response(
                    {'error': 'Invalid date format. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            # Get last Monday
            today = date.today()
            days_since_monday = today.weekday()
            week_start = today - timedelta(days=days_since_monday)

        # Generate formatted review
        reviewer = WeeklyReview(user=request.user)
        formatted_review = reviewer.generate_formatted_review(week_start=week_start)

        return Response({
            'week_start': week_start.isoformat(),
            'markdown': formatted_review
        })

    @action(detail=False, methods=['get'])
    def stats_only(self, request):
        """
        Get just the statistics without wins/blockers/streaks
        GET /api/weekly-review/stats-only/?week_start=2025-10-13
        """
        week_start_str = request.query_params.get('week_start')

        if week_start_str:
            try:
                week_start = datetime.strptime(week_start_str, '%Y-%m-%d').date()
            except ValueError:
                return Response(
                    {'error': 'Invalid date format. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            today = date.today()
            days_since_monday = today.weekday()
            week_start = today - timedelta(days=days_since_monday)

        # Get week range
        week_end = week_start + timedelta(days=6)

        # Get week tasks
        from .models import Todo
        week_tasks = Todo.objects.filter(
            user=request.user,
            scheduled_date__gte=week_start,
            scheduled_date__lte=week_end
        )

        # Calculate stats and streaks
        reviewer = WeeklyReview(user=request.user)
        stats = reviewer._calculate_stats(week_tasks)
        streaks = reviewer._calculate_streaks(week_start, week_end)

        return Response({
            'week_start': week_start.isoformat(),
            'week_end': week_end.isoformat(),
            'stats': stats,
            'streaks': streaks
        })
