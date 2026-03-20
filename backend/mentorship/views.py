from datetime import datetime, timedelta

from django.db import transaction
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    MentorAvailabilityRule,
    MentorBooking,
    MentorProfile,
    MentorReviewRequest,
    MentorReviewResponse,
)
from .notification_service import NotificationService
from .permissions import (
    IsBookingMentor,
    IsBookingMentorOrStudentCanCancel,
    IsBookingStudent,
    IsMentor,
    IsReviewRequestMentor,
    IsReviewRequestStudent,
    IsVerifiedMentor,
)
from .serializers import (
    AvailabilitySerializer,
    EssayReviewSubmissionSerializer,
    MentorAvailabilityRuleSerializer,
    MentorBookingSerializer,
    MentorProfileSerializer,
    MentorReviewRequestSerializer,
    MentorReviewResponseSerializer,
    PlanReviewSubmissionSerializer,
)
from .services import (
    AvailabilityService,
    SuggestionApplicationService,
    SuggestionNormalizationService,
)

# === Mentor Public Endpoints ===


class MentorListView(APIView):
    """Public list of verified mentors"""

    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        # Only show approved mentors to public
        mentors = MentorProfile.objects.filter(
            verification_status='approved', is_active=True
        ).select_related("user")

        # Filtering
        expertise = request.query_params.get("expertise")
        if expertise:
            mentors = mentors.filter(expertise_areas__contains=expertise)

        min_rating = request.query_params.get("min_rating")
        if min_rating:
            mentors = mentors.filter(rating__gte=float(min_rating))

        search = request.query_params.get("search")
        if search:
            mentors = mentors.filter(
                models.Q(title__icontains=search)
                | models.Q(bio__icontains=search)
                | models.Q(expertise_areas__icontains=search)
            )

        # Sorting
        ordering = request.query_params.get("ordering", "rating")
        if ordering == "rating":
            mentors = mentors.order_by("-rating")
        elif ordering == "sessions":
            mentors = mentors.order_by("-total_sessions")
        elif ordering == "price_asc":
            mentors = mentors.order_by("hourly_rate_credits")
        elif ordering == "price_desc":
            mentors = mentors.order_by("-hourly_rate_credits")

        # Pagination
        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(mentors, request)

        serializer = MentorProfileSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


from django.db import models as django_models  # Alias to avoid conflict


