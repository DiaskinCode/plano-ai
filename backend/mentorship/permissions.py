from rest_framework import permissions


class IsMentor(permissions.BasePermission):
    """User has a mentor profile (verified or not)"""

    def has_permission(self, request, view):
        return hasattr(request.user, "mentor_profile")


class IsVerifiedMentor(permissions.BasePermission):
    """Only verified mentors appear in public listings and can be booked"""

    def has_permission(self, request, view):
        return (
            hasattr(request.user, "mentor_profile")
            and request.user.mentor_profile.is_verified
        )


class IsBookingMentorOrStudent(permissions.BasePermission):
    """Only the mentor or student involved can access the booking"""

    def has_object_permission(self, request, view, obj):
        return request.user == obj.mentor.user or request.user == obj.student


class IsBookingMentor(permissions.BasePermission):
    """Only the booking's mentor can perform action"""

    def has_object_permission(self, request, view, obj):
        return request.user == obj.mentor.user


class IsBookingStudent(permissions.BasePermission):
    """Only the booking's student can perform action"""

    def has_object_permission(self, request, view, obj):
        return request.user == obj.student


class IsBookingMentorOrStudentCanCancel(permissions.BasePermission):
    """Either party can cancel (mentors need this for no-shows/emergencies)"""

    def has_object_permission(self, request, view, obj):
        return request.user == obj.mentor.user or request.user == obj.student


class IsReviewRequestMentor(permissions.BasePermission):
    """Only the review's assigned mentor can submit response"""

    def has_object_permission(self, request, view, obj):
        return request.user == obj.mentor.user


class IsReviewRequestStudent(permissions.BasePermission):
    """Only the review's student can apply suggestions"""

    def has_object_permission(self, request, view, obj):
        return request.user == obj.student
