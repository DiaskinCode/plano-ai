from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytz
from django.utils import timezone

from .models import MentorAvailabilityRule, MentorBooking

# UTC timezone for conversions (Django 5.x compatible)
UTC = ZoneInfo("UTC")


class AvailabilityService:
    """Service for generating available time slots from mentor's availability rules"""

    DURATION_OPTIONS = [30, 60]  # Standard slot durations in minutes

    @staticmethod
    def generate_slots(mentor, start_date, end_date, duration_minutes=60):
        """
        Generate available time slots for a mentor within a date range.

        Args:
            mentor: MentorProfile instance
            start_date: datetime or date (inclusive)
            end_date: datetime or date (exclusive)
            duration_minutes: slot duration (default 60)

        Returns:
            List of dicts with start_at_utc, end_at_utc, duration_minutes
        """
        slots = []

        # Ensure we have datetime objects
        if isinstance(start_date, datetime):
            start_dt = start_date
        else:
            start_dt = datetime.combine(start_date, datetime.min.time()).replace(
                tzinfo=UTC
            )

        if isinstance(end_date, datetime):
            end_dt = end_date
        else:
            end_dt = datetime.combine(end_date, datetime.min.time()).replace(tzinfo=UTC)

        # Get mentor's active availability rules
        rules = MentorAvailabilityRule.objects.filter(mentor=mentor, is_active=True)

        if not rules:
            return slots

        # Get existing bookings that conflict (confirmed and requested)
        existing_bookings = MentorBooking.objects.filter(
            mentor=mentor,
            status__in=["confirmed", "requested"],
            start_at_utc__lt=end_dt,
            end_at_utc__gt=start_dt,
        )

        # Create a set of blocked time ranges for quick lookup
        blocked_ranges = []
        for booking in existing_bookings:
            blocked_ranges.append(
                (
                    int(booking.start_at_utc.timestamp()),
                    int(booking.end_at_utc.timestamp()),
                )
            )

        # Generate slots for each day in range
        current_dt = start_dt
        while current_dt < end_dt:
            # Get day of week (0=Monday, 6=Sunday)
            day_of_week = current_dt.weekday()

            # Find rules for this day
            day_rules = rules.filter(day_of_week=day_of_week)

            for rule in day_rules:
                # Convert rule's minute-based times to datetime in mentor's timezone
                mentor_tz = pytz.timezone(mentor.timezone)

                # Create the start/end datetime in mentor's timezone
                slot_date = current_dt.date()
                slot_start = mentor_tz.localize(
                    datetime.combine(slot_date, datetime.min.time())
                    + timedelta(minutes=rule.start_minute)
                )
                slot_end = mentor_tz.localize(
                    datetime.combine(slot_date, datetime.min.time())
                    + timedelta(minutes=rule.end_minute)
                )

                # Convert to UTC
                slot_start_utc = slot_start.astimezone(UTC)
                slot_end_utc = slot_end.astimezone(UTC)

                # Generate slots within this availability window
                slot_time = slot_start_utc
                while slot_time + timedelta(minutes=duration_minutes) <= slot_end_utc:
                    slot_end_time = slot_time + timedelta(minutes=duration_minutes)

                    # Check if this slot conflicts with existing bookings
                    slot_start_ts = int(slot_time.timestamp())
                    slot_end_ts = int(slot_end_time.timestamp())

                    is_blocked = False
                    for blocked_start, blocked_end in blocked_ranges:
                        # Overlap check: slot_start < blocked_end AND slot_end > blocked_start
                        if slot_start_ts < blocked_end and slot_end_ts > blocked_start:
                            is_blocked = True
                            break

                    if not is_blocked:
                        slots.append(
                            {
                                "start_at_utc": slot_time.isoformat(),
                                "end_at_utc": slot_end_time.isoformat(),
                                "duration_minutes": duration_minutes,
                            }
                        )

                    # Move to next potential slot
                    slot_time = slot_end_time

            # Move to next day
            current_dt += timedelta(days=1)

        # Sort slots by start time
        slots.sort(key=lambda x: x["start_at_utc"])

        return slots


