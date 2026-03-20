"""
University Database API Views

Provides endpoints for accessing university data including featured universities
for the home page showcase.
"""

from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import University

# University campus photo mappings (manually curated)
CAMPUS_PHOTOS = {
    "harvard": "https://images.unsplash.com/photo-1559135197-8a45ea74d367?w=800&q=80",
    "mit": "https://images.unsplash.com/photo-1564981797816-1043664bf78d?w=800&q=80",
    "stanford": "https://images.unsplash.com/photo-1581362072978-14998d01fdaa?w=800&q=80",
    "yale": "https://images.unsplash.com/photo-1579612268683-2f1f2f7d6a4c?w=800&q=80",
    "princeton": "https://images.unsplash.com/photo-1541339907198-e08756dedf3f?w=800&q=80",
    "columbia": "https://images.unsplash.com/photo-1568792923760-d70635a89fdc?w=800&q=80",
    "oxford": "https://images.unsplash.com/photo-1580537659466-0a9bfa916a54?w=800&q=80",
    "cambridge": "https://images.unsplash.com/photo-1523240795612-9a054b0db644?w=800&q=80",
    "caltech": "https://images.unsplash.com/photo-1498243691581-b145c3f54a5a?w=800&q=80",
    "uchicago": "https://images.unsplash.com/photo-1574958269340-fa927503f3dd?w=800&q=80",
    "duke": "https://images.unsplash.com/photo-1592280771190-3e2e4d571952?w=800&q=80",
    "northwestern": "https://images.unsplash.com/photo-1562774053-701939374585?w=800&q=80",
    "brown": "https://images.unsplash.com/photo-1574957268500-3b3247ee40a0?w=800&q=80",
    "cornell": "https://images.unsplash.com/photo-1546454526-34c4b39de6f6?w=800&q=80",
    "dartmouth": "https://images.unsplash.com/photo-1517486808906-6ca8b3f04846?w=800&q=80",
    "ucla": "https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?w=800&q=80",
    "berkeley": "https://images.unsplash.com/photo-1564981797816-1043664bf78d?w=800&q=80",
    "usc": "https://images.unsplash.com/photo-1533236897111-3e94666b2edf?w=800&q=80",
    "nyu": "https://images.unsplash.com/photo-1503602642458-23211144584d?w=800&q=80",
    "upenn": "https://images.unsplash.com/photo-1559135197-8a45ea74d367?w=800&q=80",
    "bocconi": "https://images.unsplash.com/photo-1513635269975-59663e0ac1ad?w=800&q=80",
    "london-school-of-economics": "https://images.unsplash.com/photo-1513635269975-59663e0ac1ad?w=800&q=80",
    "imperial": "https://images.unsplash.com/photo-1580537659466-0a9bfa916a54?w=800&q=80",
    "eth-zurich": "https://images.unsplash.com/photo-1516455590571-18256e5bb9ff?w=800&q=80",
    "mcgill": "https://images.unsplash.com/photo-1564981797816-1043664bf78d?w=800&q=80",
    "toronto": "https://images.unsplash.com/photo-1574957268500-3b3247ee40a0?w=800&q=80",
    "ubc": "https://images.unsplash.com/photo-1546454526-34c4b39de6f6?w=800&q=80",
    "amsterdam": "https://images.unsplash.com/photo-1555921015-5532091f6026?w=800&q=80",
    "delft": "https://images.unsplash.com/photo-1523240795612-9a054b0db644?w=800&q=80",
    "heidelberg": "https://images.unsplash.com/photo-1516455590571-18256e5bb9ff?w=800&q=80",
    "munich": "https://images.unsplash.com/photo-1516455590571-18256e5bb9ff?w=800&q=80",
    "sorbonne": "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=800&q=80",
    "tokyo": "https://images.unsplash.com/photo-1542051841857-5f90071e7989?w=800&q=80",
    "seoul-national": "https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?w=800&q=80",
    "national-university-of-singapore": "https://images.unsplash.com/photo-1525625293386-3f8f99389edd?w=800&q=80",
    "melbourne": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800&q=80",
    "sydney": "https://images.unsplash.com/photo-1506973035872-a4ec16b8e8d9?w=800&q=80",
}


class FeaturedUniversitiesView(APIView):
    """
    Returns 4-6 featured universities for display on the home page as examples.

    Shows universities with campus photos if available, otherwise shows universities
    with logos. Mix of different countries and acceptance rates.
    """

    permission_classes = [AllowAny]

    def get(self, request):
        # Get diverse universities from different countries
        usa_unis = University.objects.filter(location_country="United States").order_by(
            "?"
        )[:3]
        international_unis = University.objects.exclude(
            location_country="United States"
        ).order_by("?")[:3]

        universities = list(usa_unis) + list(international_unis)

        # Format response data
        data = []
        for u in universities:
            # Use mapped campus photo or generate a placeholder
            campus_photo = u.campus_photo_url or CAMPUS_PHOTOS.get(
                u.short_name.lower(), ""
            )

            data.append(
                {
                    "id": u.id,
                    "short_name": u.short_name,
                    "name": u.name,
                    "location": f"{u.location_city}{', ' + u.location_state if u.location_state else ''}, {u.location_country}",
                    "campus_photo_url": campus_photo,
                    "logo_url": u.logo_url or "",
                    "acceptance_rate": u.acceptance_rate,
                    "total_cost": u.total_cost_per_year,
                    "location_country": u.location_country,
                    "need_blind": u.need_blind,
                    "international_aid": u.international_aid,
                }
            )

        return Response(data)
