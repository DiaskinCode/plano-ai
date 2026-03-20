from django.urls import path

from . import views

urlpatterns = [
    # === Public endpoints (students browsing mentors) ===
    path("mentors/", views.MentorListView.as_view(), name="mentor-list"),
    path("mentors/<int:id>/", views.MentorDetailView.as_view(), name="mentor-detail"),
    path(
        "mentors/<int:id>/availability/",
        views.MentorAvailabilityView.as_view(),
        name="mentor-availability",
    ),
    path(
        "mentors/<int:id>/book/",
        views.BookSessionView.as_view(),
        name="mentor-book",
    ),
    # === Mentor self-service endpoints (mentors only, verified or not) ===
    path("mentors/me/", views.MyMentorProfileView.as_view(), name="my-mentor-profile"),
    path(
        "mentors/me/availability/",
        views.MyAvailabilityRulesView.as_view(),
        name="my-availability-rules",
    ),
    path(
        "mentors/me/availability/<int:id>/",
        views.MyAvailabilityRulesView.as_view(),
        name="my-availability-rule-detail",
    ),
    # === Bookings ===
    path("mentorship/bookings/", views.MyBookingsView.as_view(), name="my-bookings"),
    path(
        "mentorship/bookings/<int:id>/confirm/",
        views.ConfirmBookingView.as_view(),
        name="confirm-booking",
    ),
    path(
        "mentorship/bookings/<int:id>/cancel/",
        views.CancelBookingView.as_view(),
        name="cancel-booking",
    ),
    path(
        "mentorship/bookings/<int:id>/complete/",
        views.CompleteBookingView.as_view(),
        name="complete-booking",
    ),
    # === Reviews (unified plan + essay) ===
    path(
        "mentorship/reviews/request/",
        views.CreateReviewRequestView.as_view(),
        name="create-review-request",
    ),
    path("mentorship/reviews/", views.MyReviewsView.as_view(), name="my-reviews"),
    path(
        "mentorship/reviews/<int:id>/",
        views.ReviewDetailView.as_view(),
        name="review-detail",
    ),
    path(
        "mentorship/reviews/<int:id>/submit/",
        views.SubmitReviewResponseView.as_view(),
        name="submit-review-response",
    ),
    path(
        "mentorship/reviews/<int:id>/apply/",
        views.ApplyReviewSuggestionsView.as_view(),
        name="apply-review-suggestions",
    ),
    # === Flagging and Reinstatement ===
    path(
        "mentors/<int:mentor_id>/flag/",
        views.FlagMentorView.as_view(),
        name="flag-mentor",
    ),
    path(
        "mentors/me/reinstate/",
        views.ReinstatementRequestView.as_view(),
        name="request-reinstatement",
    ),
]
