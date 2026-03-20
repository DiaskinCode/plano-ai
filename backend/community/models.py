"""
Community Models - College Application Platform

Reddit-style community system with:
- Region-based communities (USA, UK, China, Canada, etc.)
- Topic-based communities (SAT Prep, Essays, Extracurriculars, etc.)
- Posts, comments, voting
- User profiles and networking
"""

from django.db import models
from django.conf import settings

USER_MODEL = settings.AUTH_USER_MODEL


class Community(models.Model):
    """
    Community/Subreddit for college applicants
    Can be region-based or topic-based
    """
    TYPE_CHOICES = [
        ('region', 'Region'),
        ('topic', 'Topic'),
    ]

    name = models.CharField(max_length=200, help_text="Community name (e.g., 'USA Applicants', 'SAT Prep')")
    slug = models.SlugField(unique=True, max_length=100, help_text="URL-friendly identifier")
    description = models.TextField(help_text="Community description and purpose")

    community_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        help_text="Whether this is a region or topic community"
    )

    # Visuals
    icon = models.CharField(
        max_length=10,
        default='🎓',
        help_text="Emoji or icon for the community"
    )
    banner_color = models.CharField(
        max_length=7,
        default='#5B6AFF',
        help_text="Hex color for banner"
    )

    # Community rules and guidelines
    rules = models.JSONField(
        default=list,
        blank=True,
        help_text="Community rules: ['No spam', 'Be respectful', ...]"
    )

    # Community info
    member_count = models.IntegerField(default=0, help_text="Cached member count")
    online_count = models.IntegerField(default=0, help_text="Cached online users count")
    post_count = models.IntegerField(default=0, help_text="Cached post count")

    # Moderation
    moderators = models.ManyToManyField(
        USER_MODEL,
        related_name='moderated_communities',
        blank=True,
        help_text="Community moderators"
    )
    is_official = models.BooleanField(
        default=False,
        help_text="Official PathAI community"
    )

    # Tags for discoverability
    tags = models.JSONField(
        default=list,
        blank=True,
        help_text="Tags for search: ['sat', 'essays', 'ivy-league']"
    )

    # Related communities
    related_communities = models.ManyToManyField(
        'self',
        blank=True,
        help_text="Similar communities users might like"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_official', '-member_count', 'name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['community_type']),
            models.Index(fields=['-member_count']),
        ]
        verbose_name_plural = "Communities"

    def __str__(self):
        return f"{self.icon} {self.name}"


class CommunityMember(models.Model):
    """
    Tracks community memberships
    """
    ROLE_CHOICES = [
        ('member', 'Member'),
        ('moderator', 'Moderator'),
        ('admin', 'Admin'),
    ]

    user = models.ForeignKey(
        USER_MODEL,
        on_delete=models.CASCADE,
        related_name='community_memberships'
    )
    community = models.ForeignKey(
        Community,
        on_delete=models.CASCADE,
        related_name='memberships'
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='member'
    )

    # User's display settings for this community
    display_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Optional display name for this community"
    )
    notification_enabled = models.BooleanField(
        default=True,
        help_text="Receive notifications from this community"
    )

    # Activity tracking
    last_visited_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last time user visited this community"
    )
    post_count = models.IntegerField(
        default=0,
        help_text="Number of posts by user in this community"
    )
    comment_count = models.IntegerField(
        default=0,
        help_text="Number of comments by user in this community"
    )

    # Timestamps
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'community']
        indexes = [
            models.Index(fields=['user', 'community']),
            models.Index(fields=['community', '-joined_at']),
        ]
        verbose_name_plural = "Community Members"

    def __str__(self):
        return f"{self.user.email} - {self.community.name} ({self.role})"


