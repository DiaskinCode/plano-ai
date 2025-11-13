from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from datetime import timedelta, datetime
from django.db.models import Sum, Count, Q, Avg, F
from todos.models import Todo
from vision.models import Vision, Milestone
from chat.models import ChatMessage


class OverviewAnalyticsView(APIView):
    """Overview tab - This week at a glance"""
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        date_range = request.query_params.get('range', 'week')  # week, last_week, 30days

        # Calculate date range
        today = timezone.now().date()
        if date_range == 'week':
            start_date = today - timedelta(days=today.weekday())
        elif date_range == 'last_week':
            start_date = today - timedelta(days=today.weekday() + 7)
        else:  # 30days
            start_date = today - timedelta(days=30)

        end_date = today

        # Focus minutes completed vs budget
        todos = Todo.objects.filter(
            user=request.user,
            scheduled_date__range=[start_date, end_date]
        )

        completed_todos = todos.filter(status='done')
        focus_minutes = completed_todos.aggregate(
            total=Sum('estimated_duration_minutes')
        )['total'] or 0

        # Budget (estimated for all scheduled tasks)
        budget_minutes = todos.aggregate(
            total=Sum('estimated_duration_minutes')
        )['total'] or 0

        # High priority tasks (priority=3) as proxy for critical tasks
        critical_tasks = todos.filter(priority=3)
        milestone_done = critical_tasks.filter(status='done').count()
        milestone_total = critical_tasks.count()

        # Check-ins done (simplified - count days with completed tasks)
        checkins_done = completed_todos.values('completed_at__date').distinct().count()

        # Best day and hour analysis
        best_day_data = completed_todos.values('completed_at__date').annotate(
            total_minutes=Sum('estimated_duration_minutes')
        ).order_by('-total_minutes').first()

        best_day = best_day_data['completed_at__date'].strftime('%a') if best_day_data else 'N/A'
        best_day_minutes = best_day_data['total_minutes'] if best_day_data else 0

        # Best hour (simplified - use scheduled time)
        best_hour_data = completed_todos.exclude(scheduled_time__isnull=True).values(
            'scheduled_time'
        ).annotate(
            count=Count('id')
        ).order_by('-count').first()

        best_hour = best_hour_data['scheduled_time'].strftime('%H:00') if best_hour_data else 'N/A'

        # 7-day heatmap data
        heatmap = []
        for i in range(7):
            date = today - timedelta(days=6-i)
            day_todos = completed_todos.filter(completed_at__date=date)
            morning = day_todos.filter(scheduled_time__hour__lt=12).aggregate(Sum('estimated_duration_minutes'))['estimated_duration_minutes__sum'] or 0
            afternoon = day_todos.filter(scheduled_time__hour__gte=12, scheduled_time__hour__lt=18).aggregate(Sum('estimated_duration_minutes'))['estimated_duration_minutes__sum'] or 0
            evening = day_todos.filter(scheduled_time__hour__gte=18).aggregate(Sum('estimated_duration_minutes'))['estimated_duration_minutes__sum'] or 0

            heatmap.append({
                'date': date.isoformat(),
                'morning': morning,
                'afternoon': afternoon,
                'evening': evening
            })

        return Response({
            'focus_minutes_completed': focus_minutes,
            'focus_minutes_budget': budget_minutes,
            'milestone_critical_done': milestone_done,
            'milestone_critical_total': milestone_total,
            'checkins_done': checkins_done,
            'best_day': best_day,
            'best_day_minutes': best_day_minutes,
            'best_hour': best_hour,
            'heatmap': heatmap,
            'insight': f"Best performance on {best_day} with {best_day_minutes} focus minutes",
        })


class TimeFocusAnalyticsView(APIView):
    """Time & Focus tab"""
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        date_range = request.query_params.get('range', 'week')
        today = timezone.now().date()

        if date_range == 'week':
            start_date = today - timedelta(days=today.weekday())
        elif date_range == 'last_week':
            start_date = today - timedelta(days=today.weekday() + 7)
        else:
            start_date = today - timedelta(days=30)

        todos = Todo.objects.filter(
            user=request.user,
            scheduled_date__range=[start_date, today]
        )

        # Focus minutes (high priority tasks)
        focus_todos = todos.filter(priority=3, status='done')
        focus_minutes = focus_todos.aggregate(Sum('estimated_duration_minutes'))['estimated_duration_minutes__sum'] or 0

        # Budget adherence
        planned_minutes = todos.aggregate(Sum('estimated_duration_minutes'))['estimated_duration_minutes__sum'] or 1
        completed_minutes = todos.filter(status='done').aggregate(Sum('estimated_duration_minutes'))['estimated_duration_minutes__sum'] or 0
        budget_adherence = (completed_minutes / planned_minutes * 100) if planned_minutes > 0 else 0

        # Time by category (simplified)
        deep_work = focus_todos.aggregate(Sum('estimated_duration_minutes'))['estimated_duration_minutes__sum'] or 0
        admin_work = todos.filter(priority=1, status='done').aggregate(Sum('estimated_duration_minutes'))['estimated_duration_minutes__sum'] or 0
        other_work = completed_minutes - deep_work - admin_work

        return Response({
            'focus_minutes': focus_minutes,
            'budget_adherence': round(budget_adherence, 1),
            'time_breakdown': {
                'deep_work': deep_work,
                'admin': admin_work,
                'other': max(0, other_work)
            }
        })


