from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django.db.models import Sum, Count, Q
from django.core.cache import cache
from datetime import timedelta, datetime
from .models import Vision, Milestone
from .serializers import VisionSerializer, MilestoneSerializer
from todos.models import Todo
from todos.serializers import TodoListSerializer
from ai.services import ai_service


class VisionListView(APIView):
    """Get user's active vision (from GoalSpecs)"""
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        # NEW: Get primary GoalSpec instead of Vision
        from users.models import GoalSpec

        primary_goalspec = GoalSpec.objects.filter(
            user=request.user,
            status='active'
        ).order_by('-priority_weight', '-created_at').first()

        if not primary_goalspec:
            # Try old Vision model for backward compatibility
            vision = Vision.objects.filter(user=request.user).order_by('-created_at').first()
            if not vision:
                return Response(
                    {'error': 'No vision found. Complete onboarding to generate your vision.'},
                    status=status.HTTP_404_NOT_FOUND
                )
            return Response(VisionSerializer(vision).data)

        # Generate vision from GoalSpec
        category_map = {
            'study': 'academic excellence',
            'career': 'professional success',
            'sport': 'fitness achievement',
            'finance': 'financial freedom',
            'language': 'language mastery',
            'health': 'optimal health',
            'creative': 'creative expression',
            'admin': 'organized life',
            'research': 'research breakthrough',
            'networking': 'meaningful connections',
            'travel': 'world exploration',
            'other': 'personal growth',
        }

        category_vision = category_map.get(primary_goalspec.category, 'your goal')

        if primary_goalspec.target_date:
            days_remaining = (primary_goalspec.target_date - timezone.now().date()).days
            if days_remaining > 0:
                vision_text = f"{primary_goalspec.title} - {days_remaining} days to {category_vision}"
            else:
                vision_text = f"{primary_goalspec.title} - Achieving {category_vision} now"
        else:
            vision_text = f"{primary_goalspec.title} - Your path to {category_vision}"

        return Response({
            'vision': vision_text,
            'goalspec_id': primary_goalspec.id,
            'category': primary_goalspec.category,
            'title': primary_goalspec.title,
        })


class VisionDetailView(APIView):
    """Get, update, or delete a specific vision"""
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, pk):
        try:
            vision = Vision.objects.get(pk=pk, user=request.user)
            return Response(VisionSerializer(vision).data)
        except Vision.DoesNotExist:
            return Response({'error': 'Vision not found'}, status=status.HTTP_404_NOT_FOUND)

    def patch(self, request, pk):
        try:
            vision = Vision.objects.get(pk=pk, user=request.user)
            serializer = VisionSerializer(vision, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Vision.DoesNotExist:
            return Response({'error': 'Vision not found'}, status=status.HTTP_404_NOT_FOUND)


class MilestoneListView(APIView):
    """Get milestones for a vision"""
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, vision_id):
        milestones = Milestone.objects.filter(
            vision_id=vision_id,
            vision__user=request.user
        ).order_by('month_offset')

        return Response(MilestoneSerializer(milestones, many=True).data)


