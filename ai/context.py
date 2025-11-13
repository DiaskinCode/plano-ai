"""
AI Context Builder - Assembles user state snapshot for LLM
"""
from typing import Dict, Any
from .selectors import (
    get_profile,
    get_vision,
    get_todos,
    get_deadlines,
    get_events,
    get_chat_summary,
    rank_items
)


def build_user_state_snapshot(user_id: int, token_budget: int = 2000) -> Dict[str, Any]:
    """
    Build a token-efficient snapshot of user state for AI context

    Args:
        user_id: User ID
        token_budget: Approximate token limit for the snapshot (default 2000)

    Returns:
        Dict containing user context for AI
    """
    # Get user timezone and current local time
    from users.models import User
    from django.utils import timezone
    import pytz

    user = User.objects.get(id=user_id)
    user_tz_str = user.timezone if user.timezone else 'UTC'
    try:
        user_tz = pytz.timezone(user_tz_str)
        current_time_local = timezone.now().astimezone(user_tz)
    except:
        user_tz = pytz.UTC
        current_time_local = timezone.now()

    # Get core data
    profile = get_profile(user_id)
    vision = get_vision(user_id)
    todos_today, todos_tomorrow, overdue = get_todos(user_id)

    # Get vision ID for deadlines
    vision_id = None
    if vision:
        # Try to get vision ID from the database
        from vision.models import Vision
        active_vision = Vision.objects.filter(user_id=user_id, is_active=True).first()
        vision_id = active_vision.id if active_vision else None

    deadlines = get_deadlines(vision_id, days=60) if vision_id else []
    recent_events = get_events(user_id, days=14)
    chat_summary = get_chat_summary(user_id, max_chars=1200)

    # Build snapshot
    snapshot = {
        'user_meta': {
            'country': profile.get('country', ''),
            'destinations': profile.get('destinations', []),
            'languages': profile.get('languages', []),
            'network': profile.get('network', {}),
            'coach_character': profile.get('coach_character', 'supportive'),
            'energy_peak': profile.get('energy_peak', 'morning'),
            'notification_tone': profile.get('notification_tone', 'gentle'),
            'budget_range': profile.get('budget_range', ''),
            'target_timeline': profile.get('target_timeline', ''),
            'constraints': profile.get('constraints', {}),
            'timezone': user_tz_str,
            'current_time': current_time_local.strftime('%Y-%m-%d %H:%M:%S'),
            'current_date': current_time_local.strftime('%Y-%m-%d'),
            'current_day': current_time_local.strftime('%A'),
        },
        'vision': vision if vision else {},
        'deadlines_next_60d': deadlines[:6],
        'todos_today': rank_items(todos_today, limit=6),
        'todos_tomorrow': todos_tomorrow[:4],
        'todos_overdue_top3': overdue[:3],
        'recent_events': recent_events[:6],
        'chat_summary': chat_summary,
    }

    return snapshot


def format_snapshot_for_prompt(snapshot: Dict[str, Any]) -> str:
    """
    Format the snapshot into a readable string for LLM prompt

    Args:
        snapshot: User state snapshot from build_user_state_snapshot

    Returns:
        Formatted string for prompt injection
    """
    lines = ["=== USER CONTEXT ===\n"]

    # User Meta
    meta = snapshot.get('user_meta', {})
    current_time = meta.get('current_time', 'N/A')
    lines.append(f"**Current Time (User's local time): {current_time}**")
    lines.append(f"**Current Date: {meta.get('current_date', 'N/A')} ({meta.get('current_day', 'N/A')})**")
    lines.append(f"**User Timezone: {meta.get('timezone', 'UTC')}**")
    lines.append("")
    lines.append("CRITICAL: When calculating relative times, you MUST ADD the offset to the current time above!")
    lines.append("Examples:")
    lines.append(f"  - 'через час' (in 1 hour) → Current time {current_time} + 1 hour")
    lines.append(f"  - 'через 30 минут' (in 30 min) → Current time {current_time} + 30 minutes")
    lines.append(f"  - 'через 3 минуты' (in 3 min) → Current time {current_time} + 3 minutes")
    lines.append("  - 'завтра в 9 утра' (tomorrow 9 AM) → Tomorrow's date + 09:00")
    lines.append("DO NOT return arbitrary times like 17:00 or 09:00 - calculate based on current time!")
    lines.append("")
    lines.append(f"Coach Character: {meta.get('coach_character', 'supportive')}")
    lines.append(f"Energy Peak: {meta.get('energy_peak', 'morning')}")
    if meta.get('country'):
        lines.append(f"Location: {meta['country']}")
    if meta.get('destinations'):
        lines.append(f"Target Destinations: {', '.join(meta['destinations'])}")

    # Vision
    vision = snapshot.get('vision', {})
    if vision:
        lines.append(f"\nVision: {vision.get('title', 'N/A')}")
        lines.append(f"Summary: {vision.get('summary', 'N/A')}")
        lines.append(f"Progress: {vision.get('progress_percentage', 0)}%")

    # Deadlines
    deadlines = snapshot.get('deadlines_next_60d', [])
    if deadlines:
        lines.append("\nUpcoming Deadlines:")
        for deadline in deadlines:
            lines.append(f"  - {deadline['title']} ({deadline['date']})")

    # Today's Todos
    todos_today = snapshot.get('todos_today', [])
    if todos_today:
        lines.append("\nToday's Tasks:")
        for todo in todos_today:
            priority_str = "!!!" if todo.get('priority') == 3 else "!!" if todo.get('priority') == 2 else "!"
            status = todo.get('status', 'pending')
            status_str = f" [{status}]" if status != 'pending' else ""
            lines.append(f"  {priority_str} [ID:{todo.get('id')}] {todo['title']}{status_str}")

    # Overdue
    overdue = snapshot.get('todos_overdue_top3', [])
    if overdue:
        lines.append("\nOverdue Tasks:")
        for todo in overdue:
            lines.append(f"  - [ID:{todo.get('id')}] {todo['title']} ({todo.get('days_overdue', 0)} days overdue)")

    # Recent Events
    events = snapshot.get('recent_events', [])
    if events:
        lines.append("\nRecent Events:")
        for event in events[:3]:  # Limit to 3 most recent
            if event['type'] == 'new_opportunity':
                lines.append(f"  - NEW: {event.get('title', 'Opportunity')} (impact: {event.get('impact', 'medium')})")
            elif event['type'] == 'checkin_missed':
                lines.append(f"  - Missed {event.get('missed_count', 0)} tasks: {event.get('reason', '')}")

    # Chat Summary
    summary = snapshot.get('chat_summary', '')
    if summary:
        lines.append(f"\nChat History Summary: {summary}")

    lines.append("\n=== END CONTEXT ===")

    return "\n".join(lines)
