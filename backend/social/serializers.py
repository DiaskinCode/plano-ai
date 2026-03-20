"""
Social Serializers - College Application Platform

Serializers for user profiles, following, and messaging
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import Follow, DirectMessage, BlockedUser

User = get_user_model()


class UserProfileSerializer(serializers.ModelSerializer):
    """Lightweight serializer for user profile in social contexts"""
    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'username',
        ]


class PublicProfileSerializer(serializers.ModelSerializer):
    """
    Public user profile with privacy-respecting fields
    Used for viewing other users' profiles
    """
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    avatar_url = serializers.CharField(source='profile.avatar_url', read_only=True)
    bio = serializers.CharField(source='profile.bio', read_only=True)
    location = serializers.CharField(source='profile.location', read_only=True)
    target_universities = serializers.JSONField(source='profile.target_universities', read_only=True)
    follower_count = serializers.IntegerField(source='profile.follower_count', read_only=True)
    following_count = serializers.IntegerField(source='profile.following_count', read_only=True)
    post_count = serializers.IntegerField(source='profile.post_count', read_only=True)

    # Academic stats (conditionally included based on privacy)
    gpa = serializers.DecimalField(
        source='profile.gpa_public',
        max_digits=3,
        decimal_places=2,
        read_only=True,
        allow_null=True
    )
    sat_score = serializers.IntegerField(
        source='profile.sat_score_public',
        read_only=True,
        allow_null=True
    )
    ielts_score = serializers.DecimalField(
        source='profile.ielts_score_public',
        max_digits=3,
        decimal_places=1,
        read_only=True,
        allow_null=True
    )

    # Privacy settings
    stats_visibility = serializers.CharField(
        source='profile.stats_visibility',
        read_only=True
    )
    activity_visibility = serializers.CharField(
        source='profile.activity_visibility',
        read_only=True
    )

    # Follow status for current user
    is_following = serializers.SerializerMethodField()
    is_followed_by = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'avatar_url',
            'bio',
            'location',
            'target_universities',
            'follower_count',
            'following_count',
            'post_count',
            'gpa',
            'sat_score',
            'ielts_score',
            'stats_visibility',
            'activity_visibility',
            'is_following',
            'is_followed_by',
        ]

    def get_is_following(self, obj):
        """Check if current user is following this user"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Follow.objects.filter(
                follower=request.user,
                following=obj
            ).exists()
        return False

    def get_is_followed_by(self, obj):
        """Check if this user is following current user"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Follow.objects.filter(
                follower=obj,
                following=request.user
            ).exists()
        return False


class OwnProfileSerializer(serializers.ModelSerializer):
    """
    Full profile for viewing/editing own profile
    Includes all fields including private ones
    """
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)

    # Profile fields
    name = serializers.CharField(source='profile.name', required=False)
    bio = serializers.CharField(source='profile.bio', required=False, allow_blank=True)
    location = serializers.CharField(source='profile.location', required=False, allow_blank=True)
    avatar_url = serializers.URLField(source='profile.avatar_url', required=False, allow_blank=True)
    target_universities = serializers.JSONField(source='profile.target_universities', required=False)

    # Academic stats (public versions)
    gpa_public = serializers.DecimalField(
        source='profile.gpa_public',
        max_digits=3,
        decimal_places=2,
        required=False,
        allow_null=True
    )
    sat_score_public = serializers.IntegerField(
        source='profile.sat_score_public',
        required=False,
        allow_null=True
    )
    ielts_score_public = serializers.DecimalField(
        source='profile.ielts_score_public',
        max_digits=3,
        decimal_places=1,
        required=False,
        allow_null=True
    )

    # Privacy settings
    stats_visibility = serializers.CharField(
        source='profile.stats_visibility',
        required=False
    )
    message_privacy = serializers.CharField(
        source='profile.message_privacy',
        required=False
    )
    activity_visibility = serializers.CharField(
        source='profile.activity_visibility',
        required=False
    )

    # Social stats (read-only)
    follower_count = serializers.IntegerField(source='profile.follower_count', read_only=True)
    following_count = serializers.IntegerField(source='profile.following_count', read_only=True)
    post_count = serializers.IntegerField(source='profile.post_count', read_only=True)
    total_likes = serializers.IntegerField(source='profile.total_likes', read_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'name',
            'bio',
            'location',
            'avatar_url',
            'target_universities',
            'gpa_public',
            'sat_score_public',
            'ielts_score_public',
            'stats_visibility',
            'message_privacy',
            'activity_visibility',
            'follower_count',
            'following_count',
            'post_count',
            'total_likes',
        ]


class FollowSerializer(serializers.ModelSerializer):
    """Serializer for follow relationships"""
    follower_username = serializers.CharField(source='follower.username', read_only=True)
    following_username = serializers.CharField(source='following.username', read_only=True)
    follower_avatar = serializers.CharField(source='follower.profile.avatar_url', read_only=True)
    following_avatar = serializers.CharField(source='following.profile.avatar_url', read_only=True)

    class Meta:
        model = Follow
        fields = [
            'id',
            'follower',
            'following',
            'follower_username',
            'following_username',
            'follower_avatar',
            'following_avatar',
            'created_at',
        ]
        read_only_fields = ['created_at']


class DirectMessageSerializer(serializers.ModelSerializer):
    """Serializer for direct messages"""
    sender_username = serializers.CharField(source='sender.username', read_only=True)
    sender_avatar = serializers.CharField(source='sender.profile.avatar_url', read_only=True)
    recipient_username = serializers.CharField(source='recipient.username', read_only=True)
    recipient_avatar = serializers.CharField(source='recipient.profile.avatar_url', read_only=True)

    class Meta:
        model = DirectMessage
        fields = [
            'id',
            'sender',
            'recipient',
            'sender_username',
            'sender_avatar',
            'recipient_username',
            'recipient_avatar',
            'content',
            'attachments',
            'is_read',
            'read_at',
            'reply_to',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['is_read', 'read_at', 'created_at', 'updated_at']


class DirectMessageCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new messages"""
    class Meta:
        model = DirectMessage
        fields = [
            'recipient',
            'content',
            'attachments',
            'reply_to',
        ]

    def validate_recipient(self, value):
        """Validate recipient and privacy settings"""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError("Authentication required")

        # Can't message yourself
        if value == request.user:
            raise serializers.ValidationError("Cannot send message to yourself")

        # Check if blocked
        if BlockedUser.objects.filter(blocker=value, blocked=request.user).exists():
            raise serializers.ValidationError("You are blocked by this user")

        if BlockedUser.objects.filter(blocker=request.user, blocked=value).exists():
            raise serializers.ValidationError("You have blocked this user")

        # Check privacy settings
        recipient_profile = value.profile
        if recipient_profile.message_privacy == 'everyone':
            return value

        if recipient_profile.message_privacy == 'followers':
            is_follower = Follow.objects.filter(
                follower=request.user,
                following=value
            ).exists()
            if not is_follower:
                raise serializers.ValidationError("You must follow this user to send messages")

        if recipient_profile.message_privacy == 'following':
            is_following = Follow.objects.filter(
                follower=value,
                following=request.user
            ).exists()
            if not is_following:
                raise serializers.ValidationError("This user only accepts messages from people they follow")

        return value


class BlockedUserSerializer(serializers.ModelSerializer):
    """Serializer for blocked users"""
    blocked_username = serializers.CharField(source='blocked.username', read_only=True)
    blocked_avatar = serializers.CharField(source='blocked.profile.avatar_url', read_only=True)

    class Meta:
        model = BlockedUser
        fields = [
            'id',
            'blocked',
            'blocked_username',
            'blocked_avatar',
            'reason',
            'created_at',
        ]
        read_only_fields = ['created_at']


class UserSearchSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for user search results
    """
    username = serializers.CharField(read_only=True)
    avatar_url = serializers.CharField(source='profile.avatar_url', read_only=True)
    bio = serializers.CharField(source='profile.bio', read_only=True)
    location = serializers.CharField(source='profile.location', read_only=True)
    follower_count = serializers.IntegerField(source='profile.follower_count', read_only=True)

    # Target schools (for filtering)
    target_universities = serializers.JSONField(source='profile.target_universities', read_only=True)

    is_following = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'avatar_url',
            'bio',
            'location',
            'follower_count',
            'target_universities',
            'is_following',
        ]

    def get_is_following(self, obj):
        """Check if current user is following this user"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Follow.objects.filter(
                follower=request.user,
                following=obj
            ).exists()
        return False
