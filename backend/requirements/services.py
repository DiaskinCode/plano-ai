"""
Requirement Ingestion Service

Ingests user's shortlisted universities and generates RequirementInstance records.
Implements flexible scope: global | country | university | program | scholarship
"""

from django.db import transaction
from requirements.models import (
    RequirementInstance,
    RequirementPack,
    RequirementRule,
    RequirementTemplate,
)
from university_database.models import University


class RequirementIngestionService:
    """
    Ingest shortlist and generate RequirementInstance records

    Key principles:
    1. Country-level requirements: university=None, scope_level='country'
    2. University-level requirements: university=university, scope_level='university'
    3. Flexible scope based on requirement type (visa/medical = country-level)
    """

    def __init__(self, user):
        self.user = user
        self.created_instances = []
        self.updated_instances = []
        self.skipped_instances = []

    @transaction.atomic
    def ingest_shortlist(self, shortlist):
        """
        Create RequirementInstance for each requirement based on shortlist

        Args:
            shortlist: QuerySet or list of ShortlistItem objects

        Returns:
            dict: Statistics about ingestion
        """
        self.created_instances = []
        self.updated_instances = []
        self.skipped_instances = []

        # Get unique countries from shortlist
        universities = [item.university for item in shortlist]
        countries = set([uni.location_country for uni in universities if uni.location_country])

        # === 1. GLOBAL REQUIREMENTS (passport, IELTS, transcripts) ===
        self._ingest_global_requirements()

        # === 2. COUNTRY-LEVEL REQUIREMENTS (visa, medical, finance) ===
        for country in countries:
            self._ingest_country_requirements(country, universities)

        # === 3. UNIVERSITY-LEVEL REQUIREMENTS (portal, essays) ===
        for university in universities:
            self._ingest_university_requirements(university)

        # === 4. SCHOLARSHIP REQUIREMENTS (if applicable) ===
        if self._check_scholarship_intent():
            self._ingest_scholarship_requirements()

        return {
            'created': len(self.created_instances),
            'updated': len(self.updated_instances),
            'skipped': len(self.skipped_instances),
            'total': len(self.created_instances) + len(self.updated_instances),
        }

    def _ingest_global_requirements(self):
        """
        Ingest global requirements (passport, IELTS, transcripts)

        Global requirements apply to all universities equally.
        """
        global_template_keys = [
            'passport_validity',
            'ielts_score',
            'toefl_score',
            'transcripts',
            'recommendation_letters',
        ]

        for template_key in global_template_keys:
            try:
                template = RequirementTemplate.objects.get(key=template_key)

                instance, created = RequirementInstance.objects.update_or_create(
                    user=self.user,
                    university=None,  # No university for global
                    country='',  # No country for global
                    scope_level='global',
                    requirement_key=template_key,
                    track=self._get_user_track(),
                    defaults={
                        'status': 'required',
                        'verification_level': 'assumed',
                        'source': 'university_rule',
                        'source_domain_type': 'other',
                        'evidence_fields': template.default_evidence_fields,
                        'notes': f"Global requirement for all applications",
                    }
                )

                if created:
                    self.created_instances.append(instance)
                else:
                    self.updated_instances.append(instance)

            except RequirementTemplate.DoesNotExist:
                self.skipped_instances.append(f"Global template not found: {template_key}")

    def _ingest_country_requirements(self, country, universities):
        """
        Ingest country-level requirements (visa, medical, finance)

        CRITICAL: These use university=None, scope_level='country'
        They apply to ALL universities in this country.
        """
        # Get country pack
        try:
            country_pack = RequirementPack.objects.get(
                pack_type='country',
                country=country,
                is_active=True
            )
        except RequirementPack.DoesNotExist:
            self.skipped_instances.append(f"Country pack not found: {country}")
            return

        for template_key in country_pack.requirement_templates:
            try:
                template = RequirementTemplate.objects.get(key=template_key)

                # Find applicable rule for this country
                rule = RequirementRule.objects.filter(
                    template=template,
                    scope='country',
                    country=country,
                    is_active=True
                ).first()

                instance, created = RequirementInstance.objects.update_or_create(
                    user=self.user,
                    university=None,  # CRITICAL: None for country-level
                    country=country,
                    scope_level='country',
                    requirement_key=template_key,
                    track=self._get_user_track(),
                    defaults={
                        'status': 'required',
                        'verification_level': 'official' if rule else 'assumed',
                        'source': 'country_rule',
                        'source_domain_type': 'government',
                        'evidence_fields': template.default_evidence_fields,
                        'notes': f"Country-level requirement for {country}",
                    }
                )

                if created:
                    self.created_instances.append(instance)
                else:
                    self.updated_instances.append(instance)

            except RequirementTemplate.DoesNotExist:
                self.skipped_instances.append(f"Country template not found: {template_key}")

    def _ingest_university_requirements(self, university):
        """
        Ingest university-specific requirements (portal, essays, etc.)

        These are specific to each university.
        """
        university_rules = RequirementRule.objects.filter(
            scope='university',
            university=university,
            is_active=True
        )

        for rule in university_rules:
            # Check if rule conditions are met
            if not self._check_conditions(rule.conditions):
                continue

            template = rule.template

            instance, created = RequirementInstance.objects.update_or_create(
                user=self.user,
                university=university,
                scope_level='university',
                requirement_key=template.key,
                track=self._get_user_track(),
                defaults={
                    'status': 'required',
                    'verification_level': 'official',
                    'source': 'university_rule',
                    'source_domain_type': 'university',
                    'evidence_fields': rule.overrides.get('evidence_fields', template.default_evidence_fields),
                    'notes': f"University-specific requirement for {university.name}",
                }
            )

            if created:
                self.created_instances.append(instance)
            else:
                self.updated_instances.append(instance)

        # Must-have ingestion: Create basic portal requirement if none exists
        if not university_rules.exists():
            self._create_basic_university_requirement(university)

    def _create_basic_university_requirement(self, university):
        """
        Create basic university requirement if no specific rules exist

        This is "must-have" ingestion for scalability.
        """
        template_key = 'application_portal'

        # Create template on-the-fly if it doesn't exist
        template, _ = RequirementTemplate.objects.get_or_create(
            key=template_key,
            defaults={
                'category': 'apply',
                'title': 'Application Portal',
                'description': f'Application portal for {university.name}',
                'default_evidence_fields': ['account_created', 'form_started'],
            }
        )

        instance, created = RequirementInstance.objects.update_or_create(
            user=self.user,
            university=university,
            scope_level='university',
            requirement_key=template_key,
            track=self._get_user_track(),
            defaults={
                'status': 'unknown',  # Unknown because we haven't verified portal details
                'verification_level': 'assumed',
                'source': 'university_rule',
                'source_domain_type': 'university',
                'evidence_fields': template.default_evidence_fields,
                'notes': 'Basic portal requirement - verify details',
            }
        )

        if created:
            self.created_instances.append(instance)
        else:
            self.updated_instances.append(instance)

    def _ingest_scholarship_requirements(self):
        """
        Ingest scholarship requirements (tax, property, income)

        Only applied if user has scholarship intent.
        """
        try:
            scholarship_pack = RequirementPack.objects.get(
                pack_type='scholarship',
                is_active=True
            )
        except RequirementPack.DoesNotExist:
            self.skipped_instances.append("Scholarship pack not found")
            return

        for template_key in scholarship_pack.requirement_templates:
            try:
                template = RequirementTemplate.objects.get(key=template_key)

                instance, created = RequirementInstance.objects.update_or_create(
                    user=self.user,
                    university=None,
                    country='',
                    scope_level='scholarship',
                    requirement_key=template_key,
                    track=self._get_user_track(),
                    defaults={
                        'status': 'required',
                        'verification_level': 'assumed',
                        'source': 'scholarship_rule',
                        'source_domain_type': 'other',
                        'evidence_fields': template.default_evidence_fields,
                        'notes': 'Scholarship financial requirement',
                    }
                )

                if created:
                    self.created_instances.append(instance)
                else:
                    self.updated_instances.append(instance)

            except RequirementTemplate.DoesNotExist:
                self.skipped_instances.append(f"Scholarship template not found: {template_key}")

    def _check_conditions(self, conditions):
        """
        Check if rule conditions are met

        Args:
            conditions: dict of conditions (e.g., {"scholarship": true})

        Returns:
            bool: True if conditions are met
        """
        if not conditions:
            return True

        # Check scholarship condition
        if conditions.get('scholarship'):
            return self._check_scholarship_intent()

        # Add more condition checks as needed

        return True

    def _check_scholarship_intent(self):
        """
        Check if user intends to apply for scholarships

        Returns:
            bool: True if user has scholarship intent
        """
        # Check user profile for scholarship intent
        profile = getattr(self.user, 'profile', None)
        if profile:
            return getattr(profile, 'scholarship_intent', False)
        return False

    def _get_user_track(self):
        """
        Get user's academic track (direct vs foundation)

        Returns:
            str: Track type
        """
        profile = getattr(self.user, 'profile', None)
        if profile:
            return getattr(profile, 'track', 'direct')
        return 'direct'


