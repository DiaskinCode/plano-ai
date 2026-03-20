from rest_framework import serializers

from .models import University


class UniversitySerializer(serializers.ModelSerializer):
    """Serializer for University model with all fields including images"""

    class Meta:
        model = University
        fields = "__all__"  # Includes the new logo_url and campus_photo_url fields
