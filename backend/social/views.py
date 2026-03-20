"""
Social API Views - College Application Platform

Endpoints for:
- User profiles (view, edit)
- Follow/unfollow
- User search
- Direct messaging
- Block/unblock
"""

from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, F, Count
from django.utils import timezone

from .models import Follow, DirectMessage, BlockedUser
from .serializers import (
    PublicProfileSerializer,
    OwnProfileSerializer,
    FollowSerializer,
    DirectMessageSerializer,
    DirectMessageCreateSerializer,
    BlockedUserSerializer,
    UserSearchSerializer,
)
from django.contrib.auth import get_user_model

User = get_user_model()


class UserProfileViewSet(viewsets.ViewSet):
    """
    ViewSet for user profiles
    """
    permission_classes = (permissions.IsAuthenticated,)

    def retrieve(self, request, pk=None):
        """Get public profile by user ID"""
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response(
                {'detail': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = PublicProfileSerializer(user, context={'request': request})
        return Response(serializer.data)

    def list(self, request):
        """Get current user's own profile"""
        serializer = OwnProfileSerializer(request.user, context={'request': request})
        return Response(serializer.data)

    def partial_update(self, request, pk=None):
        """Update own profile"""
        # Only allow updating own profile
        if int(pk) != request.user.id:
            return Response(
                {'detail': 'You can only update your own profile'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = OwnProfileSerializer(
            request.user,
            data=request.data,
            partial=True,
            context={'request': request}
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FollowViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing follows
    """
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = FollowSerializer
    queryset = Follow.objects.all()

    def get_queryset(self):
        """Filter follows based on user"""
        user = self.request.user
        queryset = Follow.objects.all()

        # Filter by follower or following
        follower_id = self.request.query_params.get('follower')
        following_id = self.request.query_params.get('following')

        if follower_id:
            queryset = queryset.filter(follower_id=follower_id)
        if following_id:
            queryset = queryset.filter(following_id=following_id)

        return queryset.select_related('follower__profile', 'following__profile')

    @action(detail=False, methods=['get'])
    def followers(self, request):
        """Get current user's followers"""
        user_id = request.query_params.get('user_id') or request.user.id
        followers = Follow.objects.filter(following_id=user_id).select_related(
            'follower__profile'
        ).order_by('-created_at')

        page = self.paginate_queryset(followers)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(followers, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def following(self, request):
        """Get users that current user is following"""
        user_id = request.query_params.get('user_id') or request.user.id
        following = Follow.objects.filter(follower_id=user_id).select_related(
            'following__profile'
        ).order_by('-created_at')

        page = self.paginate_queryset(following)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(following, many=True)
        return Response(serializer.data)


class FollowActionViewSet(viewsets.ViewSet):
    """
    Separate ViewSet for follow/unfollow actions
    URLs: /api/social/{username}/follow/, /api/social/{username}/unfollow/
    """
    permission_classes = (permissions.IsAuthenticated,)

    def _get_user_by_username(self, username):
        """Helper to get user by username"""
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            return None

    @action(detail=False, methods=['post'], url_path='(?P<username>[^/.]+)/follow')
    def follow(self, request, username=None):
        """Follow a user"""
        target_user = self._get_user_by_username(username)

        if not target_user:
            return Response(
                {'detail': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        if target_user == request.user:
            return Response(
                {'detail': 'Cannot follow yourself'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if already following
        if Follow.objects.filter(follower=request.user, following=target_user).exists():
            return Response(
                {'detail': 'Already following this user'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if blocked
        if BlockedUser.objects.filter(blocker=target_user, blocked=request.user).exists():
            return Response(
                {'detail': 'Cannot follow this user'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Create follow relationship
        follow = Follow.objects.create(
            follower=request.user,
            following=target_user
        )

        # Update cached counts
        request.user.profile.following_count = F('following_count') + 1
        request.user.profile.save(update_fields=['following_count'])

        target_user.profile.follower_count = F('follower_count') + 1
        target_user.profile.save(update_fields=['follower_count'])

        serializer = FollowSerializer(follow)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='(?P<username>[^/.]+)/unfollow')
    def unfollow(self, request, username=None):
        """Unfollow a user"""
        target_user = self._get_user_by_username(username)

        if not target_user:
            return Response(
                {'detail': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check if following
        follow = Follow.objects.filter(
            follower=request.user,
            following=target_user
        ).first()

        if not follow:
            return Response(
                {'detail': 'Not following this user'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Delete follow relationship
        follow.delete()

        # Update cached counts
        request.user.profile.following_count = F('following_count') - 1
        request.user.profile.save(update_fields=['following_count'])

        target_user.profile.follower_count = F('follower_count') - 1
        target_user.profile.save(update_fields=['follower_count'])

        return Response(status=status.HTTP_204_NO_CONTENT)


class UserSearchViewSet(viewsets.ViewSet):
    """
    ViewSet for user search with optimized queries
    """
    permission_classes = (permissions.IsAuthenticated,)

    def list(self, request):
        """Search users with filters using optimized search"""
        from search.utils import UserSearchOptimizer

        # Get query parameters
        search_query = request.query_params.get('search', '')
        location = request.query_params.get('location', '')
        target_university = request.query_params.get('target_university', '')
        min_sat = request.query_params.get('min_sat')
        min_gpa = request.query_params.get('min_gpa')
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))

        # Convert to proper types
        min_sat = int(min_sat) if min_sat else None
        min_gpa = float(min_gpa) if min_gpa else None

        # Use optimized search
        results = UserSearchOptimizer.search_users(
            search_query=search_query,
            location=location,
            target_university=target_university,
            min_sat=min_sat,
            min_gpa=min_gpa,
            exclude_blocked=True,
            user_id=request.user.id,
            page=page,
            page_size=page_size,
        )

        # Serialize results
        serializer = UserSearchSerializer(results['results'], many=True, context={'request': request})

        return Response({
            'count': results['count'],
            'next': results['next'],
            'previous': results['previous'],
            'num_pages': results['num_pages'],
            'results': serializer.data,
        })


class DirectMessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for direct messages
    """
    permission_classes = (permissions.IsAuthenticated,)

    def get_serializer_class(self):
        """Use different serializers for create vs list/retrieve"""
        if self.action == 'create':
            return DirectMessageCreateSerializer
        return DirectMessageSerializer

    def get_queryset(self):
        """Get messages for current user"""
        user = self.request.user
        return DirectMessage.objects.filter(
            Q(sender=user) | Q(recipient=user)
        ).select_related('sender__profile', 'recipient__profile')

    def perform_create(self, serializer):
        """Save message with current user as sender"""
        serializer.save(sender=self.request.user)

    @action(detail=False, methods=['get'])
    def conversations(self, request):
        """Get all conversations with unique users"""
        user = request.user

        # Get unique users that current user has messaged with
        sent_to = DirectMessage.objects.filter(
            sender=user
        ).values_list('recipient_id', flat=True).distinct()

        received_from = DirectMessage.objects.filter(
            recipient=user
        ).values_list('sender_id', flat=True).distinct()

        # Combine and deduplicate
        user_ids = set(list(sent_to) + list(received_from))
        users = User.objects.filter(
            id__in=user_ids
        ).select_related('profile')

        # For each user, get last message and unread count
        conversations = []
        for other_user in users:
            # Get last message
            last_message = DirectMessage.objects.filter(
                Q(sender=user, recipient=other_user) |
                Q(sender=other_user, recipient=user)
            ).order_by('-created_at').first()

            # Get unread count
            unread_count = DirectMessage.objects.filter(
                sender=other_user,
                recipient=user,
                is_read=False
            ).count()

            conversations.append({
                'user': {
                    'id': other_user.id,
                    'username': other_user.username,
                    'avatar_url': other_user.profile.avatar_url if hasattr(other_user, 'profile') else None,
                },
                'last_message': DirectMessageSerializer(last_message).data if last_message else None,
                'unread_count': unread_count,
            })

        # Sort by last message time
        conversations.sort(
            key=lambda c: c['last_message']['created_at'] if c['last_message'] else '',
            reverse=True
        )

        return Response(conversations)

    @action(detail=False, methods=['get'])
    def with_user(self, request):
        """Get conversation with specific user"""
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response(
                {'detail': 'user_id parameter required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            other_user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response(
                {'detail': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get messages between current user and other user
        messages = DirectMessage.objects.filter(
            Q(sender=request.user, recipient=other_user) |
            Q(sender=other_user, recipient=request.user)
        ).select_related('sender__profile', 'recipient__profile').order_by('created_at')

        # Mark received messages as read
        DirectMessage.objects.filter(
            sender=other_user,
            recipient=request.user,
            is_read=False
        ).update(
            is_read=True,
            read_at=timezone.now()
        )

        # Pagination
        from rest_framework.pagination import PageNumberPagination
        paginator = PageNumberPagination()
        paginator.page_size = 50

        page = paginator.paginate_queryset(messages, request)
        if page is not None:
            serializer = DirectMessageSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = DirectMessageSerializer(messages, many=True)
        return Response(serializer.data)


class BlockedUserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for blocked users
    """
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = BlockedUserSerializer

    def get_queryset(self):
        """Get users blocked by current user"""
        return BlockedUser.objects.filter(
            blocker=self.request.user
        ).select_related('blocked__profile')

    def perform_create(self, serializer):
        """Save block with current user as blocker"""
        user_to_block = serializer.validated_data['blocked']

        # Unfollow if following
        Follow.objects.filter(
            follower=self.request.user,
            following=user_to_block
        ).delete()

        # Unfollow if being followed
        Follow.objects.filter(
            follower=user_to_block,
            following=self.request.user
        ).delete()

        serializer.save(blocker=self.request.user)

    def destroy(self, request, *args, **kwargs):
        """Unblock user"""
        blocked_user = self.get_object()

        # Check ownership
        if blocked_user.blocker != request.user:
            return Response(
                {'detail': 'You can only unblock users you blocked'},
                status=status.HTTP_403_FORBIDDEN
            )

        return super().destroy(request, *args, **kwargs)