class TasksOutcomesAnalyticsView(APIView):
    """Tasks & Outcomes tab"""
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        date_range = request.query_params.get('range', 'week')
        today = timezone.now().date()

        if date_range == 'week':
            start_date = today - timedelta(days=today.weekday())
        elif date_range == 'last_week':
            start_date = today - timedelta(days=today.weekday() + 7)
        else:
            start_date = today - timedelta(days=30)

        todos = Todo.objects.filter(
            user=request.user,
            scheduled_date__range=[start_date, today]
        )

        completed = todos.filter(status='done').count()
        skipped = todos.filter(status='skipped').count()
        pending = todos.filter(status='pending').count()

        # By source
        plan_tasks = todos.filter(source='ai_generated').count()
        adhoc_tasks = todos.filter(source='integrated').count()

        # By priority completion rate
        p1_total = todos.filter(priority=1).count()
        p1_done = todos.filter(priority=1, status='done').count()
        p2_total = todos.filter(priority=2).count()
        p2_done = todos.filter(priority=2, status='done').count()
        p3_total = todos.filter(priority=3).count()
        p3_done = todos.filter(priority=3, status='done').count()

        return Response({
            'completed': completed,
            'skipped': skipped,
            'pending': pending,
            'by_source': {
                'plan': plan_tasks,
                'adhoc': adhoc_tasks,
            },
            'by_priority': [
                {'priority': 'Low', 'total': p1_total, 'done': p1_done},
                {'priority': 'Medium', 'total': p2_total, 'done': p2_done},
                {'priority': 'High', 'total': p3_total, 'done': p3_done},
            ]
        })


class MilestonesPathAnalyticsView(APIView):
    """Milestones & Path tab"""
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        vision = Vision.objects.filter(user=request.user, is_active=True).first()

        if not vision:
            return Response({
                'on_time_rate': 0,
                'path_confidence': 50,
                'milestones': []
            })

        milestones = Milestone.objects.filter(vision=vision).order_by('due_date')

        # Calculate on-time rate
        total_milestones = milestones.count()

        if total_milestones == 0:
            return Response({
                'on_time_rate': 0,
                'path_confidence': 50,
                'milestones': []
            })

        completed_on_time = milestones.filter(
            is_completed=True,
            completed_at__lte=F('due_date')
        ).count()

        on_time_rate = (completed_on_time / total_milestones * 100) if total_milestones > 0 else 0

        # Path confidence calculation
        confidence = min(100, 50 + (on_time_rate * 0.5))

        # Milestone data
        milestone_data = []
        for m in milestones:
            milestone_data.append({
                'id': m.id,
                'title': m.title,
                'due_date': m.due_date.isoformat(),
                'is_completed': m.is_completed,
                'progress': 100 if m.is_completed else 0,
            })

        return Response({
            'on_time_rate': round(on_time_rate, 1),
            'path_confidence': round(confidence, 1),
            'milestones': milestone_data,
        })


class HabitsQualityAnalyticsView(APIView):
    """Habits & Quality tab"""
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        today = timezone.now().date()
        last_30_days = today - timedelta(days=30)

        todos = Todo.objects.filter(
            user=request.user,
            scheduled_date__range=[last_30_days, today]
        )

        # Soft streak (days with planning in last 5 days)
        streak = 0
        for i in range(5):
            date = today - timedelta(days=i)
            if todos.filter(scheduled_date=date).exists():
                streak += 1

        # Check-in rate (days with completed tasks)
        days_with_completed = todos.filter(status='done').values('completed_at__date').distinct().count()
        checkin_rate = (days_with_completed / 30 * 100)

        # Planning quality metrics (simplified)
        total_tasks = todos.count()
        completed_tasks = todos.filter(status='done').count()
        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

        return Response({
            'soft_streak': streak,
            'checkin_rate': round(checkin_rate, 1),
            'completion_rate': round(completion_rate, 1),
            'planning_quality': {
                'consistency': round(checkin_rate, 1),
                'completion': round(completion_rate, 1),
            }
        })


