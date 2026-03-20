"""
Essay Writing Assistance Models

Provides models for:
- Essay templates (reusable essay types)
- Essay projects (track writing progress)
- Essay feedback (AI and human feedback)
"""

from django.db import models
from django.conf import settings


class EssayTemplate(models.Model):
    """Reusable essay templates for different types of essays"""

    ESSAY_TYPES = [
        ('personal_statement', 'Personal Statement'),
        ('supplemental', 'Supplemental Essay'),
        ('why_college', 'Why This College'),
        ('why_major', 'Why This Major'),
        ('community', 'Community Service'),
        ('leadership', 'Leadership Experience'),
        ('challenge', 'Overcoming Challenge'),
        ('achievement', 'Significant Achievement'),
        ('activity', 'Extracurricular Activity'),
        ('creative', 'Creative/Unconventional'),
    ]

    name = models.CharField(max_length=200)
    essay_type = models.CharField(max_length=50, choices=ESSAY_TYPES)
    prompt = models.TextField(help_text="Essay prompt/question")
    word_count_min = models.IntegerField(default=250)
    word_count_max = models.IntegerField(default=650)

    # Which universities use this essay
    universities = models.JSONField(
        default=list,
        help_text="List of university names that use this essay type"
    )

    # Template structure
    structure_outline = models.JSONField(
        help_text="Suggested paragraph structure with sections and word counts"
    )
    key_themes = models.JSONField(
        default=list,
        help_text="Suggested themes to cover in this essay"
    )
    tips = models.TextField(
        blank=True,
        help_text="Writing tips and best practices for this essay type"
    )

    # Sample essays (anonymized)
    sample_essays = models.JSONField(
        default=list,
        help_text="Example essays for reference (anonymized)"
    )

    # Display order
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name = "Essay Template"
        verbose_name_plural = "Essay Templates"

    def __str__(self):
        return f"{self.icon} {self.name}"

    @property
    def icon(self):
        """Return emoji icon for this essay type"""
        icons = {
            'personal_statement': '📝',
            'supplemental': '✍️',
            'why_college': '🎓',
            'why_major': '🔬',
            'community': '🤝',
            'leadership': '👥',
            'challenge': '💪',
            'achievement': '🏆',
            'activity': '🎯',
            'creative': '🎨',
        }
        return icons.get(self.essay_type, '📄')


class EssayProject(models.Model):
    """Track essay writing progress for each university/essay type"""

    STATUS_CHOICES = [
        ('brainstorming', 'Brainstorming'),
        ('outlining', 'Outlining'),
        ('drafting', 'Drafting'),
        ('reviewing', 'Reviewing'),
        ('polishing', 'Polishing'),
        ('completed', 'Completed'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='essay_projects'
    )
    template = models.ForeignKey(
        EssayTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='projects'
    )

    # Essay identification
    title = models.CharField(max_length=200)
    essay_type = models.CharField(max_length=50)
    target_university = models.CharField(max_length=200, blank=True)
    target_prompt = models.TextField(blank=True)

    # Progress tracking
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='brainstorming'
    )
    current_draft = models.TextField(blank=True)
    word_count = models.IntegerField(default=0)
    revision_count = models.IntegerField(default=0)

    # AI assistance data
    brainstorming_notes = models.JSONField(
        default=list,
        help_text="AI-generated topic ideas and brainstorming results"
    )
    selected_topic = models.JSONField(
        null=True,
        blank=True,
        help_text="User's chosen topic from brainstorming"
    )
    outline_suggestions = models.JSONField(
        null=True,
        blank=True,
        help_text="AI-generated outline for selected topic"
    )
    feedback_history = models.JSONField(
        default=list,
        help_text="History of AI feedback on drafts"
    )

    # Metadata
    deadline = models.DateField(null=True, blank=True)
    word_count_goal = models.IntegerField(default=650)
    progress_percentage = models.IntegerField(default=0)

    # Linked to task in admissions plan (optional)
    related_task = models.ForeignKey(
        'Todo',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='essay_project'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['deadline', 'created_at']
        verbose_name = "Essay Project"
        verbose_name_plural = "Essay Projects"
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['user', 'essay_type']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.title}"

    def update_progress(self):
        """Calculate progress based on status and word count"""
        if self.status == 'completed':
            self.progress_percentage = 100
        elif self.status == 'polishing':
            self.progress_percentage = 90
        elif self.status == 'reviewing':
            self.progress_percentage = 70
        elif self.status == 'drafting':
            # Calculate based on word count
            if self.word_count_goal > 0:
                word_progress = min(100, (self.word_count / self.word_count_goal) * 100)
                self.progress_percentage = int(40 + (word_progress * 0.3))  # 40-70%
            else:
                self.progress_percentage = 50
        elif self.status == 'outlining':
            self.progress_percentage = 30
        elif self.status == 'brainstorming':
            self.progress_percentage = 10
        else:
            self.progress_percentage = 0

        self.save(update_fields=['progress_percentage'])


class EssayFeedback(models.Model):
    """AI and human feedback on essay drafts"""

    essay_project = models.ForeignKey(
        EssayProject,
        on_delete=models.CASCADE,
        related_name='feedback_sessions'
    )
    draft_content = models.TextField()
    draft_word_count = models.IntegerField()

    # AI Feedback
    ai_strengths = models.JSONField(
        default=list,
        help_text="List of strengths identified by AI"
    )
    ai_improvements = models.JSONField(
        default=list,
        help_text="List of suggested improvements from AI"
    )
    ai_structure_feedback = models.TextField(blank=True)
    ai_content_feedback = models.TextField(blank=True)
    ai_voice_feedback = models.TextField(blank=True)
    ai_grammar_feedback = models.TextField(blank=True)
    ai_score = models.IntegerField(
        null=True,
        blank=True,
        help_text="AI quality score (1-10)"
    )
    ai_detailed_feedback = models.TextField(blank=True)

    # Human feedback (optional - for teachers, counselors, mentors)
    human_feedback = models.TextField(blank=True)
    human_score = models.IntegerField(null=True, blank=True)
    human_reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviews_given'
    )

    # Metadata
    feedback_type = models.CharField(
        max_length=20,
        default='ai',
        help_text="Type of feedback: ai, human, or both"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Essay Feedback"
        verbose_name_plural = "Essay Feedback"

    def __str__(self):
        return f"Feedback for {self.essay_project.title} - {self.created_at.strftime('%Y-%m-%d')}"
