"""
Requirement Engine Models

Implements a structured requirement catalog with verification levels,
flexible scope (global/country/university/program/scholarship), and
evidence tracking.
"""

from django.db import models
from django.contrib.auth import get_user_model
from university_database.models import University

User = get_user_model()


class RequirementTemplate(models.Model):
    """
    Universal requirement template.
    Example: "passport_validity" - 18 months for China, 6 months for UK
    """
    key = models.CharField(max_length=100, unique=True, db_index=True)
    category = models.CharField(max_length=50, choices=[
        ('visa', 'Visa'),
        ('medical', 'Medical'),
        ('docs', 'Documents'),
        ('finance', 'Finance'),
        ('apply', 'Application'),
        ('offer', 'Post-Offer'),
        ('scholarship', 'Scholarship'),
    ], db_index=True)
    title = models.CharField(max_length=255)
    description = models.TextField()

    # Default evidence fields
    default_evidence_fields = models.JSONField(default=list, blank=True)
    # Example: ["passport_expiry_date", "passport_scan"]

    # Default link (can be overridden in rules)
    default_link_url = models.URLField(blank=True)

    is_active = models.BooleanField(default=True, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'key']
        indexes = [
            models.Index(fields=['key', 'is_active']),
            models.Index(fields=['category', 'is_active']),
        ]

    def __str__(self):
        return f"{self.key}: {self.title}"


