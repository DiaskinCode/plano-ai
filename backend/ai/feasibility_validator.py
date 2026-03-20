"""
Feasibility Validator Service
Validates whether user goals are realistic based on their profile and prevents false hope.
"""

from typing import Dict, List, Optional
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class FeasibilityValidator:
    """
    Validates goal feasibility and provides honest feedback about achievability.

    Key principles:
    1. Build trust through honesty - warn users about unrealistic goals
    2. Provide alternatives when goals are not feasible
    3. Use real data (university requirements, market conditions, etc.)
    """

    # University tiers based on typical admissions requirements
    UNIVERSITY_TIERS = {
        'top_tier': {
            'names': ['Harvard', 'MIT', 'Stanford', 'Oxford', 'Cambridge', 'ETH Zurich'],
            'min_gpa': 3.7,
            'min_ielts': 7.5,
            'min_toefl': 110,
            'acceptance_rate': 0.05,  # ~5%
        },
        'excellent': {
            'names': ['Imperial', 'UCL', 'Edinburgh', 'TU Munich', 'EPFL'],
            'min_gpa': 3.5,
            'min_ielts': 7.0,
            'min_toefl': 100,
            'acceptance_rate': 0.15,  # ~15%
        },
        'strong': {
            'names': ['Warwick', 'Manchester', 'KTH', 'TU Delft', 'McGill'],
            'min_gpa': 3.2,
            'min_ielts': 6.5,
            'min_toefl': 90,
            'acceptance_rate': 0.30,  # ~30%
        },
        'good': {
            'names': ['Birmingham', 'Leeds', 'Glasgow', 'Utrecht', 'Lund'],
            'min_gpa': 3.0,
            'min_ielts': 6.0,
            'min_toefl': 80,
            'acceptance_rate': 0.50,  # ~50%
        }
    }

    # Typical tuition costs by country (GBP per year)
    TUITION_COSTS = {
        'UK': {'min': 15000, 'max': 35000, 'typical': 22000},
        'US': {'min': 25000, 'max': 60000, 'typical': 40000},
        'Germany': {'min': 0, 'max': 3000, 'typical': 500},  # Most public unis are free
        'Netherlands': {'min': 8000, 'max': 18000, 'typical': 12000},
        'Sweden': {'min': 0, 'max': 15000, 'typical': 10000},
        'Canada': {'min': 15000, 'max': 35000, 'typical': 25000},
    }

    # Career transition difficulty matrix
    CAREER_TRANSITIONS = {
        'easy': ['same_role_different_company', 'internal_promotion'],
        'moderate': ['adjacent_role', 'same_industry_different_function'],
        'hard': ['different_industry', 'different_role', 'senior_leap'],
        'very_hard': ['career_pivot', 'industry_and_role_change'],
    }

    def validate_study_goal(self, goalspec: 'GoalSpec', profile: 'UserProfile') -> Dict:
        """
        Validate study abroad/university application goal.

        Returns:
            {
                "feasible": bool,
                "confidence": "high" | "medium" | "low",
                "warnings": [str],
                "recommendations": [str],
                "target_universities": [{name, tier, acceptance_probability}]
            }
        """
        warnings = []
        recommendations = []
        target_universities = []

        specs = goalspec.specifications or {}
        country = specs.get('country', '')
        target_university = specs.get('university', '')
        budget = self._parse_budget(goalspec.budget)

        # Get user's academic profile
        gpa = float(profile.gpa) if profile.gpa else None
        ielts = profile.test_scores.get('IELTS') if profile.test_scores else None
        toefl = profile.test_scores.get('TOEFL') if profile.test_scores else None

        # Validation 1: Budget vs Country
        if country and budget:
            cost_range = self.TUITION_COSTS.get(country)
            if cost_range:
                typical_cost = cost_range['typical']
                if budget < typical_cost:
                    warnings.append(
                        f"Your budget (£{budget:,}) is below typical tuition for {country} (£{typical_cost:,}). "
                        f"Consider countries like Germany (free public universities) or look for scholarships."
                    )
                    recommendations.append(f"Increase budget to £{typical_cost:,}+ or target scholarship programs")
                    recommendations.append("Consider Germany, Norway, or Finland for lower/free tuition")

        # Validation 2: Test Scores vs University Tier
        if target_university and (ielts or toefl or gpa):
            tier = self._find_university_tier(target_university)
            if tier:
                tier_requirements = self.UNIVERSITY_TIERS[tier]

                # Check GPA
                if gpa and gpa < tier_requirements['min_gpa']:
                    warnings.append(
                        f"{target_university} typically requires GPA {tier_requirements['min_gpa']}+. "
                        f"Your GPA ({gpa}) may be below the competitive range."
                    )
                    recommendations.append("Focus on universities with GPA requirements closer to your profile")

                # Check IELTS
                if ielts and ielts < tier_requirements['min_ielts']:
                    warnings.append(
                        f"{target_university} typically requires IELTS {tier_requirements['min_ielts']}+. "
                        f"Your score ({ielts}) needs improvement."
                    )
                    recommendations.append(f"Retake IELTS (target: {tier_requirements['min_ielts']}+)")

                # Check TOEFL
                if toefl and toefl < tier_requirements['min_toefl']:
                    warnings.append(
                        f"{target_university} typically requires TOEFL {tier_requirements['min_toefl']}+. "
                        f"Your score ({toefl}) needs improvement."
                    )
                    recommendations.append(f"Retake TOEFL (target: {tier_requirements['min_toefl']}+)")

        # Validation 3: Timeline Feasibility
        timeline_months = self._parse_timeline(goalspec.timeline)
        if timeline_months and timeline_months < 6:
            warnings.append(
                f"Your timeline ({timeline_months} months) is very tight for international applications. "
                f"Most programs require 6-12 months of preparation."
            )
            recommendations.append("Extend timeline to 8-12 months for better preparation")

        # Generate Target Universities based on profile
        if gpa or ielts:
            target_universities = self._suggest_target_universities(gpa, ielts, country)

        # Overall Feasibility Assessment
        feasible = len(warnings) == 0
        confidence = "high" if feasible else ("medium" if len(warnings) <= 2 else "low")

        if not feasible:
            recommendations.insert(0, "Your goal is achievable with adjustments - see recommendations below")

        return {
            "feasible": feasible,
            "confidence": confidence,
            "warnings": warnings,
            "recommendations": recommendations,
            "target_universities": target_universities,
            "estimated_success_rate": self._calculate_success_rate(gpa, ielts, target_university)
        }

    def validate_career_goal(self, goalspec: 'GoalSpec', profile: 'UserProfile') -> Dict:
        """
        Validate career transition/job search goal.

        Returns:
            {
                "feasible": bool,
                "confidence": "high" | "medium" | "low",
                "warnings": [str],
                "recommendations": [str],
                "transition_difficulty": "easy" | "moderate" | "hard" | "very_hard",
                "estimated_timeline_months": int
            }
        """
        warnings = []
        recommendations = []

        specs = goalspec.specifications or {}
        target_role = specs.get('target_role', '')
        target_company_tier = specs.get('company_tier', 'any')  # startup, midsize, faang, any

        # Get user's career profile
        years_exp = profile.years_of_experience or 0
        current_role = profile.current_role or ''
        companies = profile.companies_worked or []
        skills = profile.skills or []
        network_size = profile.referral_network_size or 0

        # Validation 1: Experience Level
        if 'senior' in target_role.lower() and years_exp < 5:
            warnings.append(
                f"Senior roles typically require 5+ years experience. "
                f"You have {years_exp} years - consider mid-level positions first."
            )
            recommendations.append("Target mid-level roles, then move to senior after 1-2 years")

        if 'lead' in target_role.lower() or 'manager' in target_role.lower() and years_exp < 3:
            warnings.append(
                f"Leadership roles typically require 3+ years experience. "
                f"You have {years_exp} years - consider building more experience first."
            )
            recommendations.append("Focus on IC (Individual Contributor) roles first")

        # Validation 2: Network Size for Referrals
        if network_size < 5:
            warnings.append(
                "Your referral network is small (<5 people). Referrals increase your chances by 4-5x."
            )
            recommendations.append("Spend 2-3 weeks building your network before applying")
            recommendations.append("Reach out to alumni, former colleagues, and LinkedIn connections")

        # Validation 3: FAANG/Top Tier Difficulty
        if target_company_tier == 'faang':
            if not any(company in ['Google', 'Facebook', 'Amazon', 'Apple', 'Microsoft', 'Netflix'] for company in companies):
                warnings.append(
                    "FAANG companies are highly competitive. Without prior big-tech experience, "
                    "acceptance rate is ~1-3%. Consider mid-tier companies first."
                )
                recommendations.append("Apply to 10+ companies simultaneously (not just FAANG)")
                recommendations.append("Include mid-tier companies (Stripe, Airbnb, Uber) with higher acceptance rates")

        # Validation 4: Timeline Realism
        timeline_months = self._parse_timeline(goalspec.timeline)
        job_search_difficulty = self._assess_career_transition_difficulty(current_role, target_role)

        expected_timeline = {
            'easy': 2,
            'moderate': 4,
            'hard': 6,
            'very_hard': 9
        }.get(job_search_difficulty, 4)

        if timeline_months and timeline_months < expected_timeline:
            warnings.append(
                f"Your timeline ({timeline_months} months) is tight for a {job_search_difficulty} transition. "
                f"Typical timeline: {expected_timeline} months."
            )
            recommendations.append(f"Extend timeline to {expected_timeline}+ months for realistic job search")

        # Overall Feasibility
        feasible = len(warnings) == 0
        confidence = "high" if feasible else ("medium" if len(warnings) <= 2 else "low")

        return {
            "feasible": feasible,
            "confidence": confidence,
            "warnings": warnings,
            "recommendations": recommendations,
            "transition_difficulty": job_search_difficulty,
            "estimated_timeline_months": expected_timeline,
            "suggested_companies": self._suggest_target_companies(profile, target_role)
        }

    def validate_fitness_goal(self, goalspec: 'GoalSpec', profile: 'UserProfile') -> Dict:
        """
        Validate fitness/sports goal.

        Returns:
            {
                "feasible": bool,
                "confidence": "high" | "medium" | "low",
                "warnings": [str],
                "recommendations": [str],
                "injury_considerations": [str]
            }
        """
        warnings = []
        recommendations = []
        injury_considerations = []

        specs = goalspec.specifications or {}
        goal_type = specs.get('sport_type', '')  # e.g., "bodybuilding", "marathon", "weight_loss"

        fitness_level = profile.fitness_level
        injuries = profile.injuries_limitations or []
        gym_access = profile.gym_access

        # Validation 1: Fitness Level vs Goal
        if fitness_level == 'beginner' and 'advanced' in goal_type.lower():
            warnings.append(
                "You're targeting an advanced goal as a beginner. This may lead to injury or burnout."
            )
            recommendations.append("Start with intermediate goals, progress to advanced after 3-6 months")

        # Validation 2: Gym Access
        if not gym_access and any(keyword in goal_type.lower() for keyword in ['bodybuilding', 'powerlifting', 'strength']):
            warnings.append(
                f"{goal_type} typically requires gym equipment. Consider home workout alternatives."
            )
            recommendations.append("Focus on bodyweight exercises or invest in basic home equipment (dumbbells, resistance bands)")

        # Validation 3: Injury Considerations
        if injuries:
            for injury in injuries:
                if 'knee' in injury.lower() and 'running' in goal_type.lower():
                    injury_considerations.append("Knee injury: Consider low-impact cardio (swimming, cycling) instead of running")
                if 'back' in injury.lower() and 'deadlift' in goal_type.lower():
                    injury_considerations.append("Lower back pain: Avoid heavy deadlifts, focus on core strengthening first")
                if 'shoulder' in injury.lower() and 'bench press' in goal_type.lower():
                    injury_considerations.append("Shoulder injury: Avoid heavy bench press, work with physical therapist")

        if injury_considerations:
            warnings.append("You have injuries that may affect your goal. See considerations below.")
            recommendations.append("Consult with a physical therapist before starting intense training")

        # Overall Feasibility
        feasible = len(warnings) == 0
        confidence = "high" if feasible else ("medium" if len(warnings) <= 2 else "low")

        return {
            "feasible": feasible,
            "confidence": confidence,
            "warnings": warnings,
            "recommendations": recommendations,
            "injury_considerations": injury_considerations
        }

    # Helper Methods

    def _parse_budget(self, budget_str: Optional[str]) -> Optional[int]:
        """Parse budget string like '£20,000-30,000' to midpoint value."""
        if not budget_str:
            return None
        try:
            # Remove currency symbols and spaces
            clean = budget_str.replace('£', '').replace('$', '').replace(',', '').replace(' ', '')
            # Handle ranges
            if '-' in clean:
                low, high = clean.split('-')
                return (int(low) + int(high)) // 2
            return int(clean)
        except:
            return None

    def _parse_timeline(self, timeline_str: Optional[str]) -> Optional[int]:
        """Parse timeline string like '6-9 months' to midpoint months."""
        if not timeline_str:
            return None
        try:
            # Extract numbers
            if 'month' in timeline_str.lower():
                numbers = [int(s) for s in timeline_str.split() if s.isdigit()]
                if numbers:
                    return sum(numbers) // len(numbers)
            elif 'year' in timeline_str.lower():
                numbers = [int(s) for s in timeline_str.split() if s.isdigit()]
                if numbers:
                    return (sum(numbers) // len(numbers)) * 12
            return None
        except:
            return None

    def _find_university_tier(self, university_name: str) -> Optional[str]:
        """Find which tier a university belongs to."""
        for tier, data in self.UNIVERSITY_TIERS.items():
            if any(uni.lower() in university_name.lower() for uni in data['names']):
                return tier
        return None

    def _suggest_target_universities(self, gpa: Optional[float], ielts: Optional[float], country: Optional[str]) -> List[Dict]:
        """Suggest realistic target universities based on profile."""
        suggestions = []

        for tier, data in self.UNIVERSITY_TIERS.items():
            # Check if user meets minimum requirements for this tier
            meets_gpa = not gpa or gpa >= data['min_gpa']
            meets_ielts = not ielts or ielts >= data['min_ielts']

            if meets_gpa and meets_ielts:
                for uni in data['names'][:2]:  # Top 2 from each tier
                    suggestions.append({
                        "name": uni,
                        "tier": tier,
                        "acceptance_probability": data['acceptance_rate'],
                        "reasoning": f"Your profile matches {tier} tier requirements"
                    })

        return suggestions[:5]  # Return top 5

    def _calculate_success_rate(self, gpa: Optional[float], ielts: Optional[float], target_university: str) -> float:
        """Estimate probability of acceptance based on profile."""
        tier = self._find_university_tier(target_university)
        if not tier:
            return 0.5  # Unknown university, assume 50%

        base_rate = self.UNIVERSITY_TIERS[tier]['acceptance_rate']
        min_gpa = self.UNIVERSITY_TIERS[tier]['min_gpa']
        min_ielts = self.UNIVERSITY_TIERS[tier]['min_ielts']

        # Adjust based on how far above minimums
        gpa_multiplier = 1.0
        if gpa:
            if gpa >= min_gpa + 0.3:
                gpa_multiplier = 1.5
            elif gpa >= min_gpa:
                gpa_multiplier = 1.2
            else:
                gpa_multiplier = 0.7

        ielts_multiplier = 1.0
        if ielts:
            if ielts >= min_ielts + 1.0:
                ielts_multiplier = 1.3
            elif ielts >= min_ielts:
                ielts_multiplier = 1.1
            else:
                ielts_multiplier = 0.8

        estimated_rate = min(base_rate * gpa_multiplier * ielts_multiplier, 0.95)
        return round(estimated_rate, 2)

    def _assess_career_transition_difficulty(self, current_role: str, target_role: str) -> str:
        """Assess difficulty of career transition."""
        if not current_role or not target_role:
            return 'moderate'

        # Same role = easy
        if current_role.lower() in target_role.lower() or target_role.lower() in current_role.lower():
            return 'easy'

        # Completely different = very hard
        role_keywords_current = set(current_role.lower().split())
        role_keywords_target = set(target_role.lower().split())
        overlap = role_keywords_current & role_keywords_target

        if len(overlap) == 0:
            return 'very_hard'
        elif len(overlap) >= 2:
            return 'easy'
        else:
            return 'moderate'

    def _suggest_target_companies(self, profile: 'UserProfile', target_role: str) -> List[str]:
        """Suggest realistic target companies based on profile."""
        companies_worked = profile.companies_worked or []
        years_exp = profile.years_of_experience or 0

        # If user has FAANG experience, can target similar tier
        faang = ['Google', 'Facebook', 'Amazon', 'Apple', 'Microsoft', 'Netflix']
        has_faang = any(company in faang for company in companies_worked)

        if has_faang:
            return ['Meta', 'Google', 'Amazon', 'Microsoft', 'Apple', 'Stripe', 'Airbnb']
        elif years_exp >= 5:
            return ['Stripe', 'Airbnb', 'Uber', 'Snap', 'Twitter', 'Pinterest', 'Dropbox']
        else:
            return ['Startup (Series B+)', 'Mid-size tech (500-2000 employees)', 'Scale-ups', 'Regional tech leaders']


# Global instance
feasibility_validator = FeasibilityValidator()
