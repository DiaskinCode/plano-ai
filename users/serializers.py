from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User, UserProfile, OnboardingProgress, OnboardingChatData


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    timezone = serializers.CharField(required=False, default='UTC')

    class Meta:
        model = User
        fields = ('email', 'username', 'password', 'password2', 'timezone')

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password']
        )
        # Create empty profile
        UserProfile.objects.create(user=user, name=validated_data.get('username', ''))
        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'is_active', 'created_at', 'timezone')
        read_only_fields = ('id', 'created_at')


class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = UserProfile
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')


class OnboardingSerializer(serializers.ModelSerializer):
    """Serializer for completing onboarding with rich profile data"""
    class Meta:
        model = UserProfile
        fields = (
            'name', 'age', 'country_of_residence',
            'current_situation', 'future_goals', 'dream_career',
            'budget_range', 'target_timeline',
            'coach_character', 'energy_peak', 'notification_tone', 'check_in_time',
            'languages', 'destinations', 'network', 'constraints',
            # Domain-specific assessment fields
            'gpa', 'test_scores', 'field_of_study', 'prior_education',
            'years_of_experience', 'current_role', 'companies_worked', 'skills', 'referral_network_size',
            # NEW: Role-specific career fields for hyper-personalization
            'career_specialization', 'tech_stack', 'experience_level', 'target_company_types',
            'notable_projects', 'current_company',
            'design_discipline', 'design_tools', 'design_specialization', 'portfolio_quality',
            # Fitness
            'fitness_level', 'injuries_limitations', 'gym_access', 'workout_history'
        )

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.onboarding_completed = True
        instance.save()
        return instance


class OnboardingProgressSerializer(serializers.ModelSerializer):
    """Serializer for tracking multi-category onboarding progress"""
    class Meta:
        model = OnboardingProgress
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'completed_at')


class OnboardingChatDataSerializer(serializers.ModelSerializer):
    """Serializer for temporary onboarding chat data storage"""
    class Meta:
        model = OnboardingChatData
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')