class MilestoneUpdateView(APIView):
    """Update a milestone (e.g., mark as completed)"""
    permission_classes = (permissions.IsAuthenticated,)

    def patch(self, request, pk):
        try:
            milestone = Milestone.objects.get(pk=pk, vision__user=request.user)
            serializer = MilestoneSerializer(milestone, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Milestone.DoesNotExist:
            return Response({'error': 'Milestone not found'}, status=status.HTTP_404_NOT_FOUND)


class VisionAnalyticsView(APIView):
    """Get vision with calculated analytics for the new UI"""
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        vision = Vision.objects.filter(user=request.user, is_active=True).first()

        if not vision:
            return Response({
                'error': 'No active vision found'
            }, status=status.HTTP_404_NOT_FOUND)

        today = timezone.now().date()

        # Calculate 12-month roadmap structure
        vision_start = vision.horizon_start
        vision_end = vision.horizon_end
        total_days = (vision_end - vision_start).days
        month_interval = total_days / 12 if total_days >= 360 else 30

        # Get existing milestones from DB
        db_milestones = list(Milestone.objects.filter(vision=vision).order_by('due_date'))

        # Generate 12 monthly milestones + weekly sub-milestones
        milestone_data = []

        for month_index in range(12):
            # Calculate this month's date range
            month_start = vision_start + timedelta(days=int(month_interval * month_index))
            month_due = vision_start + timedelta(days=int(month_interval * (month_index + 1)))

            # Use DB milestone sequentially (if available for this month index)
            closest_milestone = None
            if month_index < len(db_milestones):
                closest_milestone = db_milestones[month_index]

            # Get stats from milestone or use defaults
            if closest_milestone:
                tasks = Todo.objects.filter(milestone=closest_milestone, user=request.user)
                completed_tasks = tasks.filter(status='done')
                percent = closest_milestone.percent if hasattr(closest_milestone, 'percent') else 0
                focus_min = completed_tasks.aggregate(total=Sum('estimated_duration_minutes'))['total'] or 0

                # Calculate critical tasks (priority 3)
                critical_tasks = tasks.filter(priority=3)
                critical_done = critical_tasks.filter(status='done').count()
                critical_total = critical_tasks.count()

                # Fallback: if no tasks linked to milestone, use tasks in date range
                if focus_min == 0 and critical_total == 0:
                    date_range_tasks = Todo.objects.filter(
                        user=request.user,
                        scheduled_date__gte=month_start,
                        scheduled_date__lte=month_due
                    )
                    completed_in_range = date_range_tasks.filter(status='done')
                    focus_min = completed_in_range.aggregate(total=Sum('estimated_duration_minutes'))['total'] or 0

                    critical_in_range = date_range_tasks.filter(priority=3)
                    critical_done = critical_in_range.filter(status='done').count()
                    critical_total = critical_in_range.count()

                month_name = closest_milestone.title
                month_state = closest_milestone.state
                month_proofs = closest_milestone.proofs
                month_risks = closest_milestone.risk_flags
            else:
                # No milestone exists, calculate from date range
                date_range_tasks = Todo.objects.filter(
                    user=request.user,
                    scheduled_date__gte=month_start,
                    scheduled_date__lte=month_due
                )
                completed_in_range = date_range_tasks.filter(status='done')
                focus_min = completed_in_range.aggregate(total=Sum('estimated_duration_minutes'))['total'] or 0

                critical_in_range = date_range_tasks.filter(priority=3)
                critical_done = critical_in_range.filter(status='done').count()
                critical_total = critical_in_range.count()

                percent = 0
                month_name = f"Month {month_index + 1}"
                month_state = 'later'
                month_proofs = []
                month_risks = []

            # Determine month state based on date
            if month_due < today:
                month_state = 'done' if percent >= 80 else 'at_risk'
            elif month_start <= today <= month_due:
                month_state = 'in_progress'
            elif month_start <= today + timedelta(days=30):
                month_state = 'next'

            # Generate 4 weekly sub-milestones for this month
            week_interval = month_interval / 4

            # Get task count for this month
            if closest_milestone:
                month_tasks = Todo.objects.filter(milestone=closest_milestone, user=request.user)
                total_tasks = month_tasks.count()
                tasks_per_week = max(1, total_tasks // 4)  # Distribute across 4 weeks
            else:
                tasks_per_week = 0

            for week in range(4):
                week_due = month_start + timedelta(days=int(week_interval * (week + 1)))
                week_percent = int((week + 1) * 25 * (percent / 100))

                # Determine state for weekly milestone
                if week_due < today:
                    week_state = 'done' if week_percent >= 20 else 'at_risk'
                elif week_due <= today + timedelta(days=7):
                    week_state = 'in_progress'
                else:
                    week_state = 'later'

                milestone_data.append({
                    'id': f"m{month_index + 1}_w{week + 1}",
                    'name': f"Week {week + 1}",
                    'state': week_state,
                    'due': week_due.isoformat(),
                    'percent': week_percent,
                    'buffer_days': 0,
                    'risk_flags': [],
                    'proofs': [],
                    'next_tasks': [],
                    'stats': {
                        'focus_min': focus_min // 4,
                        'critical_done': critical_done // 4 if critical_total > 0 else 0,
                        'critical_total': critical_total // 4 if critical_total > 0 else 0
                    },
                    'is_weekly': True,
                    'parent_milestone_id': month_index + 1,
                    'task_count': tasks_per_week
                })

            # Get all tasks for this milestone (for progress calculation)
            # First try tasks linked to milestone, then fallback to date range
            if closest_milestone:
                all_tasks = Todo.objects.filter(
                    milestone=closest_milestone,
                    user=request.user
                ).order_by('-priority', 'scheduled_date')

                # Fallback: if no tasks linked to milestone, use date range
                if all_tasks.count() == 0:
                    all_tasks = Todo.objects.filter(
                        user=request.user,
                        scheduled_date__gte=month_start,
                        scheduled_date__lte=month_due
                    ).order_by('-priority', 'scheduled_date')

                next_tasks_data = TodoListSerializer(all_tasks, many=True).data
                total_tasks = all_tasks.count()
            else:
                # No milestone exists, try date range
                all_tasks = Todo.objects.filter(
                    user=request.user,
                    scheduled_date__gte=month_start,
                    scheduled_date__lte=month_due
                ).order_by('-priority', 'scheduled_date')
                next_tasks_data = TodoListSerializer(all_tasks, many=True).data
                total_tasks = all_tasks.count()

            # Add the monthly milestone
            milestone_data.append({
                'id': f"m{month_index + 1}",
                'name': month_name,
                'state': month_state,
                'due': month_due.isoformat(),
                'percent': percent,
                'buffer_days': 0,
                'risk_flags': month_risks,
                'proofs': month_proofs,
                'next_tasks': next_tasks_data,
                'stats': {
                    'focus_min': focus_min,
                    'critical_done': critical_done,
                    'critical_total': critical_total
                },
                'is_monthly': True,
                'task_count': total_tasks
            })

        # Add final achievement island
        milestone_data.append({
            'id': 'final',
            'name': vision.title,
            'state': 'later',
            'due': vision_end.isoformat(),
            'percent': vision.progress_percentage,
            'buffer_days': 0,
            'risk_flags': [],
            'proofs': [],
            'next_tasks': [],
            'stats': {
                'focus_min': 0,
                'critical_done': 0,
                'critical_total': 0
            },
            'is_monthly': True,
            'is_final': True
        })

        # Calculate overall confidence
        completed_count = sum(1 for m in milestone_data if m.get('state') == 'done' and m.get('is_monthly'))
        total_monthly = sum(1 for m in milestone_data if m.get('is_monthly'))

        if total_monthly > 0:
            on_time_rate = (completed_count / total_monthly * 100)
        else:
            on_time_rate = 50

        total_risks = sum(len(m.get('risk_flags', [])) for m in milestone_data if m.get('is_monthly'))

        confidence = max(0, min(100, 50 + 0.4 * (on_time_rate - 50) - 0.2 * total_risks * 10))

        # Calculate week effort
        week_start = today - timedelta(days=today.weekday())
        week_todos = Todo.objects.filter(
            user=request.user,
            scheduled_date__range=[week_start, today],
            status='done'
        )
        week_focus_min = week_todos.aggregate(total=Sum('estimated_duration_minutes'))['total'] or 0

        # Protected minutes (high priority tasks)
        protected_min = week_todos.filter(priority=3).aggregate(
            total=Sum('estimated_duration_minutes')
        )['total'] or 0

        # Calculate "at this pace" ETA
        days_since_start = (today - vision.horizon_start).days
        if days_since_start > 0:
            progress_percent = vision.progress_percentage
            days_per_percent = days_since_start / max(progress_percent, 1)
            remaining_percent = 100 - progress_percent
            estimated_days_left = int(days_per_percent * remaining_percent)
            at_pace_eta = today + timedelta(days=estimated_days_left)
        else:
            at_pace_eta = vision.horizon_end

        # Get current/next milestone for action bar
        current_milestone_data = next((m for m in milestone_data if m.get('state') in ['in_progress', 'next']), None)
        action_cta = None
        if current_milestone_data:
            action_cta = f"Review {current_milestone_data['name']} progress"

        return Response({
            'vision_id': vision.id,
            'title': vision.title,
            'eta': vision.horizon_end.isoformat(),
            'confidence': round(confidence, 1),
            'milestones': milestone_data,
            'effort_summary': {
                'week_focus_min': week_focus_min,
                'protected_min': protected_min
            },
            'at_pace_eta': at_pace_eta.isoformat(),
            'action_cta': action_cta
        })


class MilestoneScheduleTasksView(APIView):
    """Schedule next tasks for a milestone"""
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, pk):
        try:
            milestone = Milestone.objects.get(pk=pk, vision__user=request.user)

            # Get next 2 pending tasks
            next_tasks = Todo.objects.filter(
                milestone=milestone,
                status='pending',
                user=request.user
            ).order_by('priority', 'scheduled_date')[:2]

            # Schedule for tomorrow at optimal time (e.g., 9:30 AM)
            tomorrow = timezone.now().date() + timedelta(days=1)
            scheduled_count = 0

            for task in next_tasks:
                task.scheduled_date = tomorrow
                task.scheduled_time = datetime.strptime('09:30', '%H:%M').time()
                task.save()
                scheduled_count += 1

            return Response({
                'message': f'Scheduled {scheduled_count} tasks for {tomorrow}',
                'tasks_scheduled': scheduled_count
            })

        except Milestone.DoesNotExist:
            return Response({'error': 'Milestone not found'}, status=status.HTTP_404_NOT_FOUND)


class MilestoneAddBufferView(APIView):
    """Add buffer days to a milestone"""
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, pk):
        try:
            milestone = Milestone.objects.get(pk=pk, vision__user=request.user)
            days = request.data.get('days', 7)

            milestone.buffer_days += days
            milestone.due_date += timedelta(days=days)
            milestone.save()

            return Response({
                'message': f'Added {days} buffer days',
                'new_due_date': milestone.due_date.isoformat(),
                'buffer_days': milestone.buffer_days
            })

        except Milestone.DoesNotExist:
            return Response({'error': 'Milestone not found'}, status=status.HTTP_404_NOT_FOUND)


