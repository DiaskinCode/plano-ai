"""
Search Optimization Utilities

Provides optimized search functionality for:
- Users
- Posts
- Communities
"""

from django.db.models import Q, Count, Prefetch
from django.db.models.functions import Lower
from django.core.paginator import Paginator
from typing import Dict, Any, List, Tuple
import re


class SearchOptimizer:
    """Optimized search utilities"""

    @staticmethod
    def normalize_query(query: str) -> str:
        """
        Normalize search query by removing extra whitespace and special chars.
        """
        if not query:
            return ''
        # Remove extra whitespace
        query = ' '.join(query.split())
        # Remove special regex characters but keep @ for mentions
        query = re.sub(r'[^\w\s@.-]', '', query)
        return query.lower()

    @staticmethod
    def build_search_query(fields: List[str], query: str) -> Q:
        """
        Build an OR query across multiple fields for case-insensitive search.

        Args:
            fields: List of field names to search
            query: Search string

        Returns:
            Q object for filtering
        """
        if not query:
            return Q()

        q_objects = []
        for field in fields:
            # Use __icontains for case-insensitive search
            q_objects.append(Q(**{f'{field}__icontains': query}))

        # Combine with OR
        return Q(*q_objects, _connector=Q.OR)

    @staticmethod
    def get_paginated_results(queryset, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """
        Paginate queryset and return results with metadata.

        Args:
            queryset: Django queryset
            page: Page number (1-indexed)
            page_size: Number of items per page

        Returns:
            Dict with results, count, next, previous
        """
        paginator = Paginator(queryset, page_size)

        try:
            page_obj = paginator.page(page)
        except:
            page_obj = paginator.page(1)

        return {
            'count': paginator.count,
            'next': page_obj.next_page_number() if page_obj.has_next() else None,
            'previous': page_obj.previous_page_number() if page_obj.has_previous() else None,
            'num_pages': paginator.num_pages,
            'results': list(page_obj.object_list),
        }


class UserSearchOptimizer:
    """Optimized user search with filters"""

    @staticmethod
    def search_users(
        search_query: str = '',
        location: str = '',
        target_university: str = '',
        min_sat: int = None,
        min_gpa: float = None,
        exclude_blocked: bool = True,
        user_id: int = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """
        Optimized user search with multiple filters.

        Uses select_related to minimize database queries.
        """
        from users.models import User
        from social.models import BlockedUser

        # Start with base queryset
        queryset = User.objects.select_related('profile').all()

        # Apply search query (username or email)
        if search_query:
            search_query = SearchOptimizer.normalize_query(search_query)
            queryset = queryset.filter(
                Q(username__icontains=search_query) |
                Q(email__icontains=search_query)
            )

        # Apply location filter
        if location:
            queryset = queryset.filter(profile__location__icontains=location)

        # Apply target university filter (JSON field search)
        if target_university:
            queryset = queryset.filter(
                profile__target_universities__contains=target_university
            )

        # Apply SAT score filter
        if min_sat is not None:
            queryset = queryset.filter(
                profile__sat_score_public__gte=min_sat
            )

        # Apply GPA filter
        if min_gpa is not None:
            queryset = queryset.filter(
                profile__gpa_public__gte=min_gpa
            )

        # Exclude blocked users and blockers
        if exclude_blocked and user_id:
            blocked_ids = BlockedUser.objects.filter(
                blocker_id=user_id
            ).values_list('blocked_id', flat=True)

            blocker_ids = BlockedUser.objects.filter(
                blocked_id=user_id
            ).values_list('blocker_id', flat=True)

            exclude_ids = list(blocked_ids) + list(blocker_ids) + [user_id]
            queryset = queryset.exclude(id__in=exclude_ids)

        # Order by follower count (most popular first)
        queryset = queryset.order_by('-profile__follower_count')

        # Paginate results
        return SearchOptimizer.get_paginated_results(queryset, page, page_size)


class PostSearchOptimizer:
    """Optimized post search with filters"""

    @staticmethod
    def search_posts(
        community_id: int = None,
        search_query: str = '',
        flair: str = '',
        sort_by: str = 'hot',
        user_id: int = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """
        Optimized post search with sorting and filters.

        Uses prefetch_related to optimize comment count queries.
        """
        from community.models import Post

        # Start with base queryset
        queryset = Post.objects.select_related('user', 'user__profile', 'community').all()

        # Filter by community
        if community_id:
            queryset = queryset.filter(community_id=community_id)

        # Apply search query (title or content)
        if search_query:
            search_query = SearchOptimizer.normalize_query(search_query)
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(content__icontains=search_query)
            )

        # Filter by flair
        if flair:
            queryset = queryset.filter(flair=flair)

        # Filter by user
        if user_id:
            queryset = queryset.filter(user_id=user_id)

        # Sorting
        if sort_by == 'hot':
            # Sort by upvotes/downvotes ratio
            queryset = queryset.annotate(
                score=Count('upvotes') - Count('downvotes')
            ).order_by('-score', '-created_at')
        elif sort_by == 'new':
            queryset = queryset.order_by('-created_at')
        elif sort_by == 'top':
            queryset = queryset.order_by('-upvotes', '-created_at')
        else:  # 'controversial'
            queryset = queryset.annotate(
                total_votes=Count('upvotes') + Count('downvotes')
            ).filter(total_votes__gt=10).order_by('-created_at')

        # Paginate results
        return SearchOptimizer.get_paginated_results(queryset, page, page_size)


class CommunitySearchOptimizer:
    """Optimized community search with filters"""

    @staticmethod
    def search_communities(
        search_query: str = '',
        community_type: str = '',
        sort_by: str = 'members',
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """
        Optimized community search.
        """
        from community.models import Community

        queryset = Community.objects.all()

        # Apply search query
        if search_query:
            search_query = SearchOptimizer.normalize_query(search_query)
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query)
            )

        # Filter by type
        if community_type:
            queryset = queryset.filter(community_type=community_type)

        # Sorting
        if sort_by == 'members':
            queryset = queryset.order_by('-member_count')
        elif sort_by == 'new':
            queryset = queryset.order_by('-created_at')
        elif sort_by == 'active':
            queryset = queryset.order_by('-online_count')
        else:  # 'name'
            queryset = queryset.order_by('name')

        # Paginate results
        return SearchOptimizer.get_paginated_results(queryset, page, page_size)


class MentionDetector:
    """Detect and extract @mentions from text"""

    MENTION_REGEX = r'@(?P<username>[\w.-]+)'

    @staticmethod
    def extract_mentions(text: str) -> List[str]:
        """
        Extract all @mentions from text.

        Args:
            text: Text to search for mentions

        Returns:
            List of usernames (without @ symbol)
        """
        if not text:
            return []

        matches = re.findall(MentionDetector.MENTION_REGEX, text)
        return list(set(matches))  # Remove duplicates

    @staticmethod
    def notify_mentions(text: str, post_id: int, comment_id: int = None, actor_id: int = None):
        """
        Create notifications for all mentioned users.

        Args:
            text: Text containing mentions
            post_id: Post ID
            comment_id: Comment ID (optional)
            actor_id: User who created the post/comment
        """
        from django.contrib.auth import get_user_model
        from notifications.notification_manager import notify_mention

        User = get_user_model()
        mentions = MentionDetector.extract_mentions(text)

        for username in mentions:
            try:
                mentioned_user = User.objects.get(username=username)

                # Don't notify if mentioning yourself
                if actor_id and mentioned_user.id == actor_id:
                    continue

                notify_mention(
                    user_id=mentioned_user.id,
                    mentioner_id=actor_id,
                    post_id=post_id,
                    comment_id=comment_id,
                )
            except User.DoesNotExist:
                # Username doesn't exist, skip
                pass
