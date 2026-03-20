from django.core.management.base import BaseCommand

from university_database.models import University


class Command(BaseCommand):
    help = "Update university logos only (remove broken campus photos)"

    def handle(self, *args, **options):
        # Using UI Avatars for logos - campus photos disabled for now
        universities_to_update = [
            {
                "short_name": "harvard",
                "logo_url": "https://ui-avatars.com/api/?name=Harvard&background=A41034&color=fff&size=128&bold=true",
                "campus_photo_url": "",
            },
            {
                "short_name": "mit",
                "logo_url": "https://ui-avatars.com/api/?name=MIT&background=A31F34&color=fff&size=128&bold=true",
                "campus_photo_url": "",
            },
            {
                "short_name": "stanford",
                "logo_url": "https://ui-avatars.com/api/?name=Stanford&background=8C1515&color=fff&size=128&bold=true",
                "campus_photo_url": "",
            },
            {
                "short_name": "yale",
                "logo_url": "https://ui-avatars.com/api/?name=Yale&background=00356B&color=fff&size=128&bold=true",
                "campus_photo_url": "",
            },
            {
                "short_name": "princeton",
                "logo_url": "https://ui-avatars.com/api/?name=Princeton&background=EE7F2D&color=fff&size=128&bold=true",
                "campus_photo_url": "",
            },
            {
                "short_name": "columbia",
                "logo_url": "https://ui-avatars.com/api/?name=Columbia&background=004A8D&color=fff&size=128&bold=true",
                "campus_photo_url": "",
            },
            {
                "short_name": "duke",
                "logo_url": "https://ui-avatars.com/api/?name=Duke&background=003087&color=fff&size=128&bold=true",
                "campus_photo_url": "",
            },
            {
                "short_name": "northwestern",
                "logo_url": "https://ui-avatars.com/api/?name=Northwestern&background=4E2A84&color=fff&size=128&bold=true",
                "campus_photo_url": "",
            },
            {
                "short_name": "cornell",
                "logo_url": "https://ui-avatars.com/api/?name=Cornell&background=B31B1B&color=fff&size=128&bold=true",
                "campus_photo_url": "",
            },
        ]

        updated_count = 0
        for uni_data in universities_to_update:
            try:
                uni = University.objects.get(short_name=uni_data["short_name"])
                uni.logo_url = uni_data["logo_url"]
                uni.campus_photo_url = uni_data["campus_photo_url"]
                uni.save()
                updated_count += 1
                self.stdout.write(f"✅ Updated {uni.name}\n")
            except University.DoesNotExist:
                self.stdout.write(f"❌ Not found: {uni_data['short_name']}\n")

        self.stdout.write(
            f"\n✅ Successfully updated {updated_count} universities with logos!\n"
        )
