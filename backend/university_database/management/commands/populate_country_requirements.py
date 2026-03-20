from django.core.management.base import BaseCommand

from university_database.models import CountryRequirement


class Command(BaseCommand):
    help = "Populate country admission requirements"

    def handle(self, *args, **options):
        requirements = [
            # Italy - 12-year system required
            CountryRequirement(
                country="Italy",
                education_system_required="12-year or IB",
                foundation_required=True,
                foundation_duration="1 year (10 months)",
                alternative_paths="Study in 12-year system country first, then transfer",
                language_requirement="IELTS 6.0+ / Italian B2 for Italian-taught",
                special_rules="Legal translation of documents required; Italian consulate verification; Pre-enrollment visa required",
                application_system="Direct (university-specific)",
            ),
            # United Kingdom - 13-year (A-Levels) or IB required
            CountryRequirement(
                country="United Kingdom",
                education_system_required="13-year (A-Levels) or IB",
                foundation_required=True,
                foundation_duration="1 year",
                alternative_paths="A-Levels via Cambridge International; Foundation programs at universities",
                language_requirement="IELTS 6.5-7.5 depending on university",
                special_rules="UCAS application system; Personal statement required; References required; Interview may be required",
                application_system="UCAS",
            ),
            # USA - 12-year required
            CountryRequirement(
                country="USA",
                education_system_required="12-year (High School Diploma)",
                foundation_required=False,
                foundation_duration="",
                alternative_paths="None generally",
                language_requirement="TOEFL 80+ / IELTS 6.5+ / Duolingo 105+",
                special_rules="Common App or Coalition App; SAT/ACT often optional but recommended; Early Decision/Early Action available",
                application_system="Common App, Coalition App, or Direct",
            ),
            # Germany - 13-year (Abitur) required
            CountryRequirement(
                country="Germany",
                education_system_required="13-year (Abitur)",
                foundation_required=True,
                foundation_duration="1 year Studienkolleg + 2 semesters",
                alternative_paths="Direct admission with 3 years of university study in home country; Studienkolleg for qualified applicants",
                language_requirement="German B2-B3 for German-taught / IELTS 6.5+ for English-taught",
                special_rules="APS certificate required from German embassy; uni-assist application; Some states have semester fee",
                application_system="Uni-Assist (for public universities)",
            ),
            # Netherlands - 12-year (VWO) or IB required
            CountryRequirement(
                country="Netherlands",
                education_system_required="12-year (VWO) or IB",
                foundation_required=True,
                foundation_duration="1 year",
                alternative_paths="HBO (applied sciences) accepts 11-year with foundation",
                language_requirement="IELTS 6.0+ / TOEFL 80+",
                special_rules="Studielink application system; Numerus Fixus for selection; Motivation letter required",
                application_system="Studielink",
            ),
            # China - Gaokao required
            CountryRequirement(
                country="China",
                education_system_required="12-year (Gaokao)",
                foundation_required=False,
                foundation_duration="",
                alternative_paths="None generally",
                language_requirement="HSK 5-6 for Chinese-taught / IELTS/TOEFL for English-taught",
                special_rules="CUCAS application system; Physical examination required; Visa application (X1/X2)",
                application_system="CUCAS",
            ),
            # Canada - 12-year required
            CountryRequirement(
                country="Canada",
                education_system_required="12-year (High School Diploma)",
                foundation_required=False,
                foundation_duration="",
                alternative_paths="None generally",
                language_requirement="IELTS 6.5+ / TOEFL 80+",
                special_rules="OUAC (Ontario) or direct application; Some provinces require specific course prerequisites",
                application_system="OUAC (Ontario), Direct (other provinces)",
            ),
            # Australia - 12-year required
            CountryRequirement(
                country="Australia",
                education_system_required="12-year",
                foundation_required=False,
                foundation_duration="",
                alternative_paths="None generally",
                language_requirement="IELTS 6.5+ / TOEFL 79+",
                special_rules="Direct application to universities; ATAR system for domestic students; VTAC for some states",
                application_system="Direct (state-specific), UAC (some states)",
            ),
            # Switzerland - 12-year required
            CountryRequirement(
                country="Switzerland",
                education_system_required="12-year (Matura)",
                foundation_required=True,
                foundation_duration="1 year",
                alternative_paths="EPFL/ETH Zurich have entrance exams",
                language_requirement="German/French/English depending on region",
                special_rules="Application directly to universities; Some cantons have quotas",
                application_system="Direct",
            ),
            # Kazakhstan - 11-year system (home country)
            CountryRequirement(
                country="Kazakhstan",
                education_system_required="11-year",
                foundation_required=False,
                foundation_duration="",
                alternative_paths="None for local students",
                language_requirement="Varies by program (Kazakh/Russian/English)",
                special_rules="Entarak (ENT) exam for local universities; International applicants need different process",
                application_system="Direct (university-specific)",
            ),
        ]

        created_count = 0
        for req in requirements:
            obj, created = CountryRequirement.objects.get_or_create(
                country=req.country,
                defaults={
                    "education_system_required": req.education_system_required,
                    "foundation_required": req.foundation_required,
                    "foundation_duration": req.foundation_duration,
                    "alternative_paths": req.alternative_paths,
                    "language_requirement": req.language_requirement,
                    "special_rules": req.special_rules,
                    "application_system": req.application_system,
                },
            )
            if created:
                created_count += 1
                self.stdout.write(f"✅ Created requirements for {req.country}\n")
            else:
                self.stdout.write(f"⏭️  Already exists: {req.country}\n")

        self.stdout.write(f"\n✅ Done! Processed {len(requirements)} countries.\n")
