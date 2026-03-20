"""
LLM-based reranking for top universities.

This module uses OpenAI GPT-4 to rerank the top 40 universities
and generate personalized explanations.

MUCH CHEAPER: Only 1 LLM call instead of 40-150 calls.
"""

import json
import os

from django.conf import settings


def llm_rerank_top_universities(scored_universities, profile, top_n=40):
    """
    Uses LLM to rerank top 40 universities and generate explanations.

    Args:
        scored_universities: List of dicts with universities and scores
        profile: UniversitySeekerProfile instance
        top_n: Number of top universities to rerank (default: 40)

    Returns:
        List of dicts with LLM-enhanced scores and explanations
    """
    # Take top N by rules-based score
    top_universities = sorted(
        scored_universities, key=lambda x: x["final_rank_score"], reverse=True
    )[:top_n]

    # FIXED: Serialize extracurriculars properly
    ec_list = []
    for ec in profile.extracurriculars.all():
        ec_list.append(
            f"- {ec.category}: {ec.title} ({ec.role}), "
            f"Impact: {ec.impact_level}, "
            f"Leadership: {ec.leadership_position}, "
            f"Hours: {ec.hours_per_week}/week"
        )

    # Prepare batch prompt
    universities_summary = []
    for i, item in enumerate(top_universities):
        u = item["university"]
        universities_summary.append(f"""
{i + 1}. {u.short_name} ({u.name})
   - Strengths: {u.strength_programs}
   - Location: {u.location_city}, {u.location_state}
   - Setting: {u.campus_type}, {u.setting} ({u.undergraduate_enrollment} students)
   - Research: {u.research_intensity}, Co-op: {u.co_op_programs}
   - Aid: Need-blind={u.need_blind}, Merit={u.merit_aid_offered}, Intl Aid={u.international_aid}
   - Employment: {u.employed_within_6_months}% employed
   """)

    prompt = f"""
You are a college admissions expert. Rerank these universities based on student fit.

STUDENT PROFILE:
- Academic Interests: {profile.intended_major_1}, {profile.intended_major_2}
- Why: {profile.academic_interests}
- Spike: {profile.spike_area} - {profile.spike_achievement}
- Campus Preferences: {profile.preferred_size} size, {profile.preferred_location} location
- Budget: {profile.financial_need}, max ${profile.max_budget}/year
- Citizenship: {profile.citizenship}
- Test Flexible: {profile.test_optional_flexible}

EXTRACURRICULARS:
{chr(10).join(ec_list) if ec_list else "None provided"}

UNIVERSITIES TO RERANK:
{chr(10).join(universities_summary)}

Return ONLY a JSON object:
{{
    "rankings": [
        {{
            "short_name": "mit",
            "fit_score": 92,
            "confidence": "high",
            "reasons": ["<reason 1>", "<reason 2>"],
            "risks": ["<risk 1>"],
            "why_not_fit": ["<concern 1>"],
            "missing_info": ["<gap 1>"],
            "next_actions": ["<action 1>"]
        }},
        ...
    ]
}}

Prioritize:
1. Academic program strength and alignment
2. Campus culture fit
3. Financial feasibility (especially if international student needing aid)
4. Opportunity alignment (research, internships, special programs)
"""

    try:
        # Import OpenAI here to avoid issues if not configured
        from openai import OpenAI

        client = OpenAI(
            api_key=getattr(settings, "OPENAI_API_KEY", os.getenv("OPENAI_API_KEY"))
        )

        # Use a model that supports json_object mode
        response = client.chat.completions.create(
            model="gpt-4o",  # Updated to gpt-4o which supports json_object
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            response_format={"type": "json_object"},
        )

        result = json.loads(response.choices[0].message.content)

        # Create lookup map
        university_map = {
            item["university"].short_name: item for item in top_universities
        }

        # Apply LLM reranking
        reranked = []
        for assessment in result.get("rankings", []):
            short_name = assessment["short_name"]
            item = university_map.get(short_name)

            if not item:
                continue  # Skip if university not found

            item["llm_fit_score"] = assessment.get("fit_score", item["fit_score"])
            item["llm_confidence"] = assessment.get("confidence", "medium")
            item["llm_reasons"] = assessment.get("reasons", [])
            item["llm_risks"] = assessment.get("risks", [])
            item["llm_why_not_fit"] = assessment.get("why_not_fit", [])
            item["llm_missing_info"] = assessment.get("missing_info", [])
            item["llm_next_actions"] = assessment.get("next_actions", [])

            # Update final rank score with LLM input
            item["final_rank_score"] = (
                item["fit_score"] * 0.4
                + item["llm_fit_score"] * 0.3
                + item["finance_score"] * 0.3
            )

            reranked.append(item)

        # Add universities that weren't reranked by LLM
        reranked_short_names = {r["university"].short_name for r in reranked}
        for item in top_universities:
            if item["university"].short_name not in reranked_short_names:
                reranked.append(item)

        return reranked

    except Exception as e:
        # If LLM fails, return original rankings
        print(f"LLM reranking failed: {e}")
        return top_universities
