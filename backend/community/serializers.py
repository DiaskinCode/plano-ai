"""
Community Serializers - College Application Platform

Serializers for community, posts, comments, voting
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import Community, CommunityMember, Post, Comment, PostVote, CommentVote

User = get_user_model()


class CommunityListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for community lists"""
    member_count_display = serializers.SerializerMethodField()

    class Meta:
        model = Community
        fields = [
            'id',
            'name',
            'slug',
            'icon',
            'banner_color',
            'description',
            'community_type',
            'member_count_display',
            'is_official',
        ]

    def get_member_count_display(self, obj):
        """Format member count (e.g., 12.5k)"""
        count = obj.member_count
        if count >= 1000:
            return f"{count / 1000:.1f}k"
        return str(count)


class CommunityDetailSerializer(serializers.ModelSerializer):
    """Full serializer for community detail view"""
    is_member = serializers.SerializerMethodField()
    user_role = serializers.SerializerMethodField()

    class Meta:
        model = Community
        fields = [
            'id',
            'name',
            'slug',
            'description',
            'community_type',
            'icon',
            'banner_color',
            'rules',
            'member_count',
            'online_count',
            'post_count',
            'is_official',
            'tags',
            'is_member',
            'user_role',
        ]
        read_only_fields = ['member_count', 'online_count', 'post_count']

    def get_is_member(self, obj):
        """Check if current user is a member"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return CommunityMember.objects.filter(
                user=request.user,
                community=obj
            ).exists()
        return False

    def get_user_role(self, obj):
        """Get user's role in this community"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            membership = CommunityMember.objects.filter(
                user=request.user,
                community=obj
            ).first()
            return membership.role if membership else None
        return None


class CommunityMemberSerializer(serializers.ModelSerializer):
    """Serializer for community membership"""
    user_display = serializers.SerializerMethodField()
    community_name = serializers.SerializerMethodField()

    class Meta:
        model = CommunityMember
        fields = [
            'id',
            'user',
            'user_display',
            'community',
            'community_name',
            'role',
            'display_name',
            'joined_at',
            'post_count',
            'comment_count',
        ]
        read_only_fields = ['joined_at', 'post_count', 'comment_count']

    def get_user_display(self, obj):
        """Get user's display name"""
        return obj.user.get_full_name() or obj.user.email

    def get_community_name(self, obj):
        """Get community name"""
        return obj.community.name


class PostListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for post lists"""
    author = serializers.SerializerMethodField()
    author_avatar = serializers.SerializerMethodField()
    community_name = serializers.SerializerMethodField()
    community_icon = serializers.SerializerMethodField()
    score = serializers.ReadOnlyField()
    time_since_posted = serializers.SerializerMethodField()
    user_vote = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'id',
            'title',
            'flair',
            'author',
            'author_avatar',
            'community_name',
            'community_icon',
            'score',
            'upvotes',
            'downvotes',
            'comment_count',
            'view_count',
            'is_pinned',
            'time_since_posted',
            'user_vote',
        ]

    def get_author(self, obj):
        """Get author username"""
        return obj.user.username

    def get_author_avatar(self, obj):
        """Get author avatar URL"""
        profile = getattr(obj.user, 'profile', None)
        if profile:
            return profile.avatar_url
        return None

    def get_community_name(self, obj):
        """Get community name"""
        return obj.community.name

    def get_community_icon(self, obj):
        """Get community icon"""
        return obj.community.icon

    def get_time_since_posted(self, obj):
        """Get human-readable time since posted"""
        from django.utils import timesince
        return timesince.timesince(obj.created_at)

    def get_user_vote(self, obj):
        """Get current user's vote on this post"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            vote = PostVote.objects.filter(
                user=request.user,
                post=obj
            ).first()
            return vote.vote_type if vote else None
        return None


class PostDetailSerializer(serializers.ModelSerializer):
    """Full serializer for post detail view"""
    author = serializers.SerializerMethodField()
    author_avatar = serializers.SerializerMethodField()
    author_joined_date = serializers.SerializerMethodField()
    community = CommunityListSerializer(read_only=True)
    score = serializers.ReadOnlyField()
    time_since_posted = serializers.SerializerMethodField()
    user_vote = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'id',
            'title',
            'content',
            'flair',
            'images',
            'files',
            'author',
            'author_avatar',
            'author_joined_date',
            'community',
            'score',
            'upvotes',
            'downvotes',
            'comment_count',
            'view_count',
            'is_pinned',
            'is_locked',
            'time_since_posted',
            'user_vote',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'upvotes',
            'downvotes',
            'comment_count',
            'view_count',
            'is_pinned',
            'created_at',
            'updated_at',
        ]

    def get_author(self, obj):
        """Get author username"""
        return obj.user.username

    def get_author_avatar(self, obj):
        """Get author avatar URL"""
        profile = getattr(obj.user, 'profile', None)
        if profile:
            return profile.avatar_url
        return None

    def get_author_joined_date(self, obj):
        """Get author joined date"""
        profile = getattr(obj.user, 'profile', None)
        if profile:
            return profile.created_at
        return None

    def get_time_since_posted(self, obj):
        """Get human-readable time since posted"""
        from django.utils import timesince
        return timesince.timesince(obj.created_at)

    def get_user_vote(self, obj):
        """Get current user's vote on this post"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            vote = PostVote.objects.filter(
                user=request.user,
                post=obj
            ).first()
            return vote.vote_type if vote else None
        return None


class CommentSerializer(serializers.ModelSerializer):
    """Serializer for comments"""
    author = serializers.SerializerMethodField()
    author_avatar = serializers.SerializerMethodField()
    score = serializers.ReadOnlyField()
    time_since_posted = serializers.SerializerMethodField()
    user_vote = serializers.SerializerMethodField()
    reply_count = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            'id',
            'post',
            'parent_comment',
            'content',
            'author',
            'author_avatar',
            'score',
            'upvotes',
            'downvotes',
            'time_since_posted',
            'user_vote',
            'reply_count',
            'is_edited',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['upvotes', 'downvotes', 'created_at', 'updated_at']

    def get_author(self, obj):
        """Get author username"""
        return obj.user.username

    def get_author_avatar(self, obj):
        """Get author avatar URL"""
        profile = getattr(obj.user, 'profile', None)
        if profile:
            return profile.avatar_url
        return None

    def get_time_since_posted(self, obj):
        """Get human-readable time since posted"""
        from django.utils import timesince
        return timesince.timesince(obj.created_at)

    def get_user_vote(self, obj):
        """Get current user's vote on this comment"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            vote = CommentVote.objects.filter(
                user=request.user,
                comment=obj
            ).first()
            return vote.vote_type if vote else None
        return None

    def get_reply_count(self, obj):
        """Get number of replies to this comment"""
        return obj.replies.count()


class CommentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating comments"""

    class Meta:
        model = Comment
        fields = [
            'post',
            'parent_comment',
            'content',
        ]


class PostCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating posts"""

    class Meta:
        model = Post
        fields = [
            'community',
            'title',
            'content',
            'flair',
            'images',
            'files',
        ]

    def validate_community(self, value):
        """Validate user is a member of the community"""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError("Authentication required")

        # Check if user is a member
        is_member = CommunityMember.objects.filter(
            user=request.user,
            community=value
        ).exists()

        if not is_member:
            raise serializers.ValidationError("You must join this community before posting")

        return value


class CommunityJoinSerializer(serializers.Serializer):
    """Serializer for joining/leaving communities"""
    pass
