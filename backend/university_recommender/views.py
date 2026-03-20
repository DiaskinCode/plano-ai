"""
API views for university recommendation system.

This module provides endpoints for:
- Generating recommendations
- Managing shortlists
- Comparing universities
- Logging feedback
"""

from django.db import transaction
from django.db.models import Q
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from university_database.models import University
from university_profile.models import ExtracurricularActivity, UniversitySeekerProfile

from .analytics import get_recommendation_analytics
from .eligibility_checker import EligibilityChecker
from .filters import filter_universities
from .llm_scorer import llm_rerank_top_universities
from .models import (
    RecommendationFeedback,
    RecommendationItem,
    RecommendationLog,
    UniversityShortlist,
)
from .scoring import assign_buckets, score_universities, sort_final_recommendations


class GenerateRecommendationsView(APIView):
    """
    Generate university recommendations based on user's profile.

    POST /api/university-recommender/recommend/generate/
    """

    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        """Generate recommendations for the authenticated user"""
        try:
            # Get user's profile
            profile = UniversitySeekerProfile.objects.get(user=request.user)
        except UniversitySeekerProfile.DoesNotExist:
            return Response(
                {
                    "error": "No university profile found. Please create a profile first."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Step 1: Filter universities
            filtered_universities = filter_universities(profile)
            filter_count = filtered_universities.count()

            if filter_count == 0:
                return Response(
                    {
                        "error": "No universities match your criteria. Try adjusting your preferences."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Step 2: Get user's extracurriculars and spike achievement
            # Get user's extracurriculars
            extracurriculars = ExtracurricularActivity.objects.filter(
                profile__user=request.user
            ).values(
                "id",
                "category",
                "title",
                "role",
                "hours_per_week",
                "weeks_per_year",
                "years_participated",
                "impact_level",
                "achievements_impact",
            )

            # Get spike achievement from profile
            spike_data = {
                "spike_area": profile.spike_area if profile else None,
                "spike_achievement": profile.spike_achievement if profile else None,
            }

            # Log profile enhancement
            import logging

            logger = logging.getLogger(__name__)
            logger.info(
                f"Enhanced profile data: extracurriculars={len(extracurriculars)}, spike_area={spike_data['spike_area']}"
            )

            # Step 2: Score universities (three-score system with enhanced data)
            filtered_universities = filter_universities(profile)
            filter_count = filtered_universities.count()

            if filter_count == 0:
                return Response(
                    {
                        "error": "No universities match your criteria. Try adjusting your preferences."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Step 2: Score universities (three-score system)
            scored_universities = score_universities(filtered_universities, profile)

            # Step 3: Assign buckets based on chance score
            scored_universities = assign_buckets(scored_universities)

            # Step 4: LLM reranking (top 40)
            use_llm = request.data.get("use_llm", True)
            if use_llm:
                try:
                    scored_universities = llm_rerank_top_universities(
                        scored_universities, profile, top_n=40
                    )
                except Exception as e:
                    # LLM reranking failed - continue without it
                    import logging

                    logger = logging.getLogger(__name__)
                    logger.error(f"LLM reranking failed: {str(e)}", exc_info=True)
                    # Continue with non-LLM scored universities

            # Step 5: Sort by bucket and score
            final_recommendations = sort_final_recommendations(scored_universities)

            # Step 6: Log the recommendation session
            with transaction.atomic():
                log = RecommendationLog.objects.create(
                    user=request.user,
                    profile_snapshot=self._serialize_profile(profile),
                    total_recommendations=len(final_recommendations),
                    filter_count=filter_count,
                    llm_reranked=use_llm,
                )

                # Create recommendation items for analytics
                items_to_create = []
                for rank, item in enumerate(final_recommendations, start=1):
                    items_to_create.append(
                        RecommendationItem(
                            log=log,
                            university=item["university"],
                            rank=rank,
                            fit_score=item["fit_score"],
                            chance_score=item["chance_score"],
                            finance_score=item["finance_score"],
                            final_rank_score=item["final_rank_score"],
                            bucket=item["bucket"],
                            # LLM data (if available)
                            llm_fit_score=item.get("llm_fit_score"),
                            llm_confidence=item.get("llm_confidence"),
                            llm_reasons=item.get("llm_reasons", []),
                            llm_risks=item.get("llm_risks", []),
                            llm_why_not_fit=item.get("llm_why_not_fit", []),
                            llm_missing_info=item.get("llm_missing_info", []),
                            llm_next_actions=item.get("llm_next_actions", []),
                        )
                    )
                RecommendationItem.objects.bulk_create(items_to_create)

            # NEW: Check eligibility
            eligibility_checker = EligibilityChecker()
            university_objects = [
                item["university"] for item in final_recommendations[:20]
            ]
            eligibility_report = eligibility_checker.check_eligibility(
                profile, university_objects
            )

            # Return results
            response_data = []
            for item in final_recommendations[
                :50
            ]:  # Increased from 20 to 50 to show all buckets
                response_data.append(
                    {
                        "university": {
                            "short_name": item["university"].short_name,
                            "name": item["university"].name,
                            "location": f"{item['university'].location_city}, {item['university'].location_state}",
                            "country": item["university"].location_country,
                            "acceptance_rate": item["university"].acceptance_rate,
                            "total_cost": item["university"].total_cost_per_year,
                            "need_blind": item["university"].need_blind,
                            "international_aid": item["university"].international_aid,
                            "logo_url": item["university"].logo_url,
                            "campus_photo_url": item["university"].campus_photo_url,
                        },
                        "scores": {
                            "fit": item["fit_score"],
                            "chance": item["chance_score"],
                            "finance": item["finance_score"],
                        },
                        "bucket": item["bucket"],
                        "llm_insights": {
                            "confidence": item.get("llm_confidence"),
                            "reasons": item.get("llm_reasons", []),
                            "risks": item.get("llm_risks", []),
                            "next_actions": item.get("llm_next_actions", []),
                        }
                        if item.get("llm_confidence")
                        else None,
                    }
                )

            return Response(
                {
                    "recommendations": response_data,
                    "eligibility_report": eligibility_report,
                    "log_id": log.id,
                    "total_found": len(final_recommendations),
                    "bucket_counts": self._count_buckets(final_recommendations),
                }
            )

        except Exception as e:
            import logging
            import traceback

            logger = logging.getLogger(__name__)
            logger.error(f"Error generating recommendations: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")

            return Response(
                {"error": f"Failed to generate recommendations: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def _serialize_profile(self, profile):
        """Serialize profile for logging"""
        return {
            "gpa": profile.gpa,
            "sat_score": profile.sat_score,
            "act_score": profile.act_score,
            "intended_major_1": profile.intended_major_1,
            "country": profile.country,
            "citizenship": profile.citizenship,
            "max_budget": profile.max_budget,
            "financial_need": profile.financial_need,
        }

    def _count_buckets(self, recommendations):
        """Count universities in each bucket"""
        counts = {"Match": 0, "Safety": 0, "Reach": 0}
        for item in recommendations:
            bucket = item["bucket"]
            if bucket in counts:
                counts[bucket] += 1
        return counts


class UniversityShortlistView(generics.ListCreateAPIView):
    """
    List and manage user's university shortlist.

    GET /api/university-recommender/shortlist/
    POST /api/university-recommender/shortlist/add/
    """

    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        """Get user's shortlisted universities"""
        return UniversityShortlist.objects.filter(
            user=self.request.user
        ).select_related("university")

    def list(self, request, *args, **kwargs):
        """Return shortlisted universities with details"""
        queryset = self.get_queryset()
        data = []
        for item in queryset:
            data.append(
                {
                    "id": item.id,
                    "university": {
                        "short_name": item.university.short_name,
                        "name": item.university.name,
                        "location": f"{item.university.location_city}, {item.university.location_state}",
                        "total_cost": item.university.total_cost_per_year,
                        "acceptance_rate": item.university.acceptance_rate,
                    },
                    "status": item.status,
                    "notes": item.notes,
                    "added_at": item.added_at,
                }
            )
        return Response(data)

    def post(self, request, *args, **kwargs):
        """Add university to shortlist"""
        short_name = request.data.get("short_name")
        notes = request.data.get("notes", "")

        if not short_name:
            return Response(
                {"error": "short_name is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            university = University.objects.get(short_name=short_name)
        except University.DoesNotExist:
            return Response(
                {"error": "University not found"}, status=status.HTTP_404_NOT_FOUND
            )

            # Check if already in shortlist
        if UniversityShortlist.objects.filter(
            user=request.user, university=university
        ).exists():
            return Response(
                {"error": "University already in shortlist"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Add to shortlist
        shortlist_item = UniversityShortlist.objects.create(
            user=request.user, university=university, notes=notes
        )

        return Response(
            {"message": "Added to shortlist", "id": shortlist_item.id},
            status=status.HTTP_201_CREATED,
        )


class RemoveFromShortlistView(generics.DestroyAPIView):
    """
    Remove university from shortlist.

    DELETE /api/university-recommender/shortlist/remove/
    """

    permission_classes = (permissions.IsAuthenticated,)

    def delete(self, request, *args, **kwargs):
        """Remove university from shortlist"""
        short_name = request.data.get("short_name")

        if not short_name:
            return Response(
                {"error": "short_name is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            item = UniversityShortlist.objects.get(
                user=request.user, university__short_name=short_name
            )
            item.delete()
            return Response({"message": "Removed from shortlist"})
        except UniversityShortlist.DoesNotExist:
            return Response(
                {"error": "University not in shortlist"},
                status=status.HTTP_404_NOT_FOUND,
            )


class SubmitFeedbackView(APIView):
    """
    Submit feedback on recommendations.

    POST /api/university-recommender/feedback/
    """

    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        """Record user feedback on a recommendation"""
        item_id = request.data.get("item_id")
        action = request.data.get("action")
        new_bucket = request.data.get("new_bucket")
        notes = request.data.get("notes", "")

        if not item_id or not action:
            return Response(
                {"error": "item_id and action are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            item = RecommendationItem.objects.get(id=item_id, log__user=request.user)
        except RecommendationItem.DoesNotExist:
            return Response(
                {"error": "Recommendation item not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Create feedback
        RecommendationFeedback.objects.create(
            item=item, action=action, new_bucket=new_bucket, notes=notes
        )

        return Response({"message": "Feedback recorded"})


class UniversitySearchView(generics.ListAPIView):
    """
    Search universities database.

    GET /api/university-recommender/universities/search/?q=query
    """

    permission_classes = (permissions.AllowAny,)

    def get_queryset(self):
        """Search universities by name or location"""
        query = self.request.query_params.get("q", "")
        country = self.request.query_params.get("country")

        queryset = University.objects.all()

        if query:
            queryset = queryset.filter(
                Q(name__icontains=query)
                | Q(short_name__icontains=query)
                | Q(location_city__icontains=query)
            )

        if country:
            queryset = queryset.filter(location_country=country)

        return queryset[:20]

    def list(self, request, *args, **kwargs):
        """Return search results"""
        queryset = self.get_queryset()
        data = []
        for u in queryset:
            data.append(
                {
                    "short_name": u.short_name,
                    "name": u.name,
                    "location": f"{u.location_city}, {u.location_state}, {u.location_country}",
                    "acceptance_rate": u.acceptance_rate,
                    "total_cost": u.total_cost_per_year,
                    "need_blind": u.need_blind,
                    "international_aid": u.international_aid,
                    "logo_url": u.logo_url,
                    "campus_photo_url": u.campus_photo_url,
                }
            )
        return Response(data)


class AnalyticsView(APIView):
    """
    Get recommendation analytics (admin only).

    GET /api/university-recommender/analytics/
    """

    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        """Return analytics data"""
        # Check if user is staff/admin
        if not request.user.is_staff:
            return Response(
                {"error": "Admin access required"}, status=status.HTTP_403_FORBIDDEN
            )

        days = int(request.query_params.get("days", 30))
        analytics = get_recommendation_analytics(days)
        return Response(analytics)