class RequirementRule(models.Model):
    """
    Conditions for applying a template + overrides.
    Example: "If country=China, passport_validity=18 months"
    """
    template = models.ForeignKey(
        RequirementTemplate,
        on_delete=models.CASCADE,
        related_name='rules'
    )

    scope = models.CharField(max_length=50, choices=[
        ('country', 'Country'),
        ('university', 'University'),
        ('scholarship', 'Scholarship'),
        ('program', 'Program'),
    ], db_index=True)

    # Scope target
    country = models.CharField(max_length=100, blank=True, db_index=True)
    university = models.ForeignKey(
        University,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='requirement_rules'
    )

    # Conditions (when does this rule apply?)
    conditions = models.JSONField(default=dict, blank=True)
    # Example: {"scholarship": true, "country": "China", "family_size_required": true}

    # Overrides (modify template defaults)
    overrides = models.JSONField(default=dict, blank=True)
    # Example: {"min_passport_months": 18, "evidence_fields": ["passport", "household_registration"]}

    # Link (override template default)
    link_url = models.URLField(blank=True)

    # Priority
    priority = models.CharField(max_length=20, choices=[
        ('blocker', 'Blocker - prevents application'),
        ('warning', 'Warning - can start but need soon'),
        ('info', 'Information only'),
    ], default='info', db_index=True)

    is_active = models.BooleanField(default=True, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['priority', 'scope', 'country']
        indexes = [
            models.Index(fields=['scope', 'country', 'is_active']),
            models.Index(fields=['university', 'is_active']),
        ]

    def __str__(self):
        target = self.country or self.university.name if self.university else "Global"
        return f"{self.template.key} -> {target} ({self.priority})"


class RequirementInstance(models.Model):
    """
    Instance of a requirement for a user.
    Flexible scope: global | country | university | program | scholarship
    This is the PROOF that "China visa requires X because source=country_rule"
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='requirement_instances')

    # Flexible scope (university can be null for country-level requirements)
    university = models.ForeignKey(
        University,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='requirement_instances'
    )

    # Scope level (critical for visa/medical/finance which are country-level, not uni-level)
    scope_level = models.CharField(max_length=20, choices=[
        ('global', 'Global'),  # Passport, IELTS - applies everywhere
        ('country', 'Country'),  # Visa, medical, finance - per country
        ('university', 'University'),  # Portal, specific docs
        ('program', 'Program'),  # Portfolio, interview
        ('scholarship', 'Scholarship'),  # Tax docs, property proof
    ], default='university', db_index=True)

    # Country (for country-level requirements)
    country = models.CharField(max_length=100, blank=True, default='', db_index=True)

    # Track/intake/degree (CRITICAL - requirements vary by these)
    track = models.CharField(max_length=30, default='direct')  # direct | foundation
    intake = models.CharField(max_length=30, blank=True, default='')  # fall_2026 | spring_2027
    degree_level = models.CharField(max_length=30, blank=True, default='')  # bachelor | master
    citizenship = models.CharField(max_length=50, blank=True, default='')  # For domestic vs intl requirements

    # What requirement?
    requirement_key = models.CharField(max_length=100, db_index=True)
    # Links to RequirementTemplate.key

    # Status of this requirement
    status = models.CharField(max_length=20, choices=[
        ('required', 'Required - not satisfied'),
        ('not_required', 'Not applicable'),
        ('unknown', 'Needs verification'),
        ('satisfied', 'Requirement met'),
        ('missing', 'Required but missing'),
    ], default='unknown', db_index=True)

    # Verification level (CRITICAL - what counts as "verified"?)
    verification_level = models.CharField(max_length=20, choices=[
        ('official', 'Official source'),  # Government website, official uni portal
        ('vendor', 'Vendor/uni portal'),  # Common App, UCAS, testing agency
        ('assumed', 'Country default'),  # Default assumption for country
        ('user_reported', 'User reported'),  # User filled in, not verified
    ], default='assumed', db_index=True)

    # Source domain type (for verified coverage validation)
    source_domain_type = models.CharField(max_length=20, choices=[
        ('government', 'Government website'),
        ('university', 'University official portal'),
        ('vendor', 'Third-party vendor'),
        ('other', 'Other source'),
    ], blank=True, db_index=True)

    # Source of truth
    source = models.CharField(max_length=50, choices=[
        ('country_rule', 'Country Requirement Rule'),
        ('university_rule', 'University Requirement Rule'),
        ('scholarship_rule', 'Scholarship Requirement Rule'),
        ('program_rule', 'Program Requirement Rule'),
        ('manual_override', 'Manually verified'),
    ], default='university_rule')

    # Evidence (uniform naming, not evidence_required)
    evidence_fields = models.JSONField(default=list, blank=True)
    # Example: ["passport_expiry_date", "scan_of_passport"]

    # Notes
    notes = models.TextField(blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        # Flexible unique constraints
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'university', 'requirement_key', 'track'],
                condition=models.Q(university__isnull=False),
                name='unique_user_university_requirement'
            ),
            models.UniqueConstraint(
                fields=['user', 'country', 'requirement_key', 'track'],
                condition=models.Q(university__isnull=True),
                name='unique_user_country_requirement'
            ),
        ]
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['user', 'scope_level']),
            models.Index(fields=['country', 'requirement_key']),
            models.Index(fields=['user', 'verification_level']),
        ]
        ordering = ['scope_level', 'country', 'requirement_key']

    def __str__(self):
        scope_str = f"{self.scope_level}"
        if self.country:
            scope_str += f" ({self.country})"
        elif self.university:
            scope_str += f" ({self.university.name})"
        return f"{self.user.email} - {self.requirement_key} [{scope_str}]"


class RequirementPack(models.Model):
    """
    Pre-defined packs of requirements.
    Example: "Country Pack: China" = visa + finance + medical + translation
    """
    name = models.CharField(max_length=255)
    pack_type = models.CharField(max_length=20, choices=[
        ('country', 'Country Pack'),
        ('scholarship', 'Scholarship Pack'),
        ('program', 'Program Pack'),
    ], db_index=True)

    # Pack contents (template keys)
    requirement_templates = models.JSONField(default=list, blank=True)
    # Example: ["visa_checklist", "finance_proof", "medical_exam", "translation"]

    # Scope
    country = models.CharField(max_length=100, blank=True, db_index=True)

    # Conditions (when to apply?)
    conditions = models.JSONField(default=dict, blank=True)
    # Example: {"scholarship_intent": true} for scholarship pack

    # Priority
    priority = models.IntegerField(default=0)

    is_active = models.BooleanField(default=True, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['pack_type', '-priority', 'country']
        indexes = [
            models.Index(fields=['pack_type', 'country', 'is_active']),
        ]

    def __str__(self):
        return f"{self.pack_type.upper()}: {self.name}"


class DocumentVaultItem(models.Model):
    """
    User's uploaded documents.
    Makes evidence_status real (not computed from nothing).
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='document_vault')

    # Document type
    doc_type = models.CharField(max_length=50, choices=[
        ('passport_scan', 'Passport Scan'),
        ('passport_expiry', 'Passport Expiry Date'),
        ('ielts_trf', 'IELTS Test Report Form'),
        ('toefl_score', 'TOEFL Score Report'),
        ('transcript_pdf', 'Official Transcript'),
        ('transcript_translation', 'Transcript Translation'),
        ('bank_statement', 'Bank Statement'),
        ('tax_certificate', 'Tax Certificate'),
        ('property_proof', 'Property Ownership Proof'),
        ('medical_exam', 'Medical Exam Certificate'),
        ('visa_approval', 'Visa Approval Document'),
        ('offer_letter', 'University Offer Letter'),
        ('enrollment_deposit', 'Enrollment Deposit Receipt'),
        ('cas_document', 'CAS Confirmation Document'),
        ('i20_document', 'I-20 Form'),
    ], db_index=True)

    # File
    file_url = models.URLField(max_length=500)
    file_name = models.CharField(max_length=255)
    file_size = models.IntegerField()  # bytes

    # Metadata (extracted from doc or user-filled)
    metadata = models.JSONField(default=dict, blank=True)
    # Example for IELTS:
    # {
    #   "test_date": "2026-01-15",
    #   "overall_score": 7.5,
    #   "listening": 8.0,
    #   "reading": 7.5,
    #   "writing": 7.0,
    #   "speaking": 7.0,
    #   "trf_number": "12345678"
    # }

    # Timestamps
    uploaded_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    # Verification
    is_verified = models.BooleanField(default=False, db_index=True)
    verification_notes = models.TextField(blank=True)

    class Meta:
        unique_together = ['user', 'doc_type', 'file_name']
        indexes = [
            models.Index(fields=['user', 'doc_type']),
            models.Index(fields=['user', 'is_verified']),
            models.Index(fields=['-uploaded_at']),
        ]
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.user.email} - {self.doc_type} ({self.file_name})"


class RequirementSourceSnapshot(models.Model):
    """
    Snapshot of requirement source for audit trail.
    Answers: "What did verified look like on date X?"
    """
    requirement_instance = models.ForeignKey(
        RequirementInstance,
        on_delete=models.CASCADE,
        related_name='snapshots'
    )

    # Snapshot data
    fetched_at = models.DateTimeField(auto_now_add=True, db_index=True)

    link_url = models.URLField(max_length=500)
    hash_excerpt = models.TextField(blank=True)  # 200-500 chars from source page

    # Metadata
    updated_by = models.CharField(max_length=20, choices=[
        ('admin', 'Admin manual update'),
        ('system', 'System ingestion'),
        ('user', 'User reported'),
    ], default='system')

    # Validation
    is_valid = models.BooleanField(default=True)
    validation_notes = models.TextField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['requirement_instance', '-fetched_at']),
            models.Index(fields=['fetched_at']),
        ]
        ordering = ['-fetched_at']

    def __str__(self):
        return f"Snapshot for {self.requirement_instance.requirement_key} at {self.fetched_at}"