class MilestoneMarkRiskView(APIView):
    """Toggle risk flag on a milestone"""
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, pk):
        try:
            milestone = Milestone.objects.get(pk=pk, vision__user=request.user)
            risk_note = request.data.get('note', 'General risk')

            # Add risk flag
            milestone.risk_flags.append({
                'note': risk_note,
                'added_at': timezone.now().isoformat()
            })
            milestone.state = 'at_risk'
            milestone.save()

            return Response({
                'message': 'Risk flag added',
                'risk_flags': milestone.risk_flags
            })

        except Milestone.DoesNotExist:
            return Response({'error': 'Milestone not found'}, status=status.HTTP_404_NOT_FOUND)


class DailyHeadlineView(APIView):
    """Generate daily motivational headline from user's GoalSpec"""
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        # NEW: Get primary GoalSpec instead of Vision
        from users.models import GoalSpec
        from todos.models import Todo

        primary_goalspec = GoalSpec.objects.filter(
            user=request.user,
            status='active'
        ).order_by('-priority_weight', '-created_at').first()

        if not primary_goalspec:
            # Try old Vision model for backward compatibility
            vision = Vision.objects.filter(user=request.user, is_active=True).first()
            if not vision:
                return Response({
                    'headline': 'Ready to achieve your goals?',
                    'error': 'No active vision or goalspec found'
                })

            # Use old vision logic
            today = timezone.now().date().isoformat()
            cache_key = f"daily_headline_{request.user.id}_{vision.id}_{today}"
            cached_headline = cache.get(cache_key)
            if cached_headline:
                return Response({
                    'headline': cached_headline,
                    'cached': True
                })

            try:
                headline = ai_service.generate_daily_headline(vision.title)
                cache.set(cache_key, headline, 60 * 60 * 24)
                return Response({
                    'headline': headline,
                    'cached': False
                })
            except Exception as e:
                fallback = vision.title.replace('Vision:', '').strip().split(':')[0].lower()
                return Response({
                    'headline': fallback,
                    'error': str(e),
                    'fallback': True
                })

        # Generate headline from GoalSpec
        today = timezone.now().date()
        tasks_today = Todo.objects.filter(
            user=request.user,
            goalspec=primary_goalspec,
            scheduled_date=today
        )

        completed_today = tasks_today.filter(status='done').count()
        pending_today = tasks_today.filter(status='pending').count()

        # Generate headline based on category and progress
        headlines_by_category = {
            'study': [
                f"{pending_today} tasks closer to your dream university",
                f"Building your academic future today",
                f"{completed_today} wins for your MSc journey",
            ],
            'career': [
                f"{pending_today} steps toward your dream job",
                f"Your career breakthrough starts today",
                f"{completed_today} actions toward professional success",
            ],
            'sport': [
                f"{pending_today} workouts until peak performance",
                f"Today's training = tomorrow's victory",
                f"{completed_today} sessions toward your fitness goal",
            ],
            'finance': [
                f"{pending_today} moves toward financial freedom",
                f"Building wealth one action at a time",
                f"{completed_today} steps closer to your financial goal",
            ],
            'language': [
                f"{pending_today} lessons until fluency",
                f"Every word learned is progress made",
                f"{completed_today} practice sessions completed",
            ],
            'health': [
                f"{pending_today} healthy choices today",
                f"Your best health starts now",
                f"{completed_today} wellness actions completed",
            ],
            'creative': [
                f"{pending_today} creative tasks await",
                f"Your masterpiece takes shape today",
                f"{completed_today} creative wins today",
            ],
            'networking': [
                f"{pending_today} connections to make",
                f"Your network is your net worth",
                f"{completed_today} meaningful connections today",
            ],
        }

        category_headlines = headlines_by_category.get(
            primary_goalspec.category,
            [f"{pending_today} tasks toward your goal", f"Making progress today", f"{completed_today} wins today"]
        )

        # Choose headline based on progress
        if pending_today > 0:
            headline = category_headlines[0]
        elif completed_today > 0:
            headline = category_headlines[2]
        else:
            headline = category_headlines[1]

        return Response({
            'headline': headline,
            'goalspec_id': primary_goalspec.id,
            'generated_at': timezone.now().isoformat(),
        })