class Post(models.Model):
    """
    Community posts/discussions
    """
    FLAIR_CHOICES = [
        ('success', 'SUCCESS'),
        ('question', 'QUESTION'),
        ('advice', 'ADVICE'),
        ('essay', 'ESSAY'),
        ('news', 'NEWS'),
        ('resource', 'RESOURCE'),
        ('discussion', 'DISCUSSION'),
        ('rant', 'RANT'),
    ]

    user = models.ForeignKey(
        USER_MODEL,
        on_delete=models.CASCADE,
        related_name='community_posts'
    )
    community = models.ForeignKey(
        Community,
        on_delete=models.CASCADE,
        related_name='posts'
    )

    # Post content
    title = models.CharField(
        max_length=300,
        help_text="Post title"
    )
    content = models.TextField(
        help_text="Post body/content"
    )

    flair = models.CharField(
        max_length=50,
        choices=FLAIR_CHOICES,
        blank=True,
        help_text="Post flair/tag"
    )

    # Media attachments
    images = models.JSONField(
        default=list,
        blank=True,
        help_text="List of image URLs: ['https://...', ...]"
    )
    files = models.JSONField(
        default=list,
        blank=True,
        help_text="List of file attachments: [{'url': '...', 'name': '...'}]"
    )

    # Engagement stats
    upvotes = models.IntegerField(default=0)
    downvotes = models.IntegerField(default=0)
    comment_count = models.IntegerField(default=0, help_text="Cached comment count")
    view_count = models.IntegerField(default=0, help_text="Cached view count")

    # Post status
    is_pinned = models.BooleanField(
        default=False,
        help_text="Pinned by moderators"
    )
    is_locked = models.BooleanField(
        default=False,
        help_text="Comments disabled"
    )
    is_deleted = models.BooleanField(
        default=False,
        help_text="Soft deleted by user"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_pinned', '-created_at']
        indexes = [
            models.Index(fields=['community', '-created_at']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['-upvotes']),
            models.Index(fields=['flair']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"{self.title[:50]}... ({self.community.name})"

    @property
    def score(self):
        """Net vote score"""
        return self.upvotes - self.downvotes


class Comment(models.Model):
    """
    Nested comments on posts
    """
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    user = models.ForeignKey(
        USER_MODEL,
        on_delete=models.CASCADE,
        related_name='community_comments'
    )

    # Thread support
    parent_comment = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies'
    )

    # Content
    content = models.TextField(help_text="Comment text")

    # Engagement
    upvotes = models.IntegerField(default=0)
    downvotes = models.IntegerField(default=0)

    # Status
    is_deleted = models.BooleanField(
        default=False,
        help_text="Soft deleted by user"
    )
    is_edited = models.BooleanField(
        default=False,
        help_text="Whether comment has been edited"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['post', 'created_at']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['parent_comment']),
            models.Index(fields=['-upvotes']),
        ]

    def __str__(self):
        return f"{self.content[:50]}..."

    @property
    def score(self):
        """Net vote score"""
        return self.upvotes - self.downvotes


class PostVote(models.Model):
    """
    Tracks user votes on posts
    Prevents duplicate voting
    """
    VOTE_CHOICES = [
        ('upvote', 'Upvote'),
        ('downvote', 'Downvote'),
    ]

    user = models.ForeignKey(
        USER_MODEL,
        on_delete=models.CASCADE,
        related_name='post_votes'
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='votes'
    )

    vote_type = models.CharField(
        max_length=10,
        choices=VOTE_CHOICES
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'post']
        indexes = [
            models.Index(fields=['post', 'vote_type']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.vote_type} - Post {self.post.id}"


class CommentVote(models.Model):
    """
    Tracks user votes on comments
    """
    VOTE_CHOICES = [
        ('upvote', 'Upvote'),
        ('downvote', 'Downvote'),
    ]

    user = models.ForeignKey(
        USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comment_votes'
    )
    comment = models.ForeignKey(
        Comment,
        on_delete=models.CASCADE,
        related_name='votes'
    )

    vote_type = models.CharField(
        max_length=10,
        choices=VOTE_CHOICES
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'comment']
        indexes = [
            models.Index(fields=['comment', 'vote_type']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.vote_type} - Comment {self.comment.id}"