class StreakView(APIView):
    """Get user's true consecutive streak"""
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        user = request.user
        today = timezone.now().date()

        # Calculate current streak by going backward from today
        current_streak = 0
        check_date = today

        while True:
            # Check if user was active on this date
            # Active = completed task, created task, or messaged AI
            task_completed = Todo.objects.filter(
                user=user,
                status='done',
                completed_at__date=check_date
            ).exists()

            task_created = Todo.objects.filter(
                user=user,
                created_at__date=check_date
            ).exists()

            ai_message = ChatMessage.objects.filter(
                user=user,
                role='user',
                created_at__date=check_date
            ).exists()

            is_active = task_completed or task_created or ai_message

            if is_active:
                current_streak += 1
                check_date -= timedelta(days=1)
            else:
                # Streak broken
                break

        # Update user's streak data
        if current_streak > user.longest_streak:
            user.longest_streak = current_streak

        user.current_streak = current_streak
        user.last_activity_date = today if current_streak > 0 else user.last_activity_date
        user.save(update_fields=['current_streak', 'longest_streak', 'last_activity_date'])

        # Check today's activities
        activities_today = []
        if Todo.objects.filter(user=user, status='done', completed_at__date=today).exists():
            activities_today.append('completed_tasks')
        if Todo.objects.filter(user=user, created_at__date=today).exists():
            activities_today.append('created_tasks')
        if ChatMessage.objects.filter(user=user, role='user', created_at__date=today).exists():
            activities_today.append('messaged_ai')

        is_active_today = len(activities_today) > 0

        return Response({
            'current_streak': current_streak,
            'longest_streak': user.longest_streak,
            'is_active_today': is_active_today,
            'activities_today': activities_today
        })


class WeeklyReflectionView(APIView):
    """Get latest weekly reflection for the user"""
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        from .models import WeeklyReflection

        # Get latest reflection
        reflection = WeeklyReflection.objects.filter(
            user=request.user
        ).order_by('-week_start_date').first()

        if not reflection:
            return Response({
                'has_reflection': False,
                'message': 'No reflection generated yet'
            })

        # Mark as read
        if not reflection.is_read:
            reflection.mark_as_read()

        return Response({
            'has_reflection': True,
            'reflection': {
                'id': reflection.id,
                'week': reflection.get_week_label(),
                'week_start': reflection.week_start_date.isoformat(),
                'week_end': reflection.week_end_date.isoformat(),
                'insights': reflection.insights,
                'action_items': reflection.action_items,
                'full_message': reflection.full_message,
                'is_read': reflection.is_read,
                'patterns_analyzed': reflection.patterns_analyzed,
                'generated_at': reflection.generated_at.isoformat(),
                'generation_method': reflection.generation_method
            }
        })


class GenerateReflectionView(APIView):
    """Generate weekly reflection on demand"""
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        from .tasks import generate_reflection_for_user
        from datetime import datetime

        # Optional: specify week_start
        week_start_str = request.data.get('week_start')

        # Trigger async task
        task = generate_reflection_for_user.delay(
            user_id=request.user.id,
            week_start_str=week_start_str
        )

        return Response({
            'status': 'generating',
            'task_id': task.id,
            'message': 'Reflection generation started. Check back in a few seconds.'
        }, status=status.HTTP_202_ACCEPTED)


class BehaviorPatternsView(APIView):
    """Get user behavior patterns"""
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        from .models import UserBehaviorPattern

        # Optional: filter by pattern_type
        pattern_type = request.query_params.get('type')

        patterns = UserBehaviorPattern.objects.filter(
            user=request.user,
            is_active=True
        )

        if pattern_type:
            patterns = patterns.filter(pattern_type=pattern_type)

        patterns = patterns.order_by('-confidence_score', '-last_updated')[:20]

        return Response({
            'patterns': [
                {
                    'id': p.id,
                    'type': p.pattern_type,
                    'time_window': {
                        'start': p.time_window_start.isoformat(),
                        'end': p.time_window_end.isoformat()
                    },
                    'data': p.data,
                    'confidence_score': p.confidence_score,
                    'first_detected': p.first_detected.isoformat(),
                    'last_updated': p.last_updated.isoformat()
                }
                for p in patterns
            ]
        })


