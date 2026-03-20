"""
Django management command to generate basic requirement rules for all universities.

Usage:
    python manage.py generate_university_rules --dry-run
    python manage.py generate_university_rules
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from university_database.models import University
from requirements.models import RequirementTemplate, RequirementRule


class Command(BaseCommand):
    help = 'Generate basic requirement rules for all universities without rules'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without creating',
        )

    # Template PK mapping (matches database IDs)
    TEMPLATE_PK_MAP = {
        'application_portal': 18,
        'academic_transcripts': 4,
        'personal_statement': 6,
        'recommendation_letters': 7,
        'cv_resume': 5,
        'ielts_academic': 2,
        'toefl_ibit': 3,
        'portfolio': 8,
    }

    # Country-specific requirement patterns
    COUNTRY_PATTERNS = {
        'USA': [
            {'template': 'application_portal', 'priority': 'info'},
            {'template': 'academic_transcripts', 'priority': 'blocker'},
            {'template': 'personal_statement', 'priority': 'blocker', 'title_suffix': 'Supplemental Essays'},
            {'template': 'recommendation_letters', 'priority': 'blocker'},
            {'template': 'cv_resume', 'priority': 'info'},
            {'template': 'ielts_academic', 'priority': 'warning'},
            {'template': 'toefl_ibit', 'priority': 'warning'},
        ],
        'UK': [
            {'template': 'application_portal', 'priority': 'info', 'title_override': 'UCAS Application'},
            {'template': 'academic_transcripts', 'priority': 'blocker'},
            {'template': 'personal_statement', 'priority': 'blocker'},
            {'template': 'recommendation_letters', 'priority': 'blocker'},
            {'template': 'ielts_academic', 'priority': 'warning'},
        ],
        'Italy': [
            {'template': 'application_portal', 'priority': 'info'},
            {'template': 'academic_transcripts', 'priority': 'blocker'},
            {'template': 'cv_resume', 'priority': 'blocker'},
            {'template': 'personal_statement', 'priority': 'blocker', 'title_suffix': 'Motivation Letter'},
            {'template': 'ielts_academic', 'priority': 'blocker'},
        ],
        'China': [
            {'template': 'application_portal', 'priority': 'info'},
            {'template': 'academic_transcripts', 'priority': 'blocker'},
            {'template': 'personal_statement', 'priority': 'info'},
            {'template': 'recommendation_letters', 'priority': 'blocker'},
        ],
        'Canada': [
            {'template': 'application_portal', 'priority': 'info'},
            {'template': 'academic_transcripts', 'priority': 'blocker'},
            {'template': 'personal_statement', 'priority': 'info'},
            {'template': 'recommendation_letters', 'priority': 'blocker'},
            {'template': 'cv_resume', 'priority': 'info'},
        ],
        'Switzerland': [
            {'template': 'application_portal', 'priority': 'info'},
            {'template': 'academic_transcripts', 'priority': 'blocker'},
            {'template': 'personal_statement', 'priority': 'blocker'},
            {'template': 'recommendation_letters', 'priority': 'blocker'},
            {'template': 'cv_resume', 'priority': 'info'},
            {'template': 'ielts_academic', 'priority': 'warning'},
        ],
        'Netherlands': [
            {'template': 'application_portal', 'priority': 'info'},
            {'template': 'academic_transcripts', 'priority': 'blocker'},
            {'template': 'personal_statement', 'priority': 'info'},
            {'template': 'cv_resume', 'priority': 'blocker'},
            {'template': 'ielts_academic', 'priority': 'blocker'},
        ],
        'Australia': [
            {'template': 'application_portal', 'priority': 'info'},
            {'template': 'academic_transcripts', 'priority': 'blocker'},
            {'template': 'personal_statement', 'priority': 'info'},
            {'template': 'recommendation_letters', 'priority': 'blocker'},
            {'template': 'cv_resume', 'priority': 'info'},
            {'template': 'ielts_academic', 'priority': 'blocker'},
        ],
    }

    # Architecture/design universities that need portfolio
    ARCHITECTURE_UNIVERSITIES = [
        43,  # Delft University of Technology
        54,  # Tongji University
        65,  # Sapienza University of Rome
        68,  # Polytechnic University of Milan (already has rules)
        73,  # Polytechnic University of Turin
    ]

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        
        # Get all universities
        all_universities = University.objects.all()
        total_unis = all_universities.count()
        
        # Find universities without rules
        unis_without_rules = []
        for uni in all_universities:
            rule_count = RequirementRule.objects.filter(university=uni).count()
            if rule_count == 0:
                unis_without_rules.append(uni)
        
        self.stdout.write(f"\n{'='*60}")
        self.stdout.write(f"Total universities: {total_unis}")
        self.stdout.write(f"Universities without rules: {len(unis_without_rules)}")
        self.stdout.write(f"{'='*60}\n")
        
        if len(unis_without_rules) == 0:
            self.stdout.write(self.style.SUCCESS("✅ All universities already have rules!"))
            return
        
        # Group universities by country
        universities_by_country = {}
        for uni in unis_without_rules:
            country = uni.location_country
            if country not in universities_by_country:
                universities_by_country[country] = []
            universities_by_country[country].append(uni)
        
        # Generate rules for each country
        all_rules = []
        total_rules = 0
        
        for country, universities in sorted(universities_by_country.items()):
            self.stdout.write(f"\n📍 {country}: {len(universities)} universities")
            
            # Get pattern for this country
            pattern = self.COUNTRY_PATTERNS.get(country, self.COUNTRY_PATTERNS['USA'])  # Default to USA
            
            for uni in universities:
                uni_rules = self._generate_rules_for_university(uni, pattern)
                all_rules.extend(uni_rules)
                total_rules += len(uni_rules)
        
        # Display summary
        self.stdout.write(f"\n{'='*60}")
        self.stdout.write(f"Total rules to create: {total_rules}")
        self.stdout.write(f"{'='*60}\n")
        
        # Show breakdown by country
        rules_by_country = {}
        for rule in all_rules:
            country = rule['country']
            if country not in rules_by_country:
                rules_by_country[country] = 0
            rules_by_country[country] += 1
        
        for country, count in sorted(rules_by_country.items()):
            self.stdout.write(f"  {country}: {count} rules")
        
        if dry_run:
            self.stdout.write(self.style.WARNING("\n🔍 DRY RUN - No changes made"))
            self.stdout.write("\nSample rules to create:")
            for rule in all_rules[:5]:
                self.stdout.write(f"  - {rule['university']}: {rule['title']} ({rule['priority']})")
            if len(all_rules) > 5:
                self.stdout.write(f"  ... and {len(all_rules) - 5} more")
        else:
            # Create the rules
            self.stdout.write(self.style.SUCCESS("\n✅ Creating rules..."))
            
            with transaction.atomic():
                for rule_data in all_rules:
                    rule = RequirementRule.objects.create(
                        template_id=rule_data['template_id'],
                        scope='university',
                        university_id=rule_data['university_id'],
                        country='',
                        conditions={},
                        overrides=rule_data.get('overrides', {}),
                        link_url=rule_data.get('link_url', ''),
                        priority=rule_data['priority'],
                        is_active=True,
                        created_at=timezone.now(),
                        updated_at=timezone.now(),
                    )
                    self.stdout.write(f"  Created: {rule_data['title']} for {rule_data['university']}")
            
            self.stdout.write(self.style.SUCCESS(f"\n✅ Successfully created {total_rules} requirement rules!"))

    def _generate_rules_for_university(self, uni, pattern):
        """Generate requirement rules for a single university."""
        rules = []
        
        for req in pattern:
            template_key = req['template']
            template_id = self.TEMPLATE_PK_MAP.get(template_key)
            
            if not template_id:
                self.stdout.write(self.style.WARNING(f"  ⚠️  Template not found: {template_key}"))
                continue
            
            # Build title
            template = RequirementTemplate.objects.get(pk=template_id)
            title = template.title
            
            if req.get('title_override'):
                title = req['title_override']
            elif req.get('title_suffix'):
                title = f"{uni.name} {req['title_suffix']}"
            
            # Build overrides
            overrides = {}
            if title != template.title:
                overrides['title'] = title
            
            rules.append({
                'template_id': template_id,
                'university_id': uni.id,
                'university': uni.name,
                'country': uni.location_country,
                'title': title,
                'priority': req['priority'],
                'overrides': overrides,
                'link_url': '',
            })
        
        # Add portfolio for architecture universities
        if uni.id in self.ARCHITECTURE_UNIVERSITIES:
            template_id = self.TEMPLATE_PK_MAP.get('portfolio')
            if template_id:
                template = RequirementTemplate.objects.get(pk=template_id)
                rules.append({
                    'template_id': template_id,
                    'university_id': uni.id,
                    'university': uni.name,
                    'country': uni.location_country,
                    'title': f"{uni.name} Architecture Portfolio",
                    'priority': 'blocker',
                    'overrides': {'title': f"{uni.name} Architecture Portfolio"},
                    'link_url': '',
                })
        
        return rules