class SuggestionNormalizationService:
    """Service for normalizing human-friendly suggestion formats to internal format"""

    @staticmethod
    def normalize_plan_suggestions(suggestions):
        """
        Convert human-friendly plan suggestions to internal format.

        Input format:
        [
            {"task_id": 123, "type": "change_deadline", "new_due_date": "2026-03-20", "note": "..."},
            {"type": "add_task", "title": "...", "due_date": "...", "note": "..."}
        ]

        Output format:
        [
            {"action": "edit_task", "task_id": 123, "patch": {"due_date": "..."}, "note": "..."},
            {"action": "add_task", "task": {"title": "...", "due_date": "..."}, "note": "..."}
        ]
        """
        normalized = []

        for sugg in suggestions:
            sugg_type = sugg.get("type")

            if sugg_type == "change_deadline":
                normalized.append(
                    {
                        "action": "edit_task",
                        "task_id": sugg["task_id"],
                        "patch": {"due_date": sugg["new_due_date"]},
                        "note": sugg.get("note", ""),
                    }
                )
            elif sugg_type == "add_task":
                normalized.append(
                    {
                        "action": "add_task",
                        "task": {"title": sugg["title"], "due_date": sugg["due_date"]},
                        "note": sugg.get("note", ""),
                    }
                )

        return normalized

    @staticmethod
    def normalize_essay_feedback(strengths, improvements, rewrite_suggestions, scores):
        """
        Convert human-friendly essay feedback to internal format.
        """
        return {
            "strengths": strengths,
            "improvements": improvements,
            "rewrite_suggestions": rewrite_suggestions,
            "scores": scores,
        }


class SuggestionApplicationService:
    """Service for applying mentor suggestions to tasks"""

    ALLOWED_PATCH_FIELDS = {"due_date", "priority", "title"}

    @staticmethod
    def apply_suggestions(review_request, user):
        """
        Apply normalized suggestions from a review response.

        Args:
            review_request: MentorReviewRequest instance
            user: The student user applying the suggestions

        Returns:
            dict with summary of applied changes
        """
        from todos.models import Todo

        response = review_request.response
        if not response:
            raise ValueError("No response found for this review request")

        suggestions = response.payload_json.get("suggestions", [])
        applied = []
        errors = []

        for sugg in suggestions:
            action = sugg.get("action")

            if action == "edit_task":
                try:
                    task = Todo.objects.get(id=sugg["task_id"])

                    # Validate ownership
                    if task.user != user:
                        errors.append(f"Task {sugg['task_id']}: Not owned by student")
                        continue

                    # Validate belongs to same goal_spec (for plan reviews)
                    if review_request.request_type == "plan":
                        if task.goal_spec != review_request.goal_spec:
                            errors.append(
                                f"Task {sugg['task_id']}: Not part of the reviewed goal"
                            )
                            continue

                    # Apply only allowed patches
                    patch = sugg.get("patch", {})
                    old_values = {}
                    new_values = {}

                    for field, value in patch.items():
                        if (
                            field
                            not in SuggestionApplicationService.ALLOWED_PATCH_FIELDS
                        ):
                            errors.append(
                                f"Task {sugg['task_id']}: Field '{field}' not allowed"
                            )
                            continue

                        # Log old value
                        old_values[field] = getattr(task, field, None)
                        # Apply new value
                        setattr(task, field, value)
                        new_values[field] = value

                    task.save()

                    applied.append(
                        {
                            "type": "edit_task",
                            "task_id": task.id,
                            "task_title": task.title,
                            "old_values": old_values,
                            "new_values": new_values,
                            "note": sugg.get("note", ""),
                        }
                    )

                except Todo.DoesNotExist:
                    errors.append(f"Task {sugg['task_id']}: Not found")

            elif action == "add_task":
                try:
                    # Create new task linked to goal_spec
                    task_data = sugg.get("task", {})

                    task = Todo.objects.create(
                        user=user,
                        title=task_data.get("title", "New task from mentor"),
                        due_date=task_data.get("due_date"),
                        goal_spec=review_request.goal_spec
                        if review_request.request_type == "plan"
                        else None,
                        source="Mentor",
                        status="pending",
                    )

                    applied.append(
                        {
                            "type": "add_task",
                            "task_id": task.id,
                            "task_title": task.title,
                            "note": sugg.get("note", ""),
                        }
                    )

                except Exception as e:
                    errors.append(f"Failed to add task: {str(e)}")

        return {
            "applied": applied,
            "errors": errors,
            "total_applied": len(applied),
            "total_errors": len(errors),
        }
