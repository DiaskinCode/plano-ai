from django.core.management.base import BaseCommand

from university_database.models import University


class Command(BaseCommand):
    help = "Populate university logos and campus photos from Wikipedia"

    def handle(self, *args, **options):
        # Top universities with Wikipedia image URLs
        universities_to_update = [
            {
                "short_name": "harvard",
                "logo_url": "https://upload.wikimedia.org/wikipedia/en/thumb/a/a8/Harvard_Wrench_shield.svg/240px-Harvard_Wrench_shield.svg.png",
                "campus_photo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/72/Harvard_Yard_winter_2018.jpg/1280px-Harvard_Yard_winter_2018.jpg",
            },
            {
                "short_name": "mit",
                "logo_url": "https://upload.wikimedia.org/wikipedia/en/thumb/5/51/MIT_logo.svg/240px-MIT_logo.svg.png",
                "campus_photo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f3/MIT_Dome_Winter_Sunset.jpg/1280px-MIT_Dome_Winter_Sunset.jpg",
            },
            {
                "short_name": "stanford",
                "logo_url": "https://upload.wikimedia.org/wikipedia/en/thumb/8/83/Stanford_cardinal_logo.svg/240px-Stanford_cardinal_logo.svg.png",
                "campus_photo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f2/Stanford_campus_aerial_photo.jpg/1280px-Stanford_campus_aerial_photo.jpg",
            },
            {
                "short_name": "yale",
                "logo_url": "https://upload.wikimedia.org/wikipedia/en/thumb/c/c1/Yale_Shield.svg/240px-Yale_Shield.svg.png",
                "campus_photo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/39/Yale_University_Harkness_Tower_2019.jpg/1280px-Yale_University_Harkness_Tower_2019.jpg",
            },
            {
                "short_name": "princeton",
                "logo_url": "https://upload.wikimedia.org/wikipedia/en/thumb/2/26/Princeton_seal.svg/240px-Princeton_seal.svg.png",
                "campus_photo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/33/Princeton_Chapel_night.jpg/1280px-Princeton_Chapel_night.jpg",
            },
            {
                "short_name": "columbia",
                "logo_url": "https://upload.wikimedia.org/wikipedia/en/thumb/1/17/Columbia_shield.svg/240px-Columbia_shield.svg.png",
                "campus_photo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/63/Low_library_columbia_university.jpg/1280px-Low_library_columbia_university.jpg",
            },
            {
                "short_name": "uchicago",
                "logo_url": "https://upload.wikimedia.org/wikipedia/en/thumb/e/e3/UChicago_shield.svg/240px-UChicago_shield.svg.png",
                "campus_photo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/15/University_of_Chicago_campus_aerial.jpg/1280px-University_of_Chicago_campus_aerial.jpg",
            },
            {
                "short_name": "duke",
                "logo_url": "https://upload.wikimedia.org/wikipedia/en/thumb/4/46/Duke_Blue_Devil.svg/240px-Duke_Blue_Devil.svg.png",
                "campus_photo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e7/Duke_University_Chapel_2009.jpg/1280px-Duke_University_Chapel_2009.jpg",
            },
            {
                "short_name": "northwestern",
                "logo_url": "https://upload.wikimedia.org/wikipedia/en/thumb/3/3d/Northwestern_seal.svg/240px-Northwestern_seal.svg.png",
                "campus_photo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7f/Northwestern_University_Library.jpg/1280px-Northwestern_University_Library.jpg",
            },
            {
                "short_name": "cornell",
                "logo_url": "https://upload.wikimedia.org/wikipedia/en/thumb/2/2e/Cornell_seal.svg/240px-Cornell_seal.svg.png",
                "campus_photo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/26/Cornell_University_McGraw_Tower_spring.jpg/1280px-Cornell_University_McGraw_Tower_spring.jpg",
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
            f"\n✅ Successfully updated {updated_count} universities with images!\n"
        )
