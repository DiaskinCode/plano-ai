"""
Django management command to seed the University database from existing data.

Usage:
    python manage.py seed_universities [--count N] [--clear]

Options:
    --count N: Number of universities to import (default: 200)
    --clear: Clear existing universities before importing
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.dateparse import parse_date
from datetime import datetime, timedelta
from university_database.models import University
import sys


class Command(BaseCommand):
    help = 'Seed universities from the existing university_database.py'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=200,
            help='Number of universities to import (default: 200)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing universities before importing'
        )

    def handle(self, *args, **options):
        count = options['count']
        clear = options['clear']

        if clear:
            self.stdout.write(self.style.WARNING('Clearing existing universities...'))
            University.objects.all().delete()

        # Import the existing database
        try:
            from ai.onboarding_services.university_database import UNIVERSITY_DATABASE
        except ImportError:
            self.stdout.write(self.style.ERROR('Could not import UNIVERSITY_DATABASE'))
            return

        total = len(UNIVERSITY_DATABASE)
        to_import = min(count, total)

        self.stdout.write(f'Found {total} universities in database. Will import {to_import}.')

        # Get a subset of universities
        university_items = list(UNIVERSITY_DATABASE.items())[:to_import]

        created_count = 0
        updated_count = 0
        error_count = 0

        with transaction.atomic():
            for short_name, data in university_items:
                try:
                    # Map the old data structure to new model
                    university, created = University.objects.update_or_create(
                        short_name=short_name,
                        defaults={
                            'name': data.get('name', short_name),
                            'location_country': data.get('location', {}).get('country', 'USA'),
                            'location_state': data.get('location', {}).get('state', ''),
                            'location_city': data.get('location', {}).get('city', ''),
                            'campus_type': self._infer_campus_type(data.get('location', {}).get('city', '')),
                            'institution_type': self._map_institution_type(data.get('type', 'private_research')),
                            'setting': self._infer_setting(data),
                            'undergraduate_enrollment': data.get('enrollment', 15000),

                            # Admissions
                            'acceptance_rate': data.get('acceptance_rate', 10.0),
                            'sat_required': True,
                            'sat_optional': data.get('test_optional', False),
                            'sat_25th': data.get('sat_25th'),
                            'sat_75th': data.get('sat_75th'),
                            'sat_avg': data.get('avg_sat'),
                            'act_required': True,
                            'act_optional': data.get('test_optional', False),
                            'act_25th': data.get('act_25th'),
                            'act_75th': data.get('act_75th'),
                            'act_avg': data.get('avg_act'),

                            # Deadlines
                            'early_decision_deadline': self._parse_deadline(data.get('early_decision')),
                            'early_action_deadline': self._parse_deadline(
                                data.get('early_action') or data.get('restrictive_early_action') or data.get('single_choice_early_action')
                            ),
                            'regular_decision_deadline': self._parse_rd_deadline(data.get('application_deadline')),
                            'rolling_admissions': data.get('rolling_admissions', False),

                            # Academic Programs
                            'popular_majors': data.get('popular_majors', []),
                            'all_majors': self._expand_majors(data.get('popular_majors', [])),
                            'all_majors_normalized': self._normalize_majors(data.get('popular_majors', [])),
                            'strength_programs': data.get('specialties', []),
                            'strength_programs_normalized': self._normalize_list(data.get('specialties', [])),

                            # Costs
                            'tuition_in_state': data.get('tuition_per_year', 50000),
                            'tuition_out_of_state': data.get('tuition_per_year', 50000),
                            'room_board': int(data.get('tuition_per_year', 50000) * 0.25),
                            'total_cost_per_year': int(data.get('tuition_per_year', 50000) * 1.25),

                            # Financial Aid (defaults for MVP - needs manual verification)
                            'need_based_aid': data.get('need_blind', False) or data.get('need_aware', False),
                            'need_blind': data.get('need_blind', False),
                            'need_aware': data.get('need_aware', False),
                            'merit_aid_offered': data.get('merit_aid', False),
                            'international_aid': data.get('international_aid', False),
                            'aid_verified': False,  # Needs verification!

                            # Rankings
                            'us_news_ranking': data.get('ranking'),

                            # Campus characteristics
                            'research_intensity': 'very_high' if 'research' in data.get('type', '') else 'high',

                            # Metadata
                            'data_source': 'legacy_database',
                            'last_verified': None,
                        }
                    )

                    if created:
                        created_count += 1
                    else:
                        updated_count += 1

                    # Progress indicator
                    if (created_count + updated_count) % 50 == 0:
                        self.stdout.write(f'  Processed {created_count + updated_count} universities...')

                except Exception as e:
                    error_count += 1
                    self.stdout.write(self.style.ERROR(f'Error importing {short_name}: {e}'))

        self.stdout.write(self.style.SUCCESS(f'\nSummary:'))
        self.stdout.write(f'  Created: {created_count}')
        self.stdout.write(f'  Updated: {updated_count}')
        self.stdout.write(f'  Errors: {error_count}')
        self.stdout.write(self.style.SUCCESS(f'\nTotal universities in database: {University.objects.count()}'))

    def _infer_campus_type(self, city):
        """Infer campus type from city name"""
        urban_cities = ['new york', 'boston', 'los angeles', 'chicago', 'san francisco', 'philadelphia', 'washington']
        city_lower = city.lower()
        for urban in urban_cities:
            if urban in city_lower:
                return 'urban'
        return 'suburban'

    def _map_institution_type(self, old_type):
        """Map old type to new institution_type"""
        if 'public' in old_type:
            return 'public'
        elif 'private' in old_type:
            return 'private'
        return 'private'

    def _infer_setting(self, data):
        """Infer setting size"""
        enrollment = data.get('enrollment', 15000)
        if enrollment < 5000:
            return 'small'
        elif enrollment < 15000:
            return 'medium'
        return 'large'

    def _parse_deadline(self, deadline_str):
        """Parse deadline string like 'Jan 1' or 'Nov 1' to date"""
        if not deadline_str:
            return None

        months = {
            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
            'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
        }

        try:
            parts = deadline_str.lower().split()
            if len(parts) >= 2:
                month = months.get(parts[0][:3])
                day = int(parts[1])
                year = datetime.now().year
                if month and day:
                    return datetime(year, month, day).date()
        except:
            pass

        return None

    def _parse_rd_deadline(self, deadline_str):
        """Parse regular decision deadline"""
        # Default to Jan 15 if not specified
        default_date = datetime(datetime.now().year, 1, 15).date()
        return self._parse_deadline(deadline_str) or default_date

    def _expand_majors(self, popular_majors):
        """Expand popular majors with related majors"""
        # For MVP, just use the popular majors
        # In future, this could map to a comprehensive list
        return popular_majors

    def _normalize_majors(self, majors):
        """Create lowercase version of majors for case-insensitive matching"""
        return [m.lower() for m in majors]

    def _normalize_list(self, items):
        """Normalize a list to lowercase"""
        return [str(item).lower() for item in items]
