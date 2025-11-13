"""
Task Artifact & Evidence Models
Support for "Let's Go" flow and "Do It For Me" automation
"""
from django.db import models
from django.conf import settings
from .models import Todo


class TaskArtifact(models.Model):
    """
    Artifacts generated during task execution
    Examples: shortlists, spreadsheets, docs, emails, recordings
    """
    ARTIFACT_TYPE_CHOICES = [
        ('shortlist', 'Shortlist'),  # JSON list of options
        ('spreadsheet', 'Spreadsheet'),  # Google Sheets, CSV
        ('doc', 'Document'),  # Google Docs, PDF
        ('email', 'Email Draft'),
        ('recording', 'Recording'),  # Audio/video
        ('link', 'Link'),
        ('file', 'File'),
        ('json', 'JSON Data'),
    ]

    task = models.ForeignKey(Todo, on_delete=models.CASCADE, related_name='artifacts')
    artifact_type = models.CharField(max_length=20, choices=ARTIFACT_TYPE_CHOICES)

    # Content (JSON for structured data, text for unstructured)
    content = models.JSONField(
        blank=True,
        default=dict,
        help_text="Structured content (for shortlist, spreadsheet, etc.)"
    )
    text_content = models.TextField(
        blank=True,
        help_text="Text content (for docs, emails, etc.)"
    )

    # External references
    url = models.URLField(max_length=500, blank=True, help_text="Link to Google Doc/Sheet, etc.")
    file = models.FileField(upload_to='artifacts/', blank=True, null=True)

    # Attribution
    created_by = models.CharField(
        max_length=20,
        choices=[('ai', 'AI'), ('user', 'User'), ('ai_user', 'AI + User')],
        default='ai'
    )

    # Sources (web search results, external data)
    sources = models.JSONField(
        default=list,
        blank=True,
        help_text='[{"title": "...", "url": "...", "captured_at": "..."}]'
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['task', 'artifact_type']),
        ]

    def __str__(self):
        return f"{self.artifact_type} for {self.task.title[:30]}"


class TaskEvidence(models.Model):
    """
    User-uploaded proof of task completion
    Examples: screenshots, files, links, notes
    """
    EVIDENCE_TYPE_CHOICES = [
        ('file', 'File Upload'),
        ('link', 'Link/URL'),
        ('screenshot', 'Screenshot'),
        ('note', 'Text Note'),
        ('photo', 'Photo'),
    ]

    task = models.ForeignKey(Todo, on_delete=models.CASCADE, related_name='evidence')
    evidence_type = models.CharField(max_length=20, choices=EVIDENCE_TYPE_CHOICES)

    # Evidence content
    url = models.URLField(max_length=500, blank=True)
    file = models.FileField(upload_to='evidence/', blank=True, null=True)
    note = models.TextField(blank=True, help_text="Text description or note")

    # Metadata
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name_plural = 'Task evidence'

    def __str__(self):
        return f"{self.evidence_type} for {self.task.title[:30]}"


class TaskRun(models.Model):
    """
    Chat session log when user clicks 'Let's Go'
    Tracks the interactive flow and final output
    """
    task = models.ForeignKey(Todo, on_delete=models.CASCADE, related_name='runs')

    # Chat transcript
    user_inputs = models.JSONField(
        default=list,
        help_text='[{"timestamp": "...", "input_type": "text|chip", "value": "..."}]'
    )
    ai_responses = models.JSONField(
        default=list,
        help_text='[{"timestamp": "...", "message": "...", "suggested_actions": [...]}]'
    )

    # Final output
    final_artifact = models.ForeignKey(
        TaskArtifact,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='run'
    )

    # Session metrics
    duration_seconds = models.IntegerField(default=0)
    interactions_count = models.IntegerField(default=0, help_text="Number of back-and-forth exchanges")
    completed = models.BooleanField(default=False)

    # Metadata
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        status = "completed" if self.completed else "in progress"
        return f"Run for {self.task.title[:30]} ({status})"


class AutomationConsent(models.Model):
    """
    User permissions for 'Do It For Me' automation
    Tracks what AI is allowed to do on user's behalf
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='automation_consent')

    # Permissions
    can_create_docs = models.BooleanField(default=False, help_text="Allow AI to create Google Docs")
    can_create_sheets = models.BooleanField(default=False, help_text="Allow AI to create Spreadsheets")
    can_create_calendar = models.BooleanField(default=False, help_text="Allow AI to create calendar events")
    can_draft_emails = models.BooleanField(default=False, help_text="Allow AI to draft emails")
    can_send_emails = models.BooleanField(default=False, help_text="Allow AI to send emails (requires preview)")

    # Granted/revoked tracking
    granted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    revoked = models.BooleanField(default=False)

    def __str__(self):
        return f"Automation consent for {self.user.email}"


class AutomationAudit(models.Model):
    """
    Audit trail for all automated actions
    Tracks who did what when for accountability
    """
    ACTION_TYPE_CHOICES = [
        ('created_doc', 'Created Document'),
        ('created_sheet', 'Created Spreadsheet'),
        ('created_event', 'Created Calendar Event'),
        ('drafted_email', 'Drafted Email'),
        ('sent_email', 'Sent Email'),
        ('generated_artifact', 'Generated Artifact'),
    ]

    task = models.ForeignKey(Todo, on_delete=models.CASCADE, related_name='automation_audits')
    action_type = models.CharField(max_length=30, choices=ACTION_TYPE_CHOICES)

    # What was created
    artifact = models.ForeignKey(
        TaskArtifact,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    # Attribution
    actor = models.CharField(
        max_length=20,
        default='ai',
        choices=[('ai', 'AI'), ('user', 'User')],
        help_text="Who performed this action"
    )

    # Result
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)

    # Metadata
    timestamp = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict, blank=True, help_text="Additional context")

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['task', 'timestamp']),
        ]

    def __str__(self):
        status = "success" if self.success else "failed"
        return f"{self.action_type} - {status} ({self.timestamp})"