class RequirementEvaluator:
    """
    Evaluates requirement satisfaction based on profile and documents

    This is the MISSING LAYER between requirement ingestion and task composition.
    """

    def __init__(self, user):
        self.user = user

    def evaluate_requirements(self, requirement_instances):
        """
        Evaluate each requirement instance and update status

        Args:
            requirement_instances: QuerySet of RequirementInstance

        Returns:
            dict: Statistics about evaluation
        """
        evaluated = 0
        satisfied = 0
        missing = 0
        unknown = 0
        not_required = 0

        for instance in requirement_instances:
            old_status = instance.status

            # Evaluate based on requirement_key
            new_status, new_verification, notes = self._evaluate_instance(instance)

            # Update if changed
            if new_status != old_status:
                instance.status = new_status
                if new_verification:
                    instance.verification_level = new_verification
                if notes:
                    instance.notes = notes
                instance.save()

            # Count statistics
            evaluated += 1
            if new_status == 'satisfied':
                satisfied += 1
            elif new_status == 'missing':
                missing += 1
            elif new_status == 'unknown':
                unknown += 1
            elif new_status == 'not_required':
                not_required += 1

        return {
            'evaluated': evaluated,
            'satisfied': satisfied,
            'missing': missing,
            'unknown': unknown,
            'not_required': not_required
        }

    def _evaluate_instance(self, instance):
        """
        Evaluate a single requirement instance

        Returns:
            tuple: (status, verification_level, notes)
        """
        requirement_key = instance.requirement_key

        # === TEST SCORES ===
        # Global keys
        if requirement_key == 'ielts_score':
            return self._evaluate_ielts(instance)
        elif requirement_key == 'toefl_score':
            return self._evaluate_toefl(instance)
        elif requirement_key == 'sat_score':
            return self._evaluate_sat(instance)
        elif requirement_key == 'act_score':
            return self._evaluate_act(instance)

        # University-specific aliases (map to same evaluation)
        elif requirement_key == 'ielts_academic':
            return self._evaluate_ielts(instance)
        elif requirement_key == 'toefl_ibit':
            return self._evaluate_toefl(instance)
        elif requirement_key == 'academic_transcripts':
            return self._evaluate_transcripts(instance)

        # === DOCUMENTS ===
        elif requirement_key == 'passport_validity':
            return self._evaluate_passport(instance)
        elif requirement_key == 'transcripts':
            return self._evaluate_transcripts(instance)
        elif requirement_key == 'recommendation_letters':
            return self._evaluate_recommendations(instance)

        # === UNIVERSITY-SPECIFIC ===
        elif requirement_key == 'application_portal':
            return self._evaluate_portal(instance)
        elif requirement_key == 'personal_statement':
            return self._evaluate_essay(instance)
        elif requirement_key == 'cv_resume':
            return self._evaluate_cv(instance)
        elif requirement_key == 'portfolio':
            return self._evaluate_portfolio(instance)

        # Default: keep current status
        return (instance.status, instance.verification_level, instance.notes)

    def _evaluate_ielts(self, instance):
        """Evaluate IELTS requirement"""
        try:
            from university_profile.models import UniversitySeekerProfile
            profile = UniversitySeekerProfile.objects.filter(user=self.user).first()
            if not profile:
                return ('unknown', 'assumed', 'No profile found')

            ielts_score = getattr(profile, 'ielts_score', None)

            # Determine minimum score required
            min_score = 6.5  # Default threshold

            # Check if this is a university-specific requirement with a minimum
            if instance.university and hasattr(instance.university, 'min_ielts_score'):
                uni_min = instance.university.min_ielts_score
                if uni_min:
                    min_score = uni_min

            # Check if user has IELTS score meeting the requirement
            if ielts_score and ielts_score >= min_score:
                # Check if TRF uploaded
                try:
                    from document_vault.models import DocumentVaultItem
                    trf_uploaded = DocumentVaultItem.objects.filter(
                        user=self.user,
                        document_type='ielts_trf',
                        status='verified'
                    ).exists()

                    if trf_uploaded:
                        return ('satisfied', 'vendor', f'IELTS {ielts_score} verified (TRF uploaded)')
                    else:
                        return ('satisfied', 'user_reported', f'IELTS {ielts_score} reported (TRF not yet uploaded)')
                except ImportError:
                    # DocumentVault not available
                    return ('satisfied', 'user_reported', f'IELTS {ielts_score} reported')

            # No IELTS score or below threshold
            return ('missing', 'assumed', f'IELTS {min_score}+ needed (current: {ielts_score or "none"})')

        except Exception as e:
            return ('unknown', 'assumed', f'Evaluation error: {str(e)}')

    def _evaluate_toefl(self, instance):
        """Evaluate TOEFL requirement"""
        try:
            from university_profile.models import UniversitySeekerProfile
            profile = UniversitySeekerProfile.objects.filter(user=self.user).first()
            if not profile:
                return ('unknown', 'assumed', 'No profile found')

            toefl_score = getattr(profile, 'toefl_score', None)
            ielts_score = getattr(profile, 'ielts_score', None)

            # CRITICAL: If user has IELTS, TOEFL is not required
            if ielts_score and ielts_score >= 6.5:
                return ('not_required', 'assumed', f'IELTS {ielts_score} satisfies English requirement')

            # Check TOEFL score
            if toefl_score and toefl_score >= 80:
                try:
                    from document_vault.models import DocumentVaultItem
                    trf_uploaded = DocumentVaultItem.objects.filter(
                        user=self.user,
                        document_type='toefl_trf',
                        status='verified'
                    ).exists()

                    if trf_uploaded:
                        return ('satisfied', 'vendor', f'TOEFL {toefl_score} verified (TRF uploaded)')
                    else:
                        return ('satisfied', 'user_reported', f'TOEFL {toefl_score} reported (TRF not yet uploaded)')
                except ImportError:
                    return ('satisfied', 'user_reported', f'TOEFL {toefl_score} reported')

            # No TOEFL score
            return ('missing', 'assumed', f'TOEFL score needed (current: {toefl_score or "none"})')

        except Exception as e:
            return ('unknown', 'assumed', f'Evaluation error: {str(e)}')

    def _evaluate_sat(self, instance):
        """Evaluate SAT requirement"""
        try:
            from university_profile.models import UniversitySeekerProfile
            profile = UniversitySeekerProfile.objects.filter(user=self.user).first()
            if not profile:
                return ('unknown', 'assumed', 'No profile found')

            sat_score = getattr(profile, 'sat_score', None)

            # Check if user has SAT score
            if sat_score and sat_score >= 1200:
                return ('satisfied', 'user_reported', f'SAT {sat_score} reported')

            return ('missing', 'assumed', f'SAT score needed (current: {sat_score or "none"})')

        except Exception as e:
            return ('unknown', 'assumed', f'Evaluation error: {str(e)}')

    def _evaluate_act(self, instance):
        """Evaluate ACT requirement"""
        try:
            from university_profile.models import UniversitySeekerProfile
            profile = UniversitySeekerProfile.objects.filter(user=self.user).first()
            if not profile:
                return ('unknown', 'assumed', 'No profile found')

            act_score = getattr(profile, 'act_score', None)

            # Check if user has ACT score
            if act_score and act_score >= 24:
                return ('satisfied', 'user_reported', f'ACT {act_score} reported')

            return ('missing', 'assumed', f'ACT score needed (current: {act_score or "none"})')

        except Exception as e:
            return ('unknown', 'assumed', f'Evaluation error: {str(e)}')

    def _evaluate_passport(self, instance):
        """Evaluate passport requirement"""
        try:
            # Check if passport document uploaded
            try:
                from document_vault.models import DocumentVaultItem
                passport_uploaded = DocumentVaultItem.objects.filter(
                    user=self.user,
                    document_type='passport',
                    status='verified'
                ).exists()

                if passport_uploaded:
                    return ('satisfied', 'vendor', 'Passport uploaded and verified')
            except ImportError:
                pass  # DocumentVault not available

            return ('missing', 'assumed', 'Passport document required')

        except Exception as e:
            return ('unknown', 'assumed', f'Evaluation error: {str(e)}')

    def _evaluate_transcripts(self, instance):
        """Evaluate transcripts requirement"""
        try:
            # Check if transcripts uploaded
            try:
                from document_vault.models import DocumentVaultItem
                transcripts_uploaded = DocumentVaultItem.objects.filter(
                    user=self.user,
                    document_type='transcripts',
                    status='verified'
                ).exists()

                if transcripts_uploaded:
                    return ('satisfied', 'vendor', 'Transcripts uploaded and verified')
            except ImportError:
                pass  # DocumentVault not available

            return ('missing', 'assumed', 'Official transcripts required')

        except Exception as e:
            return ('unknown', 'assumed', f'Evaluation error: {str(e)}')

    def _evaluate_recommendations(self, instance):
        """Evaluate recommendation letters requirement"""
        try:
            # Count verified recommendation letters
            try:
                from document_vault.models import DocumentVaultItem
                rec_count = DocumentVaultItem.objects.filter(
                    user=self.user,
                    document_type='recommendation_letter',
                    status='verified'
                ).count()

                if rec_count >= 2:
                    return ('satisfied', 'vendor', f'{rec_count} recommendation letters verified')
                elif rec_count == 1:
                    return ('missing', 'assumed', f'1 of 2 recommendations received (1 more needed)')
            except ImportError:
                pass  # DocumentVault not available

            return ('missing', 'assumed', f'2 recommendation letters required (0 received)')

        except Exception as e:
            return ('unknown', 'assumed', f'Evaluation error: {str(e)}')

    def _evaluate_portal(self, instance):
        """Evaluate application portal requirement"""
        # Portal tasks are never "satisfied" - they're action items
        # But we can check if account created
        try:
            try:
                from document_vault.models import DocumentVaultItem
                account_created = DocumentVaultItem.objects.filter(
                    user=self.user,
                    university=instance.university,
                    document_type='portal_account',
                    status='verified'
                ).exists()

                if account_created:
                    return ('missing', 'user_reported', f'Account created for {instance.university.name} - complete application')
            except ImportError:
                pass  # DocumentVault not available

            return ('required', 'assumed', f'Application portal for {instance.university.name}')

        except Exception as e:
            return ('unknown', 'assumed', f'Evaluation error: {str(e)}')

    def _evaluate_essay(self, instance):
        """Evaluate personal statement/essay requirement"""
        # Essays are action items - check if document uploaded
        try:
            try:
                from document_vault.models import DocumentVaultItem
                essay_uploaded = DocumentVaultItem.objects.filter(
                    user=self.user,
                    university=instance.university,
                    document_type='personal_statement',
                    status='verified'
                ).exists()

                if essay_uploaded:
                    return ('satisfied', 'user_reported', f'Personal statement uploaded for {instance.university.name}')
            except ImportError:
                pass  # DocumentVault not available

            uni_name = instance.university.name if instance.university else 'university'
            return ('required', 'assumed', f'Personal statement required for {uni_name}')

        except Exception as e:
            return ('unknown', 'assumed', f'Evaluation error: {str(e)}')

    def _evaluate_cv(self, instance):
        """Evaluate CV/resume requirement"""
        # CV is action item - check if document uploaded
        try:
            try:
                from document_vault.models import DocumentVaultItem
                cv_uploaded = DocumentVaultItem.objects.filter(
                    user=self.user,
                    document_type='cv_resume',
                    status='verified'
                ).exists()

                if cv_uploaded:
                    return ('satisfied', 'user_reported', 'CV/Resume uploaded')
            except ImportError:
                pass  # DocumentVault not available

            return ('required', 'assumed', 'CV/Resume required')

        except Exception as e:
            return ('unknown', 'assumed', f'Evaluation error: {str(e)}')

    def _evaluate_portfolio(self, instance):
        """Evaluate portfolio requirement"""
        # Portfolio is action item - check if document uploaded
        try:
            try:
                from document_vault.models import DocumentVaultItem
                portfolio_uploaded = DocumentVaultItem.objects.filter(
                    user=self.user,
                    university=instance.university,
                    document_type='portfolio',
                    status='verified'
                ).exists()

                if portfolio_uploaded:
                    return ('satisfied', 'user_reported', f'Portfolio uploaded for {instance.university.name}')
            except ImportError:
                pass  # DocumentVault not available

            uni_name = instance.university.name if instance.university else 'university'
            return ('required', 'assumed', f'Portfolio required for {uni_name}')

        except Exception as e:
            return ('unknown', 'assumed', f'Evaluation error: {str(e)}')


def evaluate_user_requirements(user, requirement_instances):
    """
    Convenience function to evaluate requirements for a user

    Args:
        user: User instance
        requirement_instances: QuerySet of RequirementInstance

    Returns:
        dict: Statistics about evaluation
    """
    evaluator = RequirementEvaluator(user)
    return evaluator.evaluate_requirements(requirement_instances)


def ingest_user_requirements(user, shortlist):
    """
    Convenience function to ingest requirements for a user

    Args:
        user: User instance
        shortlist: QuerySet or list of ShortlistItem objects

    Returns:
        dict: Statistics about ingestion
    """
    service = RequirementIngestionService(user)
    return service.ingest_shortlist(shortlist)
