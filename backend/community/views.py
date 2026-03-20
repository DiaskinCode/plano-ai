"""
Community API Views - College Application Platform

Provides endpoints for:
- Community CRUD and membership
- Post CRUD and voting
- Comment threading and voting
"""

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q, F, Count
from django.shortcuts import get_object_or_404

from .models import Community, CommunityMember, Post, Comment, PostVote, CommentVote
from .serializers import (
    CommunityListSerializer,
    CommunityDetailSerializer,
    CommunityMemberSerializer,
    PostListSerializer,
    PostDetailSerializer,
    PostCreateSerializer,
    CommentSerializer,
    CommentCreateSerializer,
    CommunityJoinSerializer,
)


class CommunityViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing communities
    """
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Community.objects.all()
    serializer_class = CommunityListSerializer

    def get_serializer_class(self):
        """Use detailed serializer for single object"""
        if self.action == 'retrieve':
            return CommunityDetailSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        """Filter and sort communities"""
        queryset = Community.objects.all()

        # Filter by type
        community_type = self.request.query_params.get('type')
        if community_type in ['region', 'topic']:
            queryset = queryset.filter(community_type=community_type)

        # Search
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search) |
                Q(tags__contains=[search.lower()])
            )

        # Sort
        sort = self.request.query_params.get('sort', 'popular')
        if sort == 'popular':
            queryset = queryset.order_by('-member_count')
        elif sort == 'new':
            queryset = queryset.order_by('-created_at')
        elif sort == 'active':
            queryset = queryset.order_by('-post_count')

        return queryset

    @action(detail=True, methods=['post'])
    def join(self, request, pk=None):
        """Join a community"""
        community = self.get_object()
        user = request.user

        # Check if already a member
        if CommunityMember.objects.filter(user=user, community=community).exists():
            return Response(
                {'detail': 'Already a member of this community'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create membership
        membership = CommunityMember.objects.create(
            user=user,
            community=community,
            role='member'
        )

        # Update community member count
        community.member_count = F('member_count') + 1
        community.save(update_fields=['member_count'])

        # Refresh to get updated count
        community.refresh_from_db()

        serializer = CommunityDetailSerializer(
            community,
            context={'request': request}
        )
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def leave(self, request, pk=None):
        """Leave a community"""
        community = self.get_object()
        user = request.user

        # Check if member
        membership = CommunityMember.objects.filter(
            user=user,
            community=community
        ).first()

        if not membership:
            return Response(
                {'detail': 'Not a member of this community'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if user is the only moderator
        if membership.role == 'moderator':
            moderator_count = CommunityMember.objects.filter(
                community=community,
                role='moderator'
            ).count()
            if moderator_count == 1:
                return Response(
                    {'detail': 'Cannot leave - you are the only moderator'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Delete membership
        membership.delete()

        # Update community member count
        community.member_count = F('member_count') - 1
        community.save(update_fields=['member_count'])

        # Refresh to get updated count
        community.refresh_from_db()

        serializer = CommunityDetailSerializer(
            community,
            context={'request': request}
        )
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def posts(self, request, pk=None):
        """Get posts for this community"""
        community = self.get_object()

        # Sort options
        sort = request.query_params.get('sort', 'hot')
        if sort == 'hot':
            # Hot = upvotes - downvotes, with time decay
            posts = community.posts.filter(is_deleted=False).order_by('-score')
        elif sort == 'new':
            posts = community.posts.filter(is_deleted=False).order_by('-created_at')
        elif sort == 'top':
            posts = community.posts.filter(is_deleted=False).order_by('-score')
        else:  # default to hot
            posts = community.posts.filter(is_deleted=False).order_by('-score')

        # Filter by flair
        flair = request.query_params.get('flair')
        if flair:
            posts = posts.filter(flair=flair)

        # Pagination
        page = self.paginate_queryset(posts)
        if page is not None:
            serializer = PostListSerializer(
                page,
                many=True,
                context={'request': request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = PostListSerializer(
            posts,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def my_communities(self, request):
        """Get communities user has joined"""
        user = request.user
        memberships = CommunityMember.objects.filter(user=user).select_related('community')
        communities = [m.community for m in memberships]

        # Sort by last visited or joined date
        sort = request.query_params.get('sort', 'visited')
        if sort == 'visited':
            communities.sort(
                key=lambda c: max(
                    (m.last_visited_at or timezone.now()),
                    m.joined_at
                ),
                reverse=True
            )
        elif sort == 'joined':
            communities.sort(
                key=lambda c: next(
                    m2.joined_at for m2 in memberships if m2.community == c
                ),
                reverse=True
            )

        serializer = CommunityListSerializer(communities, many=True)
        return Response(serializer.data)


class PostViewSet(viewsets.ModelViewSet):
    """
    ViewSet for posts
    """
    permission_classes = (permissions.IsAuthenticated,)

    def get_serializer_class(self):
        """Use different serializers for different actions"""
        if self.action == 'create':
            return PostCreateSerializer
        elif self.action in ['retrieve', 'update', 'partial_update']:
            return PostDetailSerializer
        return PostListSerializer

    def get_queryset(self):
        """Get posts with filters"""
        queryset = Post.objects.filter(is_deleted=False).select_related(
            'user__profile',
            'community'
        )

        # Filter by community
        community_id = self.request.query_params.get('community')
        if community_id:
            queryset = queryset.filter(community_id=community_id)

        # Filter by user
        user_id = self.request.query_params.get('user')
        if user_id:
            queryset = queryset.filter(user_id=user_id)

        # Filter by flair
        flair = self.request.query_params.get('flair')
        if flair:
            queryset = queryset.filter(flair=flair)

        # Sort
        sort = self.request.query_params.get('sort', 'hot')
        if sort == 'hot':
            queryset = queryset.order_by('-score', '-created_at')
        elif sort == 'new':
            queryset = queryset.order_by('-created_at')
        elif sort == 'top':
            queryset = queryset.order_by('-score')
        else:
            queryset = queryset.order_by('-is_pinned', '-score', '-created_at')

        return queryset

    def perform_create(self, serializer):
        """Save post with current user"""
        # Increment community post count
        community = serializer.validated_data['community']
        community.post_count = F('post_count') + 1
        community.save(update_fields=['post_count'])

        # Save post
        serializer.save(user=self.request.user)

        # Update user's post count in community
        membership = CommunityMember.objects.get(
            user=self.request.user,
            community=community
        )
        membership.post_count = F('post_count') + 1
        membership.save(update_fields=['post_count'])

    def perform_update(self, serializer):
        """Update post"""
        post = self.get_object()
        old_content = post.content

        # Save updated post
        serializer.save()

        # Mark as edited if content changed
        if post.content != old_content:
            post.is_edited = True
            post.save(update_fields=['is_edited'])

    def destroy(self, request, *args, **kwargs):
        """Soft delete post"""
        post = self.get_object()

        # Check ownership
        if post.user != request.user:
            return Response(
                {'detail': 'You can only delete your own posts'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Soft delete
        post.is_deleted = True
        post.save(update_fields=['is_deleted'])

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def upvote(self, request, pk=None):
        """Upvote a post"""
        post = self.get_object()
        user = request.user

        # Check for existing vote
        existing_vote = PostVote.objects.filter(
            user=user,
            post=post
        ).first()

        if existing_vote:
            if existing_vote.vote_type == 'upvote':
                # Remove vote (toggle off)
                existing_vote.delete()
                post.upvotes = F('upvotes') - 1
            else:
                # Change from downvote to upvote
                existing_vote.vote_type = 'upvote'
                existing_vote.save()
                post.upvotes = F('upvotes') + 1
                post.downvotes = F('downvotes') - 1
        else:
            # Create new upvote
            PostVote.objects.create(user=user, post=post, vote_type='upvote')
            post.upvotes = F('upvotes') + 1

        post.save(update_fields=['upvotes', 'downvotes'])
        post.refresh_from_db()

        serializer = PostListSerializer(post, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def downvote(self, request, pk=None):
        """Downvote a post"""
        post = self.get_object()
        user = request.user

        # Check for existing vote
        existing_vote = PostVote.objects.filter(
            user=user,
            post=post
        ).first()

        if existing_vote:
            if existing_vote.vote_type == 'downvote':
                # Remove vote (toggle off)
                existing_vote.delete()
                post.downvotes = F('downvotes') - 1
            else:
                # Change from upvote to downvote
                existing_vote.vote_type = 'downvote'
                existing_vote.save()
                post.downvotes = F('downvotes') + 1
                post.upvotes = F('upvotes') - 1
        else:
            # Create new downvote
            PostVote.objects.create(user=user, post=post, vote_type='downvote')
            post.downvotes = F('downvotes') + 1

        post.save(update_fields=['upvotes', 'downvotes'])
        post.refresh_from_db()

        serializer = PostListSerializer(post, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def comments(self, request, pk=None):
        """Get comments for this post"""
        post = self.get_object()

        # Get top-level comments only (no parent)
        comments = post.comments.filter(
            parent_comment=None,
            is_deleted=False
        ).select_related('user__profile').order_by('-score', 'created_at')

        # Pagination
        page = self.paginate_queryset(comments)
        if page is not None:
            serializer = CommentSerializer(
                page,
                many=True,
                context={'request': request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = CommentSerializer(
            comments,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)


class CommentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for comments
    """
    permission_classes = (permissions.IsAuthenticated,)

    def get_serializer_class(self):
        """Use different serializers for different actions"""
        if self.action == 'create':
            return CommentCreateSerializer
        return CommentSerializer

    def get_queryset(self):
        """Get comments"""
        return Comment.objects.filter(
            is_deleted=False
        ).select_related('user__profile', 'post')

    def perform_create(self, serializer):
        """Save comment with current user"""
        comment = serializer.save(user=self.request.user)

        # Update post comment count
        post = comment.post
        post.comment_count = F('comment_count') + 1
        post.save(update_fields=['comment_count'])

        # Update user's comment count in community
        membership = CommunityMember.objects.get(
            user=self.request.user,
            community=post.community
        )
        membership.comment_count = F('comment_count') + 1
        membership.save(update_fields=['comment_count'])

    def perform_update(self, serializer):
        """Update comment"""
        comment = self.get_object()
        old_content = comment.content

        # Save updated comment
        serializer.save()

        # Mark as edited if content changed
        if comment.content != old_content:
            comment.is_edited = True
            comment.save(update_fields=['is_edited'])

    def destroy(self, request, *args, **kwargs):
        """Soft delete comment"""
        comment = self.get_object()

        # Check ownership
        if comment.user != request.user:
            return Response(
                {'detail': 'You can only delete your own comments'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Soft delete
        comment.is_deleted = True
        comment.content = '[deleted]'
        comment.save(update_fields=['is_deleted', 'content'])

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def upvote(self, request, pk=None):
        """Upvote a comment"""
        comment = self.get_object()
        user = request.user

        # Check for existing vote
        existing_vote = CommentVote.objects.filter(
            user=user,
            comment=comment
        ).first()

        if existing_vote:
            if existing_vote.vote_type == 'upvote':
                # Remove vote (toggle off)
                existing_vote.delete()
                comment.upvotes = F('upvotes') - 1
            else:
                # Change from downvote to upvote
                existing_vote.vote_type = 'upvote'
                existing_vote.save()
                comment.upvotes = F('upvotes') + 1
                comment.downvotes = F('downvotes') - 1
        else:
            # Create new upvote
            CommentVote.objects.create(user=user, comment=comment, vote_type='upvote')
            comment.upvotes = F('upvotes') + 1

        comment.save(update_fields=['upvotes', 'downvotes'])
        comment.refresh_from_db()

        serializer = CommentSerializer(comment, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def downvote(self, request, pk=None):
        """Downvote a comment"""
        comment = self.get_object()
        user = request.user

        # Check for existing vote
        existing_vote = CommentVote.objects.filter(
            user=user,
            comment=comment
        ).first()

        if existing_vote:
            if existing_vote.vote_type == 'downvote':
                # Remove vote (toggle off)
                existing_vote.delete()
                comment.downvotes = F('downvotes') - 1
            else:
                # Change from upvote to downvote
                existing_vote.vote_type = 'downvote'
                existing_vote.save()
                comment.downvotes = F('downvotes') + 1
                comment.upvotes = F('upvotes') - 1
        else:
            # Create new downvote
            CommentVote.objects.create(user=user, comment=comment, vote_type='downvote')
            comment.downvotes = F('downvotes') + 1

        comment.save(update_fields=['upvotes', 'downvotes'])
        comment.refresh_from_db()

        serializer = CommentSerializer(comment, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def replies(self, request, pk=None):
        """Get replies to this comment"""
        comment = self.get_object()

        replies = comment.replies.filter(
            is_deleted=False
        ).select_related('user__profile').order_by('-score', 'created_at')

        serializer = CommentSerializer(
            replies,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)
