"""
Management command to seed requirement templates and packs
"""

from django.core.management.base import BaseCommand
from requirements.models import RequirementTemplate, RequirementRule, RequirementPack


class Command(BaseCommand):
    help = 'Seeds requirement templates, rules, and packs'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting requirement template seeding...'))

        # === REQUIREMENT TEMPLATES ===
        templates_data = [
            # Identity Documents
            {
                'key': 'passport_validity',
                'category': 'visa',
                'title': 'Valid Passport',
                'description': 'Passport must be valid for specified number of months after program end date',
                'default_evidence_fields': ['passport_expiry_date', 'passport_scan'],
                'default_link_url': '',
            },
            {
                'key': 'medical_exam',
                'category': 'medical',
                'title': 'Medical Examination',
                'description': 'Medical examination and vaccination requirements for student visa',
                'default_evidence_fields': ['medical_certificate', 'vaccination_records'],
                'default_link_url': '',
            },
            # Language Tests
            {
                'key': 'ielts_score',
                'category': 'docs',
                'title': 'IELTS Score',
                'description': 'International English Language Testing System score requirement',
                'default_evidence_fields': ['ielts_trf_number', 'test_date', 'overall_score', 'section_scores'],
                'default_link_url': 'https://www.ielts.org/',
            },
            {
                'key': 'toefl_score',
                'category': 'docs',
                'title': 'TOEFL Score',
                'description': 'Test of English as a Foreign Language score requirement',
                'default_evidence_fields': ['toefl_registration_number', 'test_date', 'total_score'],
                'default_link_url': 'https://www.ets.org/toefl',
            },
            # Academic Documents
            {
                'key': 'transcripts',
                'category': 'docs',
                'title': 'Official Transcripts',
                'description': 'Official academic transcripts from previous institutions',
                'default_evidence_fields': ['transcript_pdf', 'translation_if_needed'],
                'default_link_url': '',
            },
            {
                'key': 'recommendation_letters',
                'category': 'docs',
                'title': 'Letters of Recommendation',
                'description': 'Academic or professional recommendation letters',
                'default_evidence_fields': ['recommendation_letter_1', 'recommendation_letter_2', 'recommendation_letter_3'],
                'default_link_url': '',
            },
            # Finance
            {
                'key': 'finance_proof',
                'category': 'finance',
                'title': 'Proof of Financial Support',
                'description': 'Bank statements or sponsorship letters demonstrating ability to pay tuition and living expenses',
                'default_evidence_fields': ['bank_statement', 'sponsorship_letter', 'affidavit_of_support'],
                'default_link_url': '',
            },
            # Visa
            {
                'key': 'visa_application',
                'category': 'visa',
                'title': 'Student Visa Application',
                'description': 'Student visa application process for country',
                'default_evidence_fields': ['visa_form', 'passport_scan', 'photo', 'acceptance_letter'],
                'default_link_url': '',
            },
            {
                'key': 'translation_requirements',
                'category': 'docs',
                'title': 'Document Translation',
                'description': 'Official translation of documents not in required language',
                'default_evidence_fields': ['translated_document', 'translator_certificate'],
                'default_link_url': '',
            },
            # Post-Offer Templates (NEW)
            {
                'key': 'offer_letter',
                'category': 'offer',
                'title': 'University Offer Letter',
                'description': 'Official offer of admission from university',
                'default_evidence_fields': ['offer_letter_pdf', 'offer_response_deadline'],
                'default_link_url': '',
            },
            {
                'key': 'enrollment_deposit',
                'category': 'offer',
                'title': 'Enrollment Deposit',
                'description': 'Deposit to secure place in program',
                'default_evidence_fields': ['deposit_receipt', 'payment_confirmation', 'deposit_deadline'],
                'default_link_url': '',
            },
            {
                'key': 'visa_sponsor_cas',
                'category': 'offer',
                'title': 'CAS Confirmation (UK)',
                'description': 'Confirmation of Acceptance for Studies required for UK student visa',
                'default_evidence_fields': ['cas_document', 'cas_number'],
                'default_link_url': 'https://www.gov.uk/student-visa',
            },
            {
                'key': 'visa_sponsor_i20',
                'category': 'offer',
                'title': 'I-20 Form (USA)',
                'description': 'Certificate of Eligibility for Nonimmigrant Student Status',
                'default_evidence_fields': ['i20_form', 'sevis_id'],
                'default_link_url': 'https://studyinthestates.dhs.gov/',
            },
            # Scholarship Documents (NEW)
            {
                'key': 'tax_certificate',
                'category': 'scholarship',
                'title': 'Tax Certificate',
                'description': 'Tax return documents for scholarship eligibility',
                'default_evidence_fields': ['tax_return_document', 'tax_year'],
                'default_link_url': '',
            },
            {
                'key': 'property_proof',
                'category': 'scholarship',
                'title': 'Property Ownership Proof',
                'description': 'Property ownership documents for financial assessment',
                'default_evidence_fields': ['property_deed', 'property_valuation'],
                'default_link_url': '',
            },
            {
                'key': 'income_proof',
                'category': 'scholarship',
                'title': 'Income Proof',
                'description': 'Proof of household income for scholarship eligibility',
                'default_evidence_fields': ['income_certificate', 'employment_letter', 'payslips'],
                'default_link_url': '',
            },
            {
                'key': 'family_size',
                'category': 'scholarship',
                'title': 'Family Size Declaration',
                'description': 'Declaration of family size for scholarship calculation',
                'default_evidence_fields': ['household_registration', 'family_composition_document'],
                'default_link_url': '',
            },
        ]

        created_count = 0
        for template_data in templates_data:
            template, created = RequirementTemplate.objects.get_or_create(
                key=template_data['key'],
                defaults=template_data
            )
            if created:
                created_count += 1
                self.stdout.write(f'  ✓ Created template: {template.key}')

        self.stdout.write(self.style.SUCCESS(f'Created {created_count} requirement templates'))

        # === REQUIREMENT RULES (Country-Specific Overrides) ===
        rules_data = [
            # Passport validity rules
            {
                'template_key': 'passport_validity',
                'scope': 'country',
                'country': 'China',
                'overrides': {'min_passport_months': 18},
                'priority': 'blocker',
            },
            {
                'template_key': 'passport_validity',
                'scope': 'country',
                'country': 'UK',
                'overrides': {'min_passport_months': 6},
                'priority': 'blocker',
            },
            {
                'template_key': 'passport_validity',
                'scope': 'country',
                'country': 'USA',
                'overrides': {'min_passport_months': 6},
                'priority': 'blocker',
            },
            {
                'template_key': 'passport_validity',
                'scope': 'country',
                'country': 'Italy',
                'overrides': {'min_passport_months': 12},
                'priority': 'blocker',
            },
            {
                'template_key': 'passport_validity',
                'scope': 'country',
                'country': 'Netherlands',
                'overrides': {'min_passport_months': 3},
                'priority': 'blocker',
            },
            # Medical exam rules
            {
                'template_key': 'medical_exam',
                'scope': 'country',
                'country': 'China',
                'overrides': {
                    'specific_tests': ['chest_xray', 'blood_test', 'hiv_test'],
                    'authorized_hospitals': 'designated_hospitals_list'
                },
                'priority': 'blocker',
            },
            {
                'template_key': 'medical_exam',
                'scope': 'country',
                'country': 'UK',
                'overrides': {
                    'specific_tests': ['chest_xray', 'tuberculosis_screening'],
                    'authorized_clinics': 'uk_approved_clinics'
                },
                'priority': 'blocker',
            },
            {
                'template_key': 'medical_exam',
                'scope': 'country',
                'country': 'USA',
                'overrides': {
                    'vaccination_required': True,
                    'vaccines': ['mmr', 'covid19', 'meningitis']
                },
                'priority': 'warning',
            },
            # Finance proof rules
            {
                'template_key': 'finance_proof',
                'scope': 'country',
                'country': 'China',
                'overrides': {
                    'funds_must_be_in_bank': '6_months',
                    'minimum_amount_usd': 15000
                },
                'priority': 'blocker',
            },
            {
                'template_key': 'finance_proof',
                'scope': 'country',
                'country': 'UK',
                'overrides': {
                    'funds_must_be_in_bank': '28_days',
                    'minimum_amount_gbp': 13345
                },
                'priority': 'blocker',
            },
            {
                'template_key': 'finance_proof',
                'scope': 'country',
                'country': 'USA',
                'overrides': {
                    'funds_must_be_in_bank': '3_months',
                    'minimum_amount_usd': 20000
                },
                'priority': 'blocker',
            },
            # Translation requirements
            {
                'template_key': 'translation_requirements',
                'scope': 'country',
                'country': 'China',
                'overrides': {
                    'certified_translator_required': True,
                    'notarization_required': True
                },
                'priority': 'blocker',
            },
            {
                'template_key': 'translation_requirements',
                'scope': 'country',
                'country': 'Italy',
                'overrides': {
                    'certified_translator_required': True,
                    'italian_consulate_approval': True
                },
                'priority': 'blocker',
            },
            {
                'template_key': 'translation_requirements',
                'scope': 'country',
                'country': 'Netherlands',
                'overrides': {
                    'certified_translator_required': True,
                    'dutch_or_english_accepted': True
                },
                'priority': 'warning',
            },
        ]

        created_rules = 0
        for rule_data in rules_data:
            template_key = rule_data.pop('template_key')
            try:
                template = RequirementTemplate.objects.get(key=template_key)

                rule, created = RequirementRule.objects.get_or_create(
                    template=template,
                    scope=rule_data['scope'],
                    country=rule_data['country'],
                    defaults=rule_data
                )
                if created:
                    created_rules += 1
                    self.stdout.write(f'  ✓ Created rule: {template_key} -> {rule_data["country"]}')
            except RequirementTemplate.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'  ⚠ Template not found: {template_key}'))

        self.stdout.write(self.style.SUCCESS(f'Created {created_rules} requirement rules'))

        # === COUNTRY PACKS ===
        country_packs = [
            {
                'name': 'China Student Visa Pack',
                'pack_type': 'country',
                'country': 'China',
                'requirement_templates': [
                    'visa_application',
                    'finance_proof',
                    'medical_exam',
                    'translation_requirements',
                    'passport_validity',
                ],
                'priority': 100,
            },
            {
                'name': 'UK Student Visa Pack',
                'pack_type': 'country',
                'country': 'UK',
                'requirement_templates': [
                    'visa_application',
                    'finance_proof',
                    'medical_exam',
                    'translation_requirements',
                    'passport_validity',
                    'visa_sponsor_cas',  # Post-offer
                ],
                'priority': 100,
            },
            {
                'name': 'USA Student Visa Pack',
                'pack_type': 'country',
                'country': 'USA',
                'requirement_templates': [
                    'visa_application',
                    'finance_proof',
                    'medical_exam',
                    'passport_validity',
                    'visa_sponsor_i20',  # Post-offer
                ],
                'priority': 100,
            },
            {
                'name': 'Italy Student Visa Pack',
                'pack_type': 'country',
                'country': 'Italy',
                'requirement_templates': [
                    'visa_application',
                    'finance_proof',
                    'medical_exam',
                    'translation_requirements',
                    'passport_validity',
                ],
                'priority': 100,
            },
            {
                'name': 'Netherlands Student Visa Pack',
                'pack_type': 'country',
                'country': 'Netherlands',
                'requirement_templates': [
                    'visa_application',
                    'finance_proof',
                    'medical_exam',
                    'translation_requirements',
                    'passport_validity',
                ],
                'priority': 100,
            },
        ]

        created_packs = 0
        for pack_data in country_packs:
            pack, created = RequirementPack.objects.get_or_create(
                pack_type=pack_data['pack_type'],
                country=pack_data['country'],
                defaults=pack_data
            )
            if created:
                created_packs += 1
                self.stdout.write(f'  ✓ Created pack: {pack.name}')

        self.stdout.write(self.style.SUCCESS(f'Created {created_packs} country packs'))

        # === SCHOLARSHIP PACK ===
        scholarship_pack = {
            'name': 'Scholarship Financial Requirements',
            'pack_type': 'scholarship',
            'country': '',
            'requirement_templates': [
                'tax_certificate',
                'property_proof',
                'income_proof',
                'family_size',
            ],
            'conditions': {'scholarship_intent': True},
            'priority': 90,
        }

        pack, created = RequirementPack.objects.get_or_create(
            pack_type=scholarship_pack['pack_type'],
            country=scholarship_pack['country'],
            defaults=scholarship_pack
        )
        if created:
            self.stdout.write(f'  ✓ Created pack: {pack.name}')
            self.stdout.write(self.style.SUCCESS('Created scholarship pack'))
        else:
            self.stdout.write(self.style.WARNING('Scholarship pack already exists'))

        self.stdout.write(self.style.SUCCESS('✓ Template seeding completed successfully!'))