class ReflectionHistoryView(APIView):
    """Get reflection history (last 8 weeks)"""
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        from .models import WeeklyReflection

        reflections = WeeklyReflection.objects.filter(
            user=request.user
        ).order_by('-week_start_date')[:8]

        return Response({
            'reflections': [
                {
                    'id': r.id,
                    'week': r.get_week_label(),
                    'week_start': r.week_start_date.isoformat(),
                    'insights_count': len(r.insights),
                    'action_items_count': len(r.action_items),
                    'is_read': r.is_read,
                    'generated_at': r.generated_at.isoformat(),
                    'patterns_analyzed': r.patterns_analyzed
                }
                for r in reflections
            ]
        })


# ==============================================
# Daily Pulse / Morning Brief Views
# ==============================================

class DailyPulseView(APIView):
    """Get today's Daily Pulse brief"""
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        from .models import DailyBrief

        today = timezone.now().date()

        # Get today's brief
        brief = DailyBrief.objects.filter(
            user=request.user,
            date=today
        ).first()

        if not brief:
            return Response({
                'has_brief': False,
                'message': 'No brief for today yet. Generate one?'
            })

        # Mark as shown in app if first time
        if not brief.shown_in_app:
            brief.mark_shown('app')

        return Response({
            'has_brief': True,
            'brief': {
                'id': brief.id,
                'date': brief.date.isoformat(),
                'greeting': brief.greeting_message,
                'top_priorities': brief.top_priorities,
                'workload': {
                    'percentage': brief.workload_percentage,
                    'status': brief.workload_status,
                    'total_minutes': brief.total_timebox_minutes,
                    'available_minutes': brief.available_minutes,
                    'emoji': brief.get_workload_emoji()
                },
                'warnings': brief.warnings,
                'smart_suggestions': brief.smart_suggestions,
                'weekly_progress': brief.weekly_progress,
                'full_message': brief.full_message,
                'generated_at': brief.generated_at.isoformat(),
                'shown_in_app': brief.shown_in_app,
                'shown_in_chat': brief.shown_in_chat,
            }
        })


class GenerateDailyPulseView(APIView):
    """Generate or regenerate Daily Pulse"""
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        from .tasks import regenerate_daily_pulse_on_login

        # Trigger async regeneration
        task = regenerate_daily_pulse_on_login.delay(request.user.id)

        return Response({
            'status': 'generating',
            'task_id': task.id,
            'message': 'Daily Pulse generation started'
        }, status=status.HTTP_202_ACCEPTED)


class DailyPulseMarkShownView(APIView):
    """Mark Daily Pulse as shown in specific channel"""
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        from .models import DailyBrief

        channel = request.data.get('channel')  # 'app', 'push', 'chat'

        if channel not in ['app', 'push', 'chat']:
            return Response({
                'error': 'Invalid channel. Must be: app, push, or chat'
            }, status=status.HTTP_400_BAD_REQUEST)

        today = timezone.now().date()

        brief = DailyBrief.objects.filter(
            user=request.user,
            date=today
        ).first()

        if not brief:
            return Response({
                'error': 'No brief found for today'
            }, status=status.HTTP_404_NOT_FOUND)

        brief.mark_shown(channel)

        return Response({
            'success': True,
            'channel': channel,
            'first_shown_at': brief.first_shown_at.isoformat() if brief.first_shown_at else None
        })


class SendDailyPulseToChatView(APIView):
    """Send Daily Pulse as chat message"""
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        from .models import DailyBrief
        from .daily_pulse_service import DailyPulseGenerator
        from chat.models import ChatMessage, ChatConversation

        today = timezone.now().date()

        # Get or generate today's brief
        brief = DailyBrief.objects.filter(
            user=request.user,
            date=today
        ).first()

        if not brief:
            # Generate new brief
            generator = DailyPulseGenerator(request.user)
            brief = generator.generate_daily_brief(trigger='on_login')

            if not brief:
                return Response({
                    'success': False,
                    'error': 'Failed to generate Daily Pulse'
                }, status=status.HTTP_400_BAD_REQUEST)

        # Check if already sent to chat
        if brief.shown_in_chat:
            return Response({
                'success': True,
                'already_sent': True,
                'message': 'Daily Pulse already sent to chat today'
            })

        # Get or create main conversation
        conversation, _ = ChatConversation.objects.get_or_create(
            user=request.user,
            task__isnull=True,
            defaults={'title': 'Daily Chat'}
        )

        # Create chat message
        ChatMessage.objects.create(
            user=request.user,
            conversation=conversation,
            role='assistant',
            content=brief.full_message
        )

        # Mark as shown
        brief.mark_shown('chat')

        return Response({
            'success': True,
            'conversation_id': conversation.id,
            'message': 'Daily Pulse sent to chat successfully'
        })
