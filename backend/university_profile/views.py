from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import UniversitySeekerProfile, ExtracurricularActivity
from .serializers import (
    UniversitySeekerProfileSerializer,
    UniversitySeekerProfileCreateSerializer,
    UniversitySeekerProfileUpdateSerializer,
    ExtracurricularActivitySerializer
)


class UniversityProfileView(generics.RetrieveUpdateAPIView):
    """
    Get or update the authenticated user's university profile.
    """
    serializer_class = UniversitySeekerProfileSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        """Get profile with proper handling of missing profile"""
        try:
            profile = UniversitySeekerProfile.objects.get(user=request.user)
            serializer = self.get_serializer(profile)
            return Response(serializer.data)
        except UniversitySeekerProfile.DoesNotExist:
            return Response(
                {'error': 'No profile found. Please create a profile first.'},
                status=status.HTTP_404_NOT_FOUND
            )

    def put(self, request, *args, **kwargs):
        """Update profile with proper handling of missing profile"""
        try:
            profile = UniversitySeekerProfile.objects.get(user=request.user)
            serializer = self.get_serializer(profile, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        except UniversitySeekerProfile.DoesNotExist:
            return Response(
                {'error': 'No profile found. Please create a profile first.'},
                status=status.HTTP_404_NOT_FOUND
            )

    def patch(self, request, *args, **kwargs):
        """Partial update with proper handling of missing profile"""
        try:
            profile = UniversitySeekerProfile.objects.get(user=request.user)
            serializer = self.get_serializer(profile, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        except UniversitySeekerProfile.DoesNotExist:
            return Response(
                {'error': 'No profile found. Please create a profile first.'},
                status=status.HTTP_404_NOT_FOUND
            )

    def get_object(self):
        """Get profile for the authenticated user, or return None if not exists"""
        try:
            return UniversitySeekerProfile.objects.get(user=self.request.user)
        except UniversitySeekerProfile.DoesNotExist:
            # Return None instead of auto-creating (required fields would fail)
            return None

    def get_serializer_class(self):
        """Use different serializers for GET vs PUT/PATCH"""
        if self.request.method in ['PUT', 'PATCH']:
            return UniversitySeekerProfileUpdateSerializer
        return UniversitySeekerProfileSerializer


class UniversityProfileCreateView(generics.CreateAPIView):
    """
    Create a new university profile for the authenticated user.
    """
    serializer_class = UniversitySeekerProfileCreateSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def perform_create(self, serializer):
        """Associate profile with the authenticated user"""
        serializer.save(user=self.request.user)


class UniversityProfileDeleteView(generics.DestroyAPIView):
    """
    Delete the authenticated user's university profile.
    """
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        """Get the user's profile"""
        try:
            return UniversitySeekerProfile.objects.get(user=self.request.user)
        except UniversitySeekerProfile.DoesNotExist:
            return None

    def delete(self, request, *args, **kwargs):
        """Delete the profile if it exists"""
        profile = self.get_object()
        if profile:
            profile.delete()
            return Response({'message': 'Profile deleted successfully'}, status=status.HTTP_200_OK)
        return Response({'error': 'No profile found'}, status=status.HTTP_404_NOT_FOUND)


class ExtracurricularActivityListView(generics.ListCreateAPIView):
    """
    List and create extracurricular activities for the user's profile.
    """
    serializer_class = ExtracurricularActivitySerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        """Get activities for the user's profile"""
        try:
            profile = UniversitySeekerProfile.objects.get(user=self.request.user)
            return profile.extracurriculars.all()
        except UniversitySeekerProfile.DoesNotExist:
            return ExtracurricularActivity.objects.none()

    def perform_create(self, serializer):
        """Associate activity with the user's profile"""
        try:
            profile = UniversitySeekerProfile.objects.get(user=self.request.user)
            serializer.save(profile=profile)
        except UniversitySeekerProfile.DoesNotExist:
            from rest_framework.exceptions import ValidationError
            raise ValidationError('No university profile found. Please create a profile first.')


class ExtracurricularActivityDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a specific extracurricular activity.
    """
    serializer_class = ExtracurricularActivitySerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        """Get activities for the user's profile"""
        try:
            profile = UniversitySeekerProfile.objects.get(user=self.request.user)
            return profile.extracurriculars.all()
        except UniversitySeekerProfile.DoesNotExist:
            return ExtracurricularActivity.objects.none()


class ProfileCompletionView(APIView):
    """
    Get profile completion status and recommendations.
    """
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        """Get completion percentage and missing required fields"""
        try:
            profile = UniversitySeekerProfile.objects.get(user=request.user)
            completion = profile.completion_percentage

            # Identify missing fields
            missing_required = []
            missing_optional = []

            # Required fields
            if not profile.gpa:
                missing_required.append('gpa')
            if not profile.country:
                missing_required.append('country')
            if not profile.citizenship:
                missing_required.append('citizenship')
            if not profile.intended_major_1:
                missing_required.append('intended_major_1')

            # Optional fields (that improve recommendations)
            if not profile.sat_score and not profile.act_score:
                missing_optional.append('test_scores')
            if not profile.course_rigor or profile.course_rigor == 'regular':
                missing_optional.append('course_rigor')
            if not profile.financial_need or profile.financial_need == 'none':
                missing_optional.append('financial_need')
            if not profile.preferred_size:
                missing_optional.append('preferred_size')
            if not profile.preferred_location:
                missing_optional.append('preferred_location')

            return Response({
                'completion_percentage': completion,
                'missing_required': missing_required,
                'missing_optional': missing_optional,
                'recommendation': self._get_completion_recommendation(completion)
            })

        except UniversitySeekerProfile.DoesNotExist:
            return Response({
                'completion_percentage': 0,
                'missing_required': ['gpa', 'country', 'citizenship', 'intended_major_1'],
                'missing_optional': [],
                'recommendation': 'Please create a profile to get started'
            })

    def _get_completion_recommendation(self, completion):
        """Get recommendation based on completion percentage"""
        if completion < 40:
            return "Complete required fields to enable basic recommendations"
        elif completion < 70:
            return "Add optional fields to improve recommendation quality"
        elif completion < 100:
            return "Almost there! Add remaining fields for the best results"
        else:
            return "Profile complete! You can now get personalized recommendations"
