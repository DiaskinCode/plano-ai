from django.db import models
from django.conf import settings


class ChatConversation(models.Model):
    """
    Chat conversation/thread (like ChatGPT sidebar chats)
    Can be general chat or task-specific
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chat_conversations')
    task = models.ForeignKey('todos.Todo', on_delete=models.CASCADE, null=True, blank=True, related_name='chat_conversations', help_text="If set, this is a task-specific conversation")
    title = models.CharField(max_length=200, default='New Chat')

    # Auto-generate title from first message
    auto_titled = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['user', '-updated_at']),
            models.Index(fields=['task']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.title}"


class ChatMessage(models.Model):
    """
    Chat messages between user and AI coach
    """
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System'),
    ]

    conversation = models.ForeignKey(ChatConversation, on_delete=models.CASCADE, related_name='messages', null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chat_messages')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()

    # For voice messages
    is_voice = models.BooleanField(default=False)
    audio_url = models.URLField(blank=True)

    # Context tracking
    context_used = models.JSONField(default=dict, blank=True)  # Snapshot of context at this point

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['conversation', 'created_at']),
            models.Index(fields=['user', 'created_at']),
        ]

    def __str__(self):
        conv_title = self.conversation.title if self.conversation else "No conversation"
        return f"{conv_title} - {self.role}: {self.content[:50]}"


class ChatSummary(models.Model):
    """
    Rolling chat summaries for token efficiency
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chat_summaries')
    summary = models.TextField()
    messages_start_id = models.IntegerField()
    messages_end_id = models.IntegerField()
    token_count = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - Summary (msgs {self.messages_start_id}-{self.messages_end_id})"
