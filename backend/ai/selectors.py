"""
Optimized database queries for AI context building
"""
from datetime import datetime, timedelta
from django.db.models import Q, Count, Prefetch
from django.utils import timezone

from users.models import UserProfile
from vision.models import Vision, Milestone
from todos.models import Todo
from events.models import CheckInEvent, OpportunityEvent
from chat.models import ChatSummary


def get_profile(user_id: int) -> dict:
    """Get user profile data"""
    try:
        profile = UserProfile.objects.select_related('user').get(user_id=user_id)
        return {
            'country': profile.country_of_residence,
            'destinations': profile.destinations,
            'languages': profile.languages,
            'network': profile.network,
            'coach_character': profile.coach_character,
            'energy_peak': profile.energy_peak,
            'notification_tone': profile.notification_tone,
            'budget_range': profile.budget_range,
            'target_timeline': profile.target_timeline,
            'constraints': profile.constraints,
        }
    except UserProfile.DoesNotExist:
        return {}


def get_vision(user_id: int) -> dict:
    """Get active vision data"""
    try:
        vision = Vision.objects.filter(
            user_id=user_id,
            is_active=True
        ).select_related('scenario').first()

        if not vision:
            return {}

        return {
            'title': vision.title,
            'summary': vision.summary,
            'horizon_start': vision.horizon_start.isoformat(),
            'horizon_end': vision.horizon_end.isoformat(),
            'progress_percentage': vision.progress_percentage,
            'monthly_milestones': vision.monthly_milestones,
        }
    except Exception:
        return {}


def get_todos(user_id: int) -> tuple:
    """Get categorized todos: today, tomorrow, overdue"""
    today = timezone.now().date()
    tomorrow = today + timedelta(days=1)

    # Today's todos (include all statuses so AI can see what's done)
    todos_today = list(Todo.objects.filter(
        user_id=user_id,
        scheduled_date=today
    ).values('id', 'title', 'priority', 'status', 'estimated_duration_minutes', 'scheduled_time')[:10])

    # Tomorrow's todos
    todos_tomorrow = list(Todo.objects.filter(
        user_id=user_id,
        scheduled_date=tomorrow,
        status='pending'
    ).values('id', 'title', 'priority', 'scheduled_time')[:10])

    # Overdue todos (sorted by priority and days overdue)
    overdue = list(Todo.objects.filter(
        user_id=user_id,
        scheduled_date__lt=today,
        status='pending'
    ).values('id', 'title', 'priority', 'scheduled_date')[:10])

    # Calculate days overdue
    for todo in overdue:
        todo['days_overdue'] = (today - todo['scheduled_date']).days

    # Sort by priority (desc) and days overdue (desc)
    overdue.sort(key=lambda x: (x['priority'], x['days_overdue']), reverse=True)

    return todos_today, todos_tomorrow, overdue


def get_deadlines(vision_id: int, days: int = 60) -> list:
    """Get upcoming deadlines from milestones"""
    if not vision_id:
        return []

    cutoff_date = timezone.now().date() + timedelta(days=days)

    milestones = Milestone.objects.filter(
        vision_id=vision_id,
        is_completed=False,
        due_date__lte=cutoff_date
    ).values('title', 'due_date').order_by('due_date')[:10]

    return [
        {
            'title': m['title'],
            'date': m['due_date'].isoformat()
        }
        for m in milestones
    ]


def get_events(user_id: int, days: int = 14) -> list:
    """Get recent events (check-ins and opportunities)"""
    cutoff_date = timezone.now().date() - timedelta(days=days)

    # Check-ins
    checkins = CheckInEvent.objects.filter(
        user_id=user_id,
        date__gte=cutoff_date
    ).values('date', 'missed_tasks', 'missed_reason', 'new_opportunities').order_by('-date')[:5]

    # Opportunities
    opportunities = OpportunityEvent.objects.filter(
        user_id=user_id,
        date_occurred__gte=cutoff_date
    ).values('title', 'description', 'date_occurred', 'ai_impact_assessment').order_by('-date_occurred')[:5]

    # Combine and format
    events = []

    for checkin in checkins:
        if checkin.get('missed_tasks'):
            events.append({
                'type': 'checkin_missed',
                'date': checkin['date'].isoformat(),
                'missed_count': len(checkin['missed_tasks']),
                'reason': checkin.get('missed_reason', '')
            })
        if checkin.get('new_opportunities'):
            events.append({
                'type': 'checkin_opportunity',
                'date': checkin['date'].isoformat(),
                'note': checkin['new_opportunities']
            })

    for opp in opportunities:
        events.append({
            'type': 'new_opportunity',
            'date': opp['date_occurred'].isoformat(),
            'title': opp['title'],
            'impact': opp.get('ai_impact_assessment', 'medium')
        })

    # Sort by date descending
    events.sort(key=lambda x: x['date'], reverse=True)
    return events[:10]


def get_chat_summary(user_id: int, max_chars: int = 1200) -> str:
    """Get latest chat summary"""
    summary = ChatSummary.objects.filter(
        user_id=user_id
    ).order_by('-created_at').first()

    if summary:
        return summary.summary[:max_chars]
    return ""


def rank_items(items: list, limit: int = 6) -> list:
    """Rank and limit items by priority"""
    # Sort by priority (descending)
    sorted_items = sorted(items, key=lambda x: x.get('priority', 0), reverse=True)
    return sorted_items[:limit]
