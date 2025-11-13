from rest_framework import serializers
from .goalspec_models import GoalSpec


class GoalSpecSerializer(serializers.ModelSerializer):
    """
    Serializer for GoalSpec model with all fields
    """
    class Meta:
        model = GoalSpec
        fields = [
            'id',
            'user',
            'category',
            'goal_type',
            'title',
            'description',
            'target_date',
            'specifications',
            'permissions',
            'quick_wins',
            'status',
            'constraints',
            'preferences',
            'assets',
            'timeline',
            'priority_weight',
            'daily_time_budget_minutes',
            'cadence_rules',
            'is_active',
            'completed',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']

    def validate_priority_weight(self, value):
        """Ensure priority weight is between 0.1 and 1.0"""
        if not (0.1 <= value <= 1.0):
            raise serializers.ValidationError("Priority weight must be between 0.1 and 1.0")
        return value

    def validate_daily_time_budget_minutes(self, value):
        """Ensure daily time budget is positive"""
        if value <= 0:
            raise serializers.ValidationError("Daily time budget must be positive")
        return value

    def validate(self, data):
        """Validate goal-specific constraints and specifications"""
        goal_type = data.get('goal_type') or data.get('category')

        # Check specifications first (new onboarding), then constraints (legacy)
        specs = data.get('specifications', {})
        constraints = data.get('constraints', {})
        combined = {**constraints, **specs}  # Specs override constraints

        # Skip validation if both are empty (optional fields)
        if not combined:
            return data

        if goal_type == 'study':
            # Check in either specifications or constraints
            required_fields = ['country', 'degree']
            missing = [field for field in required_fields if field not in combined]
            if missing:
                # Only raise error if we have some data but missing required fields
                if combined:
                    raise serializers.ValidationError({
                        'specifications': f"Study goals require: {', '.join(missing)}"
                    })

        elif goal_type == 'career':
            if combined and 'targetRole' not in combined and 'target_role' not in combined:
                raise serializers.ValidationError({
                    'specifications': "Career goals require 'targetRole' in specifications"
                })

        elif goal_type == 'sport':
            if combined and 'sportType' not in combined and 'sport_type' not in combined:
                raise serializers.ValidationError({
                    'specifications': "Sport goals require 'sportType' in specifications"
                })

        return data


class GoalSpecCreateSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for creating GoalSpec (used during onboarding)
    """
    class Meta:
        model = GoalSpec
        fields = [
            'category',
            'goal_type',
            'title',
            'description',
            'target_date',
            'specifications',
            'permissions',
            'quick_wins',
            'status',
            'constraints',
            'preferences',
            'assets',
            'timeline',
            'priority_weight',
            'daily_time_budget_minutes',
            'cadence_rules'
        ]

    def create(self, validated_data):
        # Add user from request context
        validated_data['user'] = self.context['request'].user
        validated_data['is_active'] = True

        # Sync goal_type with category if not provided
        if 'category' in validated_data and 'goal_type' not in validated_data:
            validated_data['goal_type'] = validated_data['category']

        return super().create(validated_data)


class GoalSpecListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for listing goals
    """
    class Meta:
        model = GoalSpec
        fields = [
            'id',
            'goal_type',
            'title',
            'priority_weight',
            'daily_time_budget_minutes',
            'is_active',
            'completed'
        ]
