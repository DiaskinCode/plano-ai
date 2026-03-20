"""
Management Command: Load Essay Templates

Loads default essay templates into the database.
Run: python manage.py load_essay_templates
"""

from django.core.management.base import BaseCommand
from todos.essay_models import EssayTemplate
from todos.essay_templates_data import ESSAY_TEMPLATES


class Command(BaseCommand):
    help = 'Load default essay templates into the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            dest='force',
            help='Update existing templates instead of skipping them',
        )

    def handle(self, *args, **options):
        """Load essay templates from data file"""
        force = options.get('force', False)

        self.stdout.write(self.style.SUCCESS('Loading essay templates...'))

        created_count = 0
        updated_count = 0
        skipped_count = 0

        for template_data in ESSAY_TEMPLATES:
            template_name = template_data['name']

            try:
                template, created = EssayTemplate.objects.get_or_create(
                    name=template_name,
                    defaults=template_data
                )

                if created:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'  ✓ Created: {template_name}')
                    )
                elif force:
                    # Update existing template
                    for key, value in template_data.items():
                        setattr(template, key, value)
                    template.save()
                    updated_count += 1
                    self.stdout.write(
                        self.style.WARNING(f'  ↻ Updated: {template_name}')
                    )
                else:
                    skipped_count += 1
                    self.stdout.write(
                        self.style.NOTICE(f'  ⊘ Skipped: {template_name} (already exists)')
                    )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'  ✗ Error loading {template_name}: {str(e)}')
                )

        # Summary
        total = len(ESSAY_TEMPLATES)
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('Essay Templates Loading Complete!'))
        self.stdout.write(f'Total templates: {total}')
        self.stdout.write(self.style.SUCCESS(f'Created: {created_count}'))
        if updated_count > 0:
            self.stdout.write(self.style.WARNING(f'Updated: {updated_count}'))
        if skipped_count > 0:
            self.stdout.write(self.style.NOTICE(f'Skipped: {skipped_count}'))
        self.stdout.write('='*60)

        # Show all templates in database
        all_templates = EssayTemplate.objects.all()
        self.stdout.write(f'\nTotal templates in database: {all_templates.count()}')
        for template in all_templates.order_by('order'):
            self.stdout.write(f'  • {template.icon} {template.name} ({template.get_essay_type_display()})')