class MentorDetailView(APIView):
    """Public mentor details"""

    permission_classes = (permissions.AllowAny,)

    def get(self, request, id):
        try:
            # Only show approved mentors
            mentor = MentorProfile.objects.get(id=id, verification_status='approved', is_active=True)
        except MentorProfile.DoesNotExist:
            return Response(
                {"error": "Mentor not found"}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = MentorProfileSerializer(mentor)
        return Response(serializer.data)


class MentorAvailabilityView(APIView):
    """Get mentor's available time slots"""

    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, id):
        try:
            # Only check availability for approved mentors
            mentor = MentorProfile.objects.get(id=id, verification_status='approved', is_active=True)
        except MentorProfile.DoesNotExist:
            return Response(
                {"error": "Mentor not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Parse date range
        start_str = request.query_params.get("from")
        end_str = request.query_params.get("to")
        duration = int(request.query_params.get("duration", 60))

        if not start_str or not end_str:
            return Response(
                {"error": "from and to query parameters required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            start_date = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
            end_date = datetime.fromisoformat(end_str.replace("Z", "+00:00"))
        except ValueError:
            return Response(
                {"error": "Invalid date format. Use ISO 8601 format."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Generate slots
        slots = AvailabilityService.generate_slots(
            mentor, start_date, end_date, duration
        )

        response_data = {"mentor_timezone": mentor.timezone, "slots": slots}

        serializer = AvailabilitySerializer(response_data)
        return Response(serializer.data)


class BookSessionView(APIView):
    """Book a mentor session"""

    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, id):
        # Check subscription paywall
        from onboarding.models import UserSubscription

        try:
            subscription = UserSubscription.objects.get(user=request.user)
        except UserSubscription.DoesNotExist:
            return Response(
                {
                    "error": "Subscription required",
                    "message": "You need an active subscription to book mentor sessions.",
                    "upgrade_required": True
                },
                status=status.HTTP_403_FORBIDDEN
            )

        # Check if subscription is active
        if not subscription.is_active():
            return Response(
                {
                    "error": "Subscription not active",
                    "message": "Your subscription is not active. Please renew your subscription to book mentor sessions.",
                    "upgrade_required": True
                },
                status=status.HTTP_403_FORBIDDEN
            )

        # Check if user has remaining mentor bookings
        if not subscription.can_book_mentor_session():
            plan = subscription.plan
            return Response(
                {
                    "error": "Monthly limit reached",
                    "message": f"You've used all your mentor bookings for this month. Your {plan.display_name} plan includes {plan.monthly_mentor_bookings} bookings per month.",
                    "limit": plan.monthly_mentor_bookings,
                    "upgrade_required": True
                },
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            # Only allow booking with approved mentors
            mentor = MentorProfile.objects.get(id=id, verification_status='approved', is_active=True)
        except MentorProfile.DoesNotExist:
            return Response(
                {"error": "Mentor not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Parse request data
        start_at_str = request.data.get("start_at")
        duration_minutes = request.data.get("duration_minutes", 60)

        if not start_at_str:
            return Response(
                {"error": "start_at is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            start_at = datetime.fromisoformat(start_at_str.replace("Z", "+00:00"))
            # Convert to UTC if naive
            if start_at.tzinfo is None:
                start_at = start_at.replace(tzinfo=timezone.utc)
        except ValueError:
            return Response(
                {"error": "Invalid datetime format. Use ISO 8601 format."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        end_at = start_at + timedelta(minutes=duration_minutes)

        # Atomic booking creation with conflict check
        try:
            with transaction.atomic():
                # Lock mentor row
                mentor_locked = MentorProfile.objects.select_for_update().get(
                    id=mentor.id
                )

                # Lock conflicting booking rows
                existing = (
                    MentorBooking.objects.select_for_update()
                    .filter(mentor=mentor_locked, status__in=["confirmed", "requested"])
                    .filter(start_at_utc__lt=end_at, end_at_utc__gt=start_at)
                )

                if existing.exists():
                    return Response(
                        {"error": "Time slot already booked"},
                        status=status.HTTP_409_CONFLICT,
                    )

                # Create booking
                booking = MentorBooking.objects.create(
                    mentor=mentor_locked,
                    student=request.user,
                    start_at_utc=start_at,
                    end_at_utc=end_at,
                    duration_minutes=duration_minutes,
                    student_notes=request.data.get("notes", ""),
                    topic=request.data.get("topic", ""),
                    meeting_url=mentor_locked.meeting_link,
                    status="requested",
                )

                # Decrement mentor booking count
                subscription.use_mentor_booking()

                # Send notification to mentor
                NotificationService.notify_booking_requested(booking)

        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        serializer = MentorBookingSerializer(booking)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


# === Mentor Self-Service Endpoints ===


class MyMentorProfileView(APIView):
    """Get or update current user's mentor profile"""

    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        # Get or create mentor profile
        profile, created = MentorProfile.objects.get_or_create(
            user=request.user,
            defaults={"title": "Your Name", "bio": "", "timezone": "America/New_York"},
        )

        serializer = MentorProfileSerializer(profile)
        return Response(serializer.data)

    def patch(self, request):
        # Get or create mentor profile with minimal defaults
        profile, created = MentorProfile.objects.get_or_create(
            user=request.user,
            defaults={"title": "Your Name", "bio": "", "timezone": "America/New_York"},
        )

        serializer = MentorProfileSerializer(profile, data=request.data, partial=True)

        if serializer.is_valid():
            # Check if video URL is being submitted for the first time
            video_url = request.data.get('verification_video_url')
            should_notify_admin = (
                video_url and
                video_url.strip() and
                not profile.verification_submitted_at
            )

            serializer.save()

            # Send admin notification if this is the first submission
            if should_notify_admin:
                try:
                    from .email_service import send_mentor_submission_email
                    send_mentor_submission_email(profile)
                except ImportError:
                    # Email service not yet available, skip
                    pass

            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MyAvailabilityRulesView(APIView):
    """Manage mentor's availability rules"""

    permission_classes = (permissions.IsAuthenticated, IsMentor)

    def get(self, request):
        profile = request.user.mentor_profile
        rules = MentorAvailabilityRule.objects.filter(mentor=profile, is_active=True)

        serializer = MentorAvailabilityRuleSerializer(rules, many=True)
        return Response(serializer.data)

    def post(self, request):
        profile = request.user.mentor_profile

        serializer = MentorAvailabilityRuleSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(mentor=profile)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        profile = request.user.mentor_profile

        try:
            rule = MentorAvailabilityRule.objects.get(id=id, mentor=profile)
            rule.is_active = False
            rule.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except MentorAvailabilityRule.DoesNotExist:
            return Response(
                {"error": "Rule not found"}, status=status.HTTP_404_NOT_FOUND
            )


# === Booking Endpoints ===


class MyBookingsView(APIView):
    """Get current user's bookings"""

    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        if hasattr(request.user, "mentor_profile"):
            # User is a mentor, show their bookings
            bookings = MentorBooking.objects.filter(mentor=request.user.mentor_profile)
        else:
            # User is a student, show their bookings
            bookings = MentorBooking.objects.filter(student=request.user)

        bookings = bookings.select_related("mentor", "student").order_by("-created_at")

        serializer = MentorBookingSerializer(bookings, many=True)
        return Response(serializer.data)


class ConfirmBookingView(APIView):
    """Confirm a booking (mentor only)"""

    permission_classes = (permissions.IsAuthenticated, IsBookingMentor)

    def post(self, request, id):
        try:
            booking = MentorBooking.objects.get(id=id)
        except MentorBooking.DoesNotExist:
            return Response(
                {"error": "Booking not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Check permission
        self.check_object_permissions(request, booking)

        if booking.status != "requested":
            return Response(
                {"error": "Booking can only be confirmed if status is requested"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        booking.status = "confirmed"
        booking.confirmed_at = timezone.now()
        booking.save()

        # Create Todo task for student
        from todos.models import Todo

        Todo.objects.create(
            user=booking.student,
            title=f"Mentor Session: {booking.mentor.title}",
            description=f"Session type: {booking.topic}\nNotes: {booking.student_notes}",
            task_type="mentor_session",
            scheduled_date=booking.start_at_utc.date(),
            timebox_minutes=booking.duration_minutes,
            status="ready",
            external_url=f"/mentors/bookings/{booking.id}",
            notes={"booking_id": booking.id, "mentor_id": booking.mentor.id},
        )

        # Send notification to student
        NotificationService.notify_booking_confirmed(booking)

        # Send confirmation email
        from .email_service import send_booking_confirmation_email
        send_booking_confirmation_email(booking)

        serializer = MentorBookingSerializer(booking)
        return Response(serializer.data)


class CancelBookingView(APIView):
    """Cancel a booking (mentor or student)"""

    permission_classes = (
        permissions.IsAuthenticated,
        IsBookingMentorOrStudentCanCancel,
    )

    def post(self, request, id):
        try:
            booking = MentorBooking.objects.get(id=id)
        except MentorBooking.DoesNotExist:
            return Response(
                {"error": "Booking not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Check permission
        self.check_object_permissions(request, booking)

        if booking.status in ["completed", "cancelled"]:
            return Response(
                {"error": "Cannot cancel a completed or cancelled booking"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        booking.status = "cancelled"
        booking.save()

        # Notify the other party
        NotificationService.notify_booking_cancelled(booking, request.user)

        # Send cancellation email
        from .email_service import send_booking_cancellation_email
        send_booking_cancellation_email(booking)

        serializer = MentorBookingSerializer(booking)
        return Response(serializer.data)


class CompleteBookingView(APIView):
    """Mark a booking as complete (mentor only)"""

    permission_classes = (permissions.IsAuthenticated, IsBookingMentor)

    def post(self, request, id):
        try:
            booking = MentorBooking.objects.get(id=id)
        except MentorBooking.DoesNotExist:
            return Response(
                {"error": "Booking not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Check permission
        self.check_object_permissions(request, booking)

        if booking.status != "confirmed":
            return Response(
                {"error": "Booking must be confirmed before completing"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        booking.status = "completed"
        booking.completed_at = timezone.now()
        booking.mentor_summary = request.data.get("mentor_summary", "")
        booking.action_items = request.data.get("action_items", [])
        booking.save()

        # Update mentor stats
        from .tasks import update_mentor_stats

        update_mentor_stats.delay(booking.mentor.id)

        # TODO: Prompt student for review
        # Could create a notification asking for review

        serializer = MentorBookingSerializer(booking)
        return Response(serializer.data)


# === Review Endpoints ===


class CreateReviewRequestView(APIView):
    """Create a review request (plan or essay)"""

    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        mentor_id = request.data.get("mentor_id")
        request_type = request.data.get("request_type")

        if not mentor_id or not request_type:
            return Response(
                {"error": "mentor_id and request_type are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            mentor = MentorProfile.objects.get(
                id=mentor_id, verification_status='approved', is_active=True
            )
        except MentorProfile.DoesNotExist:
            return Response(
                {"error": "Mentor not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Create review request
        data = {
            "mentor": mentor.id,
            "student": request.user.id,
            "request_type": request_type,
            "questions": request.data.get("questions", ""),
            "price_credits": request.data.get("price_credits", 0),
        }

        # Set goal_spec or essay_project based on request_type
        if request_type == "plan":
            goal_spec_id = request.data.get("goal_spec_id")
            if not goal_spec_id:
                return Response(
                    {"error": "goal_spec_id required for plan reviews"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            data["goal_spec"] = goal_spec_id
        elif request_type == "essay":
            essay_project_id = request.data.get("essay_project_id")
            if not essay_project_id:
                return Response(
                    {"error": "essay_project_id required for essay reviews"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            data["essay_project"] = essay_project_id
        else:
            return Response(
                {"error": 'Invalid request_type. Must be "plan" or "essay"'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = MentorReviewRequestSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            # TODO: Notify mentor
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MyReviewsView(APIView):
    """Get current user's review requests"""

    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        if hasattr(request.user, "mentor_profile"):
            # User is a mentor, show review requests for them
            reviews = MentorReviewRequest.objects.filter(
                mentor=request.user.mentor_profile
            )
        else:
            # User is a student, show their review requests
            reviews = MentorReviewRequest.objects.filter(student=request.user)

        reviews = reviews.select_related(
            "mentor", "student", "goal_spec", "essay_project"
        ).order_by("-created_at")

        serializer = MentorReviewRequestSerializer(reviews, many=True)
        return Response(serializer.data)


class ReviewDetailView(APIView):
    """Get review request details"""

    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, id):
        try:
            review = MentorReviewRequest.objects.get(id=id)
        except MentorReviewRequest.DoesNotExist:
            return Response(
                {"error": "Review request not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Check permission (mentor or student involved)
        if request.user != review.mentor.user and request.user != review.student:
            return Response(
                {"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
            )

        serializer = MentorReviewRequestSerializer(review)
        return Response(serializer.data)


class SubmitReviewResponseView(APIView):
    """Submit review response (mentor only)"""

    permission_classes = (permissions.IsAuthenticated, IsReviewRequestMentor)

    def post(self, request, id):
        try:
            review_request = MentorReviewRequest.objects.get(id=id)
        except MentorReviewRequest.DoesNotExist:
            return Response(
                {"error": "Review request not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Check permission
        self.check_object_permissions(request, review_request)

        if review_request.status != "pending":
            return Response(
                {"error": "Review request has already been responded to"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate based on request type
        if review_request.request_type == "plan":
            serializer = PlanReviewSubmissionSerializer(data=request.data)
        elif review_request.request_type == "essay":
            serializer = EssayReviewSubmissionSerializer(data=request.data)
        else:
            return Response(
                {"error": "Invalid request type"}, status=status.HTTP_400_BAD_REQUEST
            )

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Normalize and save response
        if review_request.request_type == "plan":
            payload = {
                "verdict": serializer.validated_data["verdict"],
                "top_risks": serializer.validated_data.get("top_risks", []),
                "next_steps": serializer.validated_data.get("next_steps", []),
                "suggestions": SuggestionNormalizationService.normalize_plan_suggestions(
                    serializer.validated_data.get("suggestions", [])
                ),
            }
        else:  # essay
            payload = SuggestionNormalizationService.normalize_essay_feedback(
                serializer.validated_data.get("strengths", []),
                serializer.validated_data.get("improvements", []),
                serializer.validated_data.get("rewrite_suggestions", []),
                serializer.validated_data.get("scores", {}),
            )

        response = MentorReviewResponse.objects.create(
            request=review_request,
            overall_comment=serializer.validated_data["overall_comment"],
            payload_json=payload,
        )

        review_request.status = "done"
        review_request.responded_at = timezone.now()
        review_request.save()

        # Notify student
        NotificationService.notify_review_ready(review_request)

        response_serializer = MentorReviewResponseSerializer(response)
        return Response(response_serializer.data)


class ApplyReviewSuggestionsView(APIView):
    """Apply mentor suggestions to tasks (student only)"""

    permission_classes = (permissions.IsAuthenticated, IsReviewRequestStudent)

    def post(self, request, id):
        try:
            review_request = MentorReviewRequest.objects.get(id=id)
        except MentorReviewRequest.DoesNotExist:
            return Response(
                {"error": "Review request not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Check permission
        self.check_object_permissions(request, review_request)

        if review_request.request_type != "plan":
            return Response(
                {"error": "Suggestions can only be applied to plan reviews"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Apply suggestions
        result = SuggestionApplicationService.apply_suggestions(
            review_request, request.user
        )

        return Response(result)


# === Flagging and Reinstatement Endpoints ===


class FlagMentorView(APIView):
    """Flag a mentor for review (student only)"""

    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, mentor_id):
        """Flag a mentor due to issues"""
        reason = request.data.get('reason', '')
        booking_id = request.data.get('booking_id')

        if not reason:
            return Response(
                {'error': 'Reason is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            mentor = MentorProfile.objects.get(id=mentor_id)
        except MentorProfile.DoesNotExist:
            return Response(
                {'error': 'Mentor not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Increment flag count
        mentor.flag_count += 1
        mentor.flagged_at = timezone.now()

        FLAG_THRESHOLD = 3

        # Auto-suspend if threshold reached
        if mentor.flag_count >= FLAG_THRESHOLD:
            mentor.verification_status = 'suspended'
            mentor.is_active = False
            mentor.verification_notes = f'Auto-suspended after {mentor.flag_count} flags'

            # Send suspension email
            try:
                from .email_service import send_mentor_suspension_email
                send_mentor_suspension_email(mentor, reason)
            except ImportError:
                pass

        mentor.save()

        # Flag the booking if provided
        if booking_id:
            MentorBooking.objects.filter(id=booking_id).update(
                is_flagged=True,
                flag_reason=reason,
                flagged_at=timezone.now()
            )

        # Notify admins
        try:
            from users.models import User
            admin_users = User.objects.filter(is_staff=True, is_active=True).first()
            if admin_users:
                from notifications.service import NotificationService
                NotificationService.create_notification(
                    recipient=admin_users,
                    notification_type='mentor_flagged',
                    title=f'Mentor Flagged: {mentor.title}',
                    message=f'Mentor has been flagged ({mentor.flag_count} total)',
                    data={'mentor_id': mentor.id, 'reason': reason}
                )
        except Exception:
            # Notification system might not be configured, skip
            pass

        response_data = {
            'message': 'Mentor flagged successfully',
            'flag_count': mentor.flag_count,
            'status': mentor.verification_status
        }

        # Auto-suspension message
        if mentor.flag_count >= FLAG_THRESHOLD:
            response_data['auto_suspended'] = True

        return Response(response_data)


class ReinstatementRequestView(APIView):
    """Request reinstatement for suspended mentors"""

    permission_classes = (permissions.IsAuthenticated, IsMentor)

    def post(self, request):
        """Submit reinstatement request"""
        mentor = request.user.mentor_profile

        if mentor.verification_status != 'suspended':
            return Response(
                {'error': 'Only suspended mentors can request reinstatement'},
                status=status.HTTP_400_BAD_REQUEST
            )

        explanation = request.data.get('explanation', '')

        if not explanation:
            return Response(
                {'error': 'Explanation is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Add explanation to notes and reset to pending
        mentor.verification_notes += f'\n\nReinstatement Request:\n{explanation}'
        mentor.verification_status = 'pending'
        mentor.save()

        # Notify admins
        try:
            from users.models import User
            admin_users = User.objects.filter(is_staff=True, is_active=True).first()
            if admin_users:
                from notifications.service import NotificationService
                NotificationService.create_notification(
                    recipient=admin_users,
                    notification_type='mentor_reinstatement',
                    title=f'Reinstatement Request: {mentor.title}',
                    message=f'Suspended mentor has requested reinstatement',
                    data={'mentor_id': mentor.id}
                )
        except Exception:
            # Notification system might not be configured, skip
            pass

        return Response({
            'message': 'Reinstatement request submitted',
            'status': 'pending'
        })

