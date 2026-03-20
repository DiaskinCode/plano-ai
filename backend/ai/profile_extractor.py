"""
Profile Data Extractor

Extracts structured context from UserProfile for template variable filling.

KEY INSIGHT: Don't add new database fields - extract better from existing data.
- prior_education JSONField contains university names
- network JSONField contains warm introductions
- skills JSONField contains top skills

This extractor transforms unstructured JSON into structured template variables.
"""

from typing import Dict, List, Optional, Any
import json
import re


class ProfileExtractor:
    """
    Extract structured template variables from UserProfile.

    Transforms existing JSONFields into clean, usable template context.
    """

    def extract_context(self, user_profile: Any, goal_spec: Any) -> Dict[str, Any]:
        """
        Extract all relevant context for template rendering.

        Args:
            user_profile: UserProfile object
            goal_spec: GoalSpec object

        Returns:
            Dictionary of template variables
        """
        context = {}

        # Basic profile data
        context.update(self._extract_basic_info(user_profile))

        # === LAYER 2: PERSONALIZATION FLAGS ===
        specs = getattr(goal_spec, 'specifications', {}) or {}

        # Startup/founder background
        context['has_startup_background'] = specs.get('has_startup_background', False)
        if context['has_startup_background']:
            context['startup_name'] = specs.get('startup_name', 'your startup')
            context['startup_description'] = specs.get('startup_description', 'your startup')
            context['startup_users'] = specs.get('startup_users', '0')
            context['startup_funding'] = specs.get('startup_funding', '$0')
            context['startup_role'] = specs.get('startup_role', 'Founder')

        # Work experience and achievements
        years_experience = getattr(user_profile, 'years_of_experience', 0) or 0
        notable_achievements = getattr(user_profile, 'notable_achievements', []) or []
        context['has_work_experience'] = years_experience > 0
        context['has_notable_achievements'] = bool(notable_achievements)

        # GPA flags for compensation strategies
        gpa = getattr(user_profile, 'gpa', None) or specs.get('gpa', None)
        context['gpa_raw'] = gpa
        context['gpa_below_average'] = (gpa is not None and gpa < 3.5)
        context['gpa_needs_compensation'] = (
            gpa is not None and
            gpa < 3.5 and
            (context['has_startup_background'] or context['has_notable_achievements'])
        )

        # Test prep flags (smart adaptation)
        context['test_prep_needed'] = {}
        if goal_spec.category == 'study':
            # Extract test scores
            test_scores = getattr(user_profile, 'test_scores', {}) or {}
            if isinstance(test_scores, str):
                # Parse string format if needed
                import re
                result = {}
                test_str = test_scores.lower()
                patterns = {
                    'ielts': r'ielts[:\s]+(\d+\.?\d*)',
                    'toefl': r'toefl[:\s]+(\d+)',
                    'gre': r'gre[:\s]+(\d+)',
                }
                for test_name, pattern in patterns.items():
                    match = re.search(pattern, test_str)
                    if match:
                        try:
                            result[test_name] = float(match.group(1))
                        except ValueError:
                            continue
                test_scores = result if result else {}

            # Get target scores from specs
            target_ielts = specs.get('target_ielts', specs.get('target_score', 7.0))
            target_toefl = specs.get('target_toefl', 100)
            target_gre = specs.get('target_gre', 320)

            # Only prep needed if current < target
            current_ielts = test_scores.get('ielts', 0)
            current_toefl = test_scores.get('toefl', 0)
            current_gre = test_scores.get('gre', 0)

            # Convert to float for comparison (handle string inputs)
            try:
                current_ielts_float = float(current_ielts) if current_ielts else 0
            except (ValueError, TypeError):
                current_ielts_float = 0

            try:
                current_toefl_float = float(current_toefl) if current_toefl else 0
            except (ValueError, TypeError):
                current_toefl_float = 0

            try:
                current_gre_float = float(current_gre) if current_gre else 0
            except (ValueError, TypeError):
                current_gre_float = 0

            context['test_prep_needed']['ielts'] = current_ielts_float > 0 and current_ielts_float < float(target_ielts)
            context['test_prep_needed']['toefl'] = current_toefl_float > 0 and current_toefl_float < target_toefl
            context['test_prep_needed']['gre'] = current_gre_float > 0 and current_gre_float < target_gre

        # Study-specific context
        if goal_spec.category == 'study':
            context.update(self._extract_study_context(user_profile, goal_spec))

        # Career-specific context
        elif goal_spec.category == 'career':
            context.update(self._extract_career_context(user_profile, goal_spec))

        # Fitness-specific context
        elif goal_spec.category == 'fitness':
            context.update(self._extract_fitness_context(user_profile, goal_spec))

        # Goal specifications
        context.update(self._extract_goal_specs(goal_spec))

        # DEBUG: Log extracted context to help diagnose template rendering issues
        print(f"[ProfileExtractor] Extracted {len(context)} context variables for goal: {goal_spec.title}")
        print(f"[ProfileExtractor] Available keys: {', '.join(sorted(context.keys()))}")

        # Log key values for critical variables
        critical_keys = ['target_role', 'field', 'years_experience', 'target_regions', 'max_tuition', 'target_universities']
        for key in critical_keys:
            if key in context:
                value = str(context[key])[:80]  # Truncate long values
                print(f"[ProfileExtractor]   {key} = {value}")

        return context

    def _extract_basic_info(self, profile: Any) -> Dict[str, Any]:
        """Extract universal profile info"""
        return {
            'user_name': getattr(profile, 'user_name', 'there'),
            'country': getattr(profile, 'country_of_residence', 'your country'),
            'energy_peak': getattr(profile, 'energy_peak', 'morning'),
            'daily_minutes': getattr(profile, 'daily_available_minutes', 120),
            'weaknesses': self._extract_weaknesses(profile),
        }

    def _extract_weaknesses(self, profile: Any) -> str:
        """Extract first weakness for targeting"""
        weaknesses = getattr(profile, 'weaknesses', None)

        if not weaknesses:
            return 'general improvement'

        if isinstance(weaknesses, list) and len(weaknesses) > 0:
            return weaknesses[0]

        if isinstance(weaknesses, str):
            return weaknesses

        return 'general improvement'

    def _extract_study_context(self, profile: Any, goal_spec: Any) -> Dict[str, Any]:
        """Extract study-specific context"""
        context = {}

        # Budget (NEW: prioritize conversational onboarding)
        specs = getattr(goal_spec, 'specifications', {}) or {}
        constraints = getattr(goal_spec, 'constraints', {}) or {}
        profile_budget = getattr(profile, 'budget', None)
        budget_str = profile_budget or specs.get('budget') or constraints.get('budget') or ''
        context['budget'] = budget_str
        context['max_tuition'] = self._parse_max_tuition(budget_str)

        # GPA
        gpa = getattr(profile, 'gpa', None)
        context['gpa'] = f"{gpa}/4.0" if gpa else "your GPA"
        context['gpa_value'] = gpa or 3.5  # Default for comparisons

        # Test scores (IELTS, TOEFL, GRE)
        test_scores = getattr(profile, 'test_scores', {}) or {}

        # Handle case where test_scores might be a string (from older data)
        if isinstance(test_scores, str):
            # Try to parse it
            import re
            result = {}
            test_str = test_scores.lower()
            patterns = {
                'ielts': r'ielts[:\s]+(\d+\.?\d*)',
                'toefl': r'toefl[:\s]+(\d+)',
                'gre': r'gre[:\s]+(\d+)',
            }
            for test_name, pattern in patterns.items():
                match = re.search(pattern, test_str)
                if match:
                    try:
                        result[test_name] = float(match.group(1))
                    except ValueError:
                        continue
            test_scores = result if result else {}

        context['ielts_score'] = test_scores.get('ielts', 6.0)
        context['toefl_score'] = test_scores.get('toefl', 80)
        context['gre_score'] = test_scores.get('gre', 310)
        context['test_scores'] = test_scores

        # Field of study (NEW: prioritize conversational onboarding)
        # Priority order: profile.field_of_study (conversational) > specs > infer from title
        field = getattr(profile, 'field_of_study', '') or ''

        if not field or field == 'your field':
            # Try specifications
            specs = getattr(goal_spec, 'specifications', {}) or {}
            field = specs.get('field', specs.get('field_of_study', ''))

            # If still empty, extract from goalspec title/description
            if not field:
                title = getattr(goal_spec, 'title', '').lower()
                description = getattr(goal_spec, 'description', '').lower()
                combined = f"{title} {description}"

                # Common field keywords
                if 'computer science' in combined or 'cs ' in combined or ' cs' in combined:
                    field = 'Computer Science'
                elif 'software engineer' in combined or 'software dev' in combined:
                    field = 'Software Engineering'
                elif 'data science' in combined or 'data scien' in combined:
                    field = 'Data Science'
                elif 'business' in combined or 'mba' in combined:
                    field = 'Business'
                elif 'engineering' in combined:
                    field = 'Engineering'
                elif 'medicine' in combined or 'medical' in combined:
                    field = 'Medicine'
                elif 'law' in combined:
                    field = 'Law'
                elif 'economics' in combined:
                    field = 'Economics'
                elif 'mathematics' in combined or 'math' in combined:
                    field = 'Mathematics'
                elif 'physics' in combined:
                    field = 'Physics'
                else:
                    field = 'your field of study'

        context['field'] = field

        # Degree level (NEW: prioritize conversational onboarding)
        profile_degree_level = getattr(profile, 'degree_level', None)
        context['degree_level'] = profile_degree_level or self._infer_degree_level(goal_spec)

        # Current education (NEW: from conversational onboarding)
        current_education = getattr(profile, 'current_education', None)
        if current_education:
            context['current_education'] = current_education
            # Try to extract university name from current_education
            context['current_university'] = current_education
        else:
            context['current_education'] = None
            context['current_university'] = self._extract_current_university(profile, goal_spec)

        # Academic projects (extract from prior_education or profile)
        context['top_projects'] = self._extract_academic_projects(profile)

        # Target universities (NEW: prioritize conversational onboarding)
        profile_target_schools = getattr(profile, 'target_schools', []) or []
        if profile_target_schools:
            context['target_universities'] = profile_target_schools
            context['school_1'] = profile_target_schools[0] if len(profile_target_schools) > 0 else 'your target university'
            context['school_2'] = profile_target_schools[1] if len(profile_target_schools) > 1 else None
            context['school_3'] = profile_target_schools[2] if len(profile_target_schools) > 2 else None
        else:
            context['target_universities'] = self._extract_target_universities(goal_spec)
            context['school_1'] = context['target_universities'][0] if isinstance(context['target_universities'], list) and len(context['target_universities']) > 0 else 'your target university'
            context['school_2'] = None
            context['school_3'] = None

        # Professor contacts (from network)
        context['professor_contacts'] = self._extract_professor_contacts(profile)

        # Research interests (NEW: from conversational onboarding)
        profile_research_interests = getattr(profile, 'research_interests', None)
        if profile_research_interests:
            context['research_interest'] = profile_research_interests
            context['research_interests'] = profile_research_interests
        else:
            context['research_interest'] = self._extract_research_interest(profile, goal_spec)
            context['research_interests'] = context['research_interest']

        # Target regions/countries (NEW: prioritize conversational onboarding)
        specs = getattr(goal_spec, 'specifications', {}) or {}

        # Priority: profile.target_country > specs.country
        profile_target_country = getattr(profile, 'target_country', None)
        country = profile_target_country or specs.get('country', '')

        if country in ['US', 'USA']:
            context['target_regions'] = 'United States'
            context['target_countries'] = 'US'
        elif country == 'UK':
            context['target_regions'] = 'United Kingdom'
            context['target_countries'] = 'UK'
        elif country == 'CANADA':
            context['target_regions'] = 'Canada'
            context['target_countries'] = 'Canada'
        elif country in ['GERMANY', 'FRANCE', 'SPAIN', 'ITALY', 'NETHERLANDS']:
            context['target_regions'] = 'Europe'
            context['target_countries'] = country
        elif country == 'AUSTRALIA':
            context['target_regions'] = 'Australia'
            context['target_countries'] = 'Australia'
        else:
            # Fallback to specification values or defaults
            context['target_countries'] = specs.get('target_countries', 'UK, US, Canada')
            context['target_regions'] = specs.get('target_regions', 'Europe and North America')

        # Number of schools to research
        context['num_schools'] = specs.get('num_schools', 5)

        # Scholarship needs
        context['scholarship_name'] = specs.get('scholarship_name', 'merit-based scholarship')
        context['essay_topic'] = specs.get('essay_topic', 'your academic journey')
        context['financial_need'] = specs.get('financial_need', 'significant financial support needed')

        # Application deadlines
        context['deadline_earliest'] = self._extract_earliest_deadline(goal_spec)

        # Visa information
        context['country'] = specs.get('target_country', context['target_countries'].split(',')[0].strip())
        context['visa_type'] = specs.get('visa_type', 'Student Visa')
        context['financial_proof_amount'] = specs.get('financial_proof', context.get('max_tuition', '$20,000'))

        # Professor and university info (for outreach templates)
        context['professor_name'] = self._extract_professor_name(profile, goal_spec)
        context['university_name'] = self._extract_university_name(goal_spec, context)

        # Additional study variables for base templates
        field = context['field']
        context['target_score'] = specs.get('target_score', '7.0')
        context['current_score'] = specs.get('current_score', str(context.get('ielts_score', 6.0)))
        context['exam_month'] = specs.get('exam_month', 'next available')
        context['exam_date'] = specs.get('exam_date', 'your exam date')
        context['days_until_exam'] = specs.get('days_until_exam', 60)
        context['program_name'] = specs.get('program_name', f"Master's in {field}")
        context['key_project'] = context.get('top_projects', '').split(',')[0].strip() if context.get('top_projects') else f'your {field} project'
        context['key_project_1'] = context.get('top_projects', '').split(',')[0].strip() if context.get('top_projects') else f'your {field} project'
        context['key_project_2'] = context.get('top_projects', '').split(',')[1].strip() if ',' in context.get('top_projects', '') else f'another {field} project'
        context['career_goal'] = specs.get('career_goal', f'work in {field} research or industry')
        context['course_name'] = specs.get('course_name', f'{field} course')
        context['grade_received'] = specs.get('grade_received', 'A')
        context['early_deadline'] = context.get('deadline_earliest', '2025-11-15')
        context['fee'] = specs.get('application_fee', '$75')
        context['savings_amount'] = specs.get('savings', '$5,000')
        context['program_start_date'] = specs.get('program_start_date', 'September 2026')
        context['required_funds'] = context.get('financial_proof_amount', '$30,000')
        # Parse max_tuition to number for arithmetic, then format back
        max_tuition_num = self._parse_currency_to_number(context.get('max_tuition', '$20,000'))
        context['funding_gap'] = specs.get('funding_gap', f"${max_tuition_num - 5000:,}")
        weakness = context.get('weaknesses', 'writing')
        context['weakness'] = weakness
        context['test_name'] = specs.get('test_name', 'IELTS')
        context['week_number'] = specs.get('week_number', '1')
        context['how_improved'] = specs.get('how_improved', f'dedicated practice in {weakness}')
        context['research_area'] = context.get('research_interest', field)
        context['family_contribution'] = specs.get('family_contribution', '$10,000')
        context['skills'] = context.get('top_projects', f'{field} skills')
        context['target_university'] = context.get('university_name', context['target_universities'].split(',')[0].strip() if ',' in context['target_universities'] else context['target_universities'])
        context['your_background'] = f"{context.get('current_university', 'your university')} {field} student"
        context['weeks_until_test'] = specs.get('weeks_until_test', context.get('days_until_exam', 60) // 7)
        context['weakness_section'] = weakness
        context['total_cost'] = specs.get('total_cost', context.get('max_tuition', '$20,000'))
        context['gap_amount'] = specs.get('gap_amount', context.get('funding_gap', '$15,000'))

        return context

    def _extract_current_university(self, profile: Any, goal_spec: Any = None) -> str:
        """
        Extract current/most recent university from prior_education JSONField.

        ENHANCED: Falls back to GoalSpec.specifications when profile is empty.

        prior_education format (example):
        {
            "education": [
                {"institution": "University of Kazakhstan", "degree": "BSc CS", "year": 2023},
                {"institution": "High School #5", "degree": "Diploma", "year": 2019}
            ]
        }
        """
        prior_education = getattr(profile, 'prior_education', {}) or {}

        # Try profile first
        if prior_education:
            # Handle different JSON structures
            if isinstance(prior_education, dict):
                education_list = prior_education.get('education', [])
            elif isinstance(prior_education, list):
                education_list = prior_education
            else:
                education_list = []

            # Get most recent (assume first or last)
            if education_list:
                most_recent = education_list[0] if isinstance(education_list[0], dict) else {}
                institution = most_recent.get('institution', '')
                if institution:
                    return institution

        # ENHANCEMENT: Fall back to GoalSpec specifications
        if goal_spec:
            specs = getattr(goal_spec, 'specifications', {}) or {}

            # Check for explicitly set current university
            current_uni = specs.get('current_university')
            if current_uni:
                return current_uni

            # Use first target university as fallback (user is applying there)
            target_unis = specs.get('target_universities', [])
            if target_unis and isinstance(target_unis, list) and len(target_unis) > 0:
                return f"{target_unis[0]} (target)"

        return "your university"

    def _infer_degree_level(self, goal_spec: Any) -> str:
        """Infer degree level from goal title/description"""
        title = getattr(goal_spec, 'title', '').lower()
        description = getattr(goal_spec, 'description', '').lower()

        combined = f"{title} {description}"

        if 'phd' in combined or 'doctorate' in combined:
            return 'PhD'
        elif 'master' in combined or 'msc' in combined or 'ma ' in combined:
            return 'Master\'s'
        elif 'bachelor' in combined or 'bsc' in combined or 'ba ' in combined:
            return 'Bachelor\'s'
        else:
            return 'graduate'

    def _extract_career_context(self, profile: Any, goal_spec: Any) -> Dict[str, Any]:
        """Extract career-specific context with rich profile data"""
        context = {}

        # Experience level (prioritize structured field, fallback to years)
        experience_level = getattr(profile, 'experience_level', '')
        years = getattr(profile, 'years_of_experience', 0) or 0  # Handle None

        context['years_experience'] = years
        context['experience_level'] = experience_level if experience_level else self._map_experience_level(years)

        # Provide text version for templates (handles zero case gracefully)
        if years == 0 or experience_level == 'entry':
            context['years_experience_text'] = "early-career"
            context['years_text'] = "as an aspiring"  # "I'm an aspiring Software Engineer"
            context['job_search_strategy'] = 'entry-level'
            context['target_companies'] = 'startups and growing tech companies'
            context['job_search_focus'] = 'junior roles, internships, and entry-level positions'
        elif years == 1 or experience_level == 'junior':
            context['years_experience_text'] = "1 year of"
            context['years_text'] = "with 1 year of"
            context['job_search_strategy'] = 'junior'
            context['target_companies'] = 'mid-size companies and tech startups'
            context['job_search_focus'] = 'junior and mid-level roles'
        elif years <= 3 or experience_level == 'mid':
            context['years_experience_text'] = f"{years} years of" if years > 0 else "mid-level"
            context['years_text'] = f"with {years} years of" if years > 0 else "as a mid-level"
            context['job_search_strategy'] = 'mid-level'
            context['target_companies'] = 'established tech companies and competitive startups'
            context['job_search_focus'] = 'mid-level and senior roles'
        elif experience_level in ['senior', 'staff_plus'] or years >= 5:
            context['years_experience_text'] = f"{years} years of" if years > 0 else "senior"
            context['years_text'] = f"with {years} years of" if years > 0 else "as a senior"
            context['job_search_strategy'] = 'senior'
            context['target_companies'] = 'FAANG and top-tier tech companies'
            context['job_search_focus'] = 'senior and lead roles'
        else:
            context['years_experience_text'] = f"{years} years of"
            context['years_text'] = f"with {years} years of"
            context['job_search_strategy'] = 'mid-level'
            context['target_companies'] = 'established tech companies and competitive startups'
            context['job_search_focus'] = 'mid-level and senior roles'

        # Current role (prioritize career_specialization)
        career_specialization = getattr(profile, 'career_specialization', '')
        current_role = getattr(profile, 'current_role', '')
        context['current_role'] = career_specialization or current_role or 'your current role'
        context['career_specialization'] = career_specialization or current_role or 'your field'

        # Current company
        context['current_company'] = getattr(profile, 'current_company', 'your current company')

        # Target role (NEW: prioritize profile.target_role from conversational onboarding)
        specs = getattr(goal_spec, 'specifications', {}) or {}
        profile_target_role = getattr(profile, 'target_role', None)

        context['target_role'] = (
            profile_target_role or  # NEW: From conversational onboarding
            specs.get('target_role') or
            specs.get('targetRole') or
            specs.get('role') or
            getattr(goal_spec, 'title', 'your target role')  # Last resort: use goalspec title
        )

        context['target_industry'] = (
            specs.get('target_industry') or
            specs.get('industry') or
            'Tech'  # Common default
        )

        context['location'] = specs.get('location', 'Any')

        # Top skills (extract from skills JSONField or structured tech_stack)
        context['top_skills'] = self._extract_top_skills(profile)

        # Tech stack string (formatted for templates: "Python, React, PostgreSQL, AWS")
        # NEW: Prioritize conversational onboarding tech_stack (list format)
        tech_stack_from_convo = getattr(profile, 'tech_stack', None)

        # Check if it's from conversational onboarding (list) or old format (dict)
        if isinstance(tech_stack_from_convo, list) and tech_stack_from_convo:
            # NEW: Conversational onboarding format (list of strings)
            context['tech_stack_string'] = ', '.join(tech_stack_from_convo[:5])
            context['tech_stack_list'] = tech_stack_from_convo
        elif isinstance(tech_stack_from_convo, dict) and tech_stack_from_convo:
            # OLD: Structured format (dict with categories)
            all_skills = []
            for category in ['languages', 'frameworks', 'databases', 'cloud']:
                skill_list = tech_stack_from_convo.get(category, [])
                if isinstance(skill_list, list):
                    all_skills.extend(skill_list[:2])  # 2 per category
            context['tech_stack_string'] = ', '.join(all_skills[:5]) if all_skills else ', '.join(context['top_skills'][:3])
            context['tech_stack_list'] = all_skills
        else:
            # Fallback to top_skills
            context['tech_stack_string'] = ', '.join(context['top_skills'][:3]) if isinstance(context['top_skills'], list) else 'relevant technologies'
            context['tech_stack_list'] = context['top_skills'][:3] if isinstance(context['top_skills'], list) else []

        # Notable projects/achievements (NEW: conversational onboarding)
        # Prioritize notable_achievements (from conversational onboarding), fallback to notable_projects
        notable_achievements = getattr(profile, 'notable_achievements', []) or []
        notable_projects = getattr(profile, 'notable_projects', []) or []

        # Combine both sources
        all_notable = notable_achievements if notable_achievements else notable_projects
        context['notable_projects'] = all_notable
        context['notable_achievements'] = notable_achievements  # NEW field
        context['project_1'] = all_notable[0] if len(all_notable) > 0 else None
        context['project_2'] = all_notable[1] if len(all_notable) > 1 else None
        context['project_3'] = all_notable[2] if len(all_notable) > 2 else None

        # Target company types (NEW: conversational onboarding)
        # Prioritize target_companies (from conversational onboarding), fallback to target_company_types
        target_companies_from_convo = getattr(profile, 'target_companies', []) or []
        target_company_types = getattr(profile, 'target_company_types', []) or []

        # Use conversational data if available, otherwise use old format
        final_target_companies = target_companies_from_convo if target_companies_from_convo else target_company_types

        if final_target_companies:
            context['target_company_types'] = final_target_companies
            context['target_companies_string'] = ' & '.join(final_target_companies[:2])  # "Startups & FAANG"
        else:
            # Fallback to experience-level defaults (already set above)
            context['target_company_types'] = []
            context['target_companies_string'] = context['target_companies']  # Use the generic text

        # Skill gap (inferred from target role vs current skills)
        context['skill_gap'] = self._infer_skill_gap(profile, specs)

        # Warm introductions (extract from network JSONField)
        context['warm_intros'] = self._extract_warm_intros(profile)
        context['has_warm_intros'] = len(context['warm_intros']) > 0

        # Companies worked (for resume bullet points)
        context['companies_worked'] = self._extract_companies(profile)

        # Target companies (use profile data if available, otherwise fallback to specs)
        # FIX: Don't overwrite correctly extracted target_companies from profile
        if final_target_companies:
            # Use the list from conversational onboarding
            context['target_companies'] = ', '.join(final_target_companies[:5])
        else:
            # Only use generic fallback if no profile data exists
            context['target_companies'] = self._extract_target_companies(specs)

        # Achievements (from profile or work history)
        context['top_achievement'] = self._extract_top_achievement(profile)
        context['challenge_story'] = self._extract_challenge_story(profile)

        # Portfolio/online presence
        context['current_online_presence'] = self._extract_online_presence(profile)

        # Interview prep specifics
        context['company_name'] = specs.get('company_name', 'the company')
        context['role_title'] = context['target_role']
        context['key_requirement'] = specs.get('key_requirement', 'relevant experience')
        context['relevant_achievement'] = context['top_achievement']

        # Networking event details
        context['event_name'] = specs.get('event_name', 'upcoming networking event')
        context['elevator_pitch'] = self._build_elevator_pitch(profile, specs)

        # Salary negotiation
        context['market_rate'] = specs.get('market_rate', specs.get('salary', '$80-100k'))
        context['your_target'] = self._calculate_target_salary(context['market_rate'], years)
        context['unique_value'] = self._extract_unique_value(profile)

        # Job search specifics
        context['role_type'] = context['target_role']
        context['domain_name'] = specs.get('domain_name', f"{context['current_role'].lower().replace(' ', '')}.com")

        # LinkedIn profile data
        context['expertise_area'] = self._extract_expertise_area(profile)
        context['connection_point'] = self._extract_connection_point(profile, specs)

        # Technical interview
        context['key_technical_skill'] = self._extract_key_technical_skill(profile, specs)

        # Additional career variables for base templates
        # NEW: Prioritize tech_stack_list (from conversational onboarding), fallback to top_skills
        skills_for_templates = context.get('tech_stack_list', []) or context.get('top_skills', [])

        context['key_skill_1'] = skills_for_templates[0] if len(skills_for_templates) > 0 else 'your primary skill'
        context['key_skill_2'] = skills_for_templates[1] if len(skills_for_templates) > 1 else 'your secondary skill'
        context['key_skill_3'] = skills_for_templates[2] if len(skills_for_templates) > 2 else None

        # Skills summary (for LinkedIn headlines, resumes, etc.)
        if len(skills_for_templates) >= 3:
            context['skills_summary'] = ', '.join(skills_for_templates[:5])
        else:
            context['skills_summary'] = context.get('tech_stack_string', 'your skills')
        context['company_1'] = context['companies_worked'][0] if isinstance(context['companies_worked'], list) and len(context['companies_worked']) > 0 else 'previous company'
        context['company_2'] = context['companies_worked'][1] if isinstance(context['companies_worked'], list) and len(context['companies_worked']) > 1 else 'another company'
        context['unique_skill'] = context.get('expertise_area', context.get('key_skill_1', 'your unique skill'))
        context['why_company'] = specs.get('why_company', f"mission and {context['target_industry']} focus")
        context['applications_target'] = specs.get('applications_target', '10')
        # Referral/mutual connection (provide flag to conditionally show referral instructions)
        has_referral = context.get('has_warm_intros') and context.get('warm_intros')
        context['has_referral'] = has_referral
        context['mutual_connection'] = (
            context['warm_intros'][0]['name']
            if has_referral
            else 'a mutual contact'  # Generic fallback (better than [Mutual Connection Name])
        )
        context['num_positions'] = specs.get('num_positions', '20')
        context['common_ground'] = specs.get('common_ground', f"shared interest in {context['target_industry']}")
        context['event_date'] = specs.get('event_date', 'next month')
        context['tech_stack'] = ', '.join(context['top_skills'][:3]) if isinstance(context['top_skills'], list) else 'relevant technologies'
        context['practice_problems_count'] = specs.get('practice_problems', '50')
        context['key_qualification'] = context.get('top_achievement', f"experience in {context['target_role']}")
        context['contact_name'] = context['mutual_connection']
        context['num_people'] = specs.get('num_people', '10')
        context['learning_resources'] = specs.get('learning_resources', 'online courses and practice projects')
        context['learning_resource'] = context['learning_resources']
        context['current_skills'] = ', '.join(context['top_skills'][:4]) if isinstance(context['top_skills'], list) else 'your current skills'
        context['skills'] = context['top_skills']
        context['referral_name'] = context.get('mutual_connection', '[Referral Name]')
        context['contact_company'] = specs.get('contact_company', 'the company')
        context['purpose'] = specs.get('purpose', f"discuss opportunities in {context['target_industry']}")
        context['time_commitment_hours'] = specs.get('time_commitment', context.get('daily_minutes', 120) // 60)
        context['top_projects'] = specs.get('portfolio_projects', f"projects in {context['target_industry']}")
        context['university'] = specs.get('university', 'your university')

        return context

    def _map_experience_level(self, years: int) -> str:
        """Map years to experience level"""
        if years is None:
            return 'entry_level'  # Default for new users
        if years <= 2:
            return 'entry_level'
        elif years <= 7:
            return 'mid_level'
        else:
            return 'senior'

    def _extract_top_skills(self, profile: Any) -> List[str]:
        """
        Extract top 3-5 skills from structured tech_stack or legacy skills field.

        tech_stack format (priority 1):
        {
            "languages": ["Python", "JavaScript"],
            "frameworks": ["React", "Node.js"],
            "databases": ["PostgreSQL"],
            "cloud": ["AWS", "Docker"]
        }

        skills format (fallback):
        {
            "technical": ["Python", "React", "PostgreSQL"],
            "soft": ["Communication", "Leadership"]
        }
        OR
        ["Python", "React", "PostgreSQL", "AWS"]
        """
        # Priority 1: Check for structured tech_stack
        tech_stack = getattr(profile, 'tech_stack', {}) or {}

        if tech_stack and isinstance(tech_stack, dict):
            top_skills = []
            # Extract in priority order: languages → frameworks → databases → cloud
            for category in ['languages', 'frameworks', 'databases', 'cloud']:
                skill_list = tech_stack.get(category, [])
                if isinstance(skill_list, list):
                    top_skills.extend(skill_list[:2])  # Take first 2 from each category

            if top_skills:
                return top_skills[:5]  # Return top 5 overall

        # Priority 2: Check for legacy skills field
        skills = getattr(profile, 'skills', {}) or {}

        if not skills:
            return ["your key skills"]

        top_skills = []

        # Handle different JSON structures
        if isinstance(skills, dict):
            # Combine all skill categories
            for category, skill_list in skills.items():
                if isinstance(skill_list, list):
                    top_skills.extend(skill_list[:3])  # Take first 3 from each category
        elif isinstance(skills, list):
            top_skills = skills[:5]

        return top_skills[:5] if top_skills else ["your key skills"]

    def _extract_warm_intros(self, profile: Any) -> List[Dict[str, str]]:
        """
        Extract warm introductions from network JSONField.

        network format (example):
        {
            "contacts": [
                {"name": "John Smith", "company": "Google", "role": "SWE", "relationship": "former colleague"},
                {"name": "Jane Doe", "company": "Meta", "role": "Manager", "relationship": "university friend"}
            ]
        }
        """
        network = getattr(profile, 'network', {}) or {}

        if not network:
            return []

        contacts = []

        # Handle different JSON structures
        if isinstance(network, dict):
            contact_list = network.get('contacts', [])
        elif isinstance(network, list):
            contact_list = network
        else:
            return []

        # Extract relevant contacts with company info
        for contact in contact_list:
            if isinstance(contact, dict) and 'company' in contact:
                contacts.append({
                    'name': contact.get('name', 'Contact'),
                    'company': contact.get('company', ''),
                    'role': contact.get('role', ''),
                    'relationship': contact.get('relationship', 'connection')
                })

        return contacts[:5]  # Return top 5 contacts

    def _extract_companies(self, profile: Any) -> List[str]:
        """Extract list of companies worked at"""
        companies = getattr(profile, 'companies_worked', []) or []

        if isinstance(companies, list):
            return companies[:3]  # Top 3 companies
        elif isinstance(companies, str):
            # Handle comma-separated string
            return [c.strip() for c in companies.split(',')][:3]

        return []

    def _extract_fitness_context(self, profile: Any, goal_spec: Any) -> Dict[str, Any]:
        """Extract fitness-specific context"""
        context = {}

        # Fitness level
        context['fitness_level'] = getattr(profile, 'fitness_level', 'beginner')

        # Gym access
        gym_access = getattr(profile, 'gym_access', False)
        context['gym_access'] = gym_access
        context['workout_location'] = 'gym' if gym_access else 'home'

        # Injuries/limitations
        limitations = getattr(profile, 'injuries_limitations', None)
        context['has_limitations'] = bool(limitations)
        context['limitations'] = limitations if limitations else 'none'

        # Fitness goal (from specs)
        specs = getattr(goal_spec, 'specifications', {}) or {}
        context['fitness_goal'] = specs.get('goal_type', 'general fitness')
        context['target_weight'] = specs.get('target_weight', 'your target weight')

        return context

    def _extract_goal_specs(self, goal_spec: Any) -> Dict[str, Any]:
        """Extract goal specifications and constraints"""
        context = {}

        # Budget (extract from specs or constraints)
        # NOTE: Profile budget is extracted in _extract_study_context where profile is available
        specs = getattr(goal_spec, 'specifications', {}) or {}
        constraints = getattr(goal_spec, 'constraints', {}) or {}

        budget_str = specs.get('budget') or constraints.get('budget') or ''
        context['budget'] = budget_str
        context['max_tuition'] = self._parse_max_tuition(budget_str)

        # Timeline (extract deadline)
        context['deadline'] = constraints.get('deadline', 'your deadline')

        # Priority
        context['priority'] = getattr(goal_spec, 'priority', 2)

        return context

    def _parse_currency_to_number(self, currency_str: str) -> int:
        """
        Parse a formatted currency string back to a number.

        Examples:
        - "$20,000" -> 20000
        - "£15,000" -> 15000
        - "20000" -> 20000
        """
        if not currency_str:
            return 20000

        # Remove currency symbols, commas, and spaces
        clean = str(currency_str).replace('$', '').replace('£', '').replace('€', '').replace(',', '').strip()

        try:
            return int(float(clean))
        except (ValueError, TypeError):
            print(f"[ProfileExtractor] Could not parse currency to number: {currency_str}")
            return 20000

    def _parse_max_tuition(self, budget_str: str) -> str:
        """
        Parse budget string to max tuition.

        Examples:
        - "$15k" -> "$15,000"
        - "£20k-30k" -> "£20,000"
        - "≤£10k" -> "£10,000"
        - "" -> "$20,000" (default)
        """
        if not budget_str:
            return "$20,000"

        # Remove spaces and comparison symbols
        clean = budget_str.strip()
        clean = clean.replace('≤', '').replace('≥', '').replace('<', '').replace('>', '').strip()

        # Get currency symbol (check before removing)
        currency = '$'
        if '£' in clean:
            currency = '£'
        elif '€' in clean:
            currency = '€'

        # Remove currency symbols and extra spaces
        clean = clean.replace('$', '').replace('£', '').replace('€', '').strip()

        # Handle range (take lower bound)
        if '-' in clean:
            clean = clean.split('-')[0].strip()

        # Handle 'k' suffix (case insensitive)
        if 'k' in clean.lower():
            # Remove 'k' and multiply by 1000
            clean = clean.lower().replace('k', '').strip()
            try:
                value = float(clean) * 1000
            except ValueError:
                print(f"[ProfileExtractor] Could not parse budget: {budget_str}")
                return f"{currency}20,000"
        else:
            # No 'k' suffix, parse directly
            try:
                value = float(clean)
            except ValueError:
                print(f"[ProfileExtractor] Could not parse budget: {budget_str}")
                return f"{currency}20,000"

        # Format with commas
        return f"{currency}{int(value):,}"

    def _extract_academic_projects(self, profile: Any) -> str:
        """
        Extract top academic projects from prior_education or profile.

        Returns formatted string of project names.
        """
        prior_education = getattr(profile, 'prior_education', {}) or {}

        # Try to extract projects from prior_education
        if isinstance(prior_education, dict):
            projects = prior_education.get('projects', [])
            if projects and isinstance(projects, list):
                return ', '.join(projects[:3])  # Top 3 projects

        # Fallback to generic based on field
        field = getattr(profile, 'field_of_study', 'your field')
        return f"your {field} projects"

    def _extract_research_interest(self, profile: Any, goal_spec: Any) -> str:
        """Extract research interest from profile or goal"""
        specs = getattr(goal_spec, 'specifications', {}) or {}

        # Check goal specs first
        research = specs.get('research_interest') or specs.get('research_area')
        if research:
            return research

        # Check prior_education
        prior_education = getattr(profile, 'prior_education', {}) or {}
        if isinstance(prior_education, dict):
            research = prior_education.get('research_interest')
            if research:
                return research

        # Fallback to field of study
        field = getattr(profile, 'field_of_study', 'your field')
        return field

    def _extract_target_universities(self, goal_spec: Any) -> str:
        """
        Extract specific target universities from goal specs.

        ENHANCED: Better fallback based on country/region instead of hardcoded "Oxford".
        """
        specs = getattr(goal_spec, 'specifications', {}) or {}

        target_unis = specs.get('target_universities') or specs.get('universities')
        if target_unis:
            if isinstance(target_unis, list):
                return ', '.join(target_unis[:5])
            return target_unis

        # IMPROVED FALLBACK: Use country/region-specific defaults
        country = specs.get('country', '').upper()

        if country == 'UK':
            return "top UK universities (Oxford, Cambridge, Imperial)"
        elif country in ['USA', 'US']:
            return "top US universities (MIT, Stanford, Harvard)"
        elif country == 'CANADA':
            return "top Canadian universities (Toronto, UBC, McGill)"
        elif country == 'AUSTRALIA':
            return "top Australian universities (ANU, Melbourne, Sydney)"
        else:
            return "top universities in your target country"

    def _extract_professor_contacts(self, profile: Any) -> List[Dict[str, str]]:
        """Extract professors from network contacts"""
        network = getattr(profile, 'network', {}) or {}

        if not network:
            return []

        contacts = []
        contact_list = network.get('contacts', []) if isinstance(network, dict) else network

        for contact in contact_list if isinstance(contact_list, list) else []:
            if isinstance(contact, dict):
                role = contact.get('role', '').lower()
                # Check if contact is academic (professor, researcher, etc.)
                if 'professor' in role or 'researcher' in role or 'phd' in role or 'academic' in role:
                    contacts.append({
                        'name': contact.get('name', 'Professor'),
                        'university': contact.get('company', 'University'),
                        'relationship': contact.get('relationship', 'connection')
                    })

        return contacts[:3]  # Top 3 professor contacts

    def _extract_professor_name(self, profile: Any, goal_spec: Any) -> str:
        """Extract a professor name from network or use placeholder"""
        # Check goal specs first
        specs = getattr(goal_spec, 'specifications', {}) or {}
        if specs.get('professor_name'):
            return specs['professor_name']

        # Check network for professor contacts
        professor_contacts = self._extract_professor_contacts(profile)
        if professor_contacts:
            return professor_contacts[0]['name']

        # Placeholder
        return "[Professor Name]"

    def _extract_university_name(self, goal_spec: Any, context: Dict[str, Any]) -> str:
        """Extract a specific university name for targeting"""
        # Check goal specs first
        specs = getattr(goal_spec, 'specifications', {}) or {}
        if specs.get('university_name'):
            return specs['university_name']

        # Extract first target university from list
        target_universities = context.get('target_universities', '')
        if target_universities and ',' in target_universities:
            return target_universities.split(',')[0].strip()
        elif target_universities:
            return target_universities

        # Placeholder
        return "[University Name]"

    def _extract_earliest_deadline(self, goal_spec: Any) -> str:
        """Extract earliest deadline from goal timeline"""
        timeline = getattr(goal_spec, 'timeline', {}) or {}

        if isinstance(timeline, dict):
            milestones = timeline.get('milestones', [])
            if milestones and isinstance(milestones, list):
                # Get earliest deadline
                earliest = min([m.get('target_date', '2025-12-31') for m in milestones if isinstance(m, dict)])
                return earliest

        # Check constraints
        constraints = getattr(goal_spec, 'constraints', {}) or {}
        deadline = constraints.get('deadline')
        if deadline:
            return deadline

        # Default to 6 months from now
        from datetime import datetime, timedelta
        future = datetime.now() + timedelta(days=180)
        return future.strftime('%Y-%m-%d')

    def _infer_skill_gap(self, profile: Any, specs: Dict[str, Any]) -> str:
        """Infer primary skill gap for target role"""
        target_role = specs.get('target_role', specs.get('targetRole', '')).lower()

        # Common skill gaps by role
        role_skills = {
            'product manager': 'product strategy and roadmapping',
            'data scientist': 'machine learning and statistics',
            'software engineer': 'system design and algorithms',
            'ux designer': 'user research and prototyping',
            'marketing': 'digital marketing and analytics',
        }

        for role, skill in role_skills.items():
            if role in target_role:
                return skill

        return 'relevant technical skills'

    def _extract_target_companies(self, specs: Dict[str, Any]) -> str:
        """Extract target companies from specs"""
        companies = specs.get('target_companies') or specs.get('companies')

        if companies:
            if isinstance(companies, list):
                return ', '.join(companies[:5])
            return companies

        # Default based on industry
        industry = specs.get('target_industry', specs.get('industry', '')).lower()
        if 'tech' in industry:
            return 'Google, Meta, Apple, Amazon, Microsoft'
        elif 'finance' in industry:
            return 'Goldman Sachs, JP Morgan, BlackRock'
        else:
            return 'top companies in your industry'

    def _extract_top_achievement(self, profile: Any) -> str:
        """Extract top career achievement"""
        # Priority 1: Check notable_projects (new rich field)
        notable_projects = getattr(profile, 'notable_projects', []) or []
        if notable_projects and isinstance(notable_projects, list) and len(notable_projects) > 0:
            project = notable_projects[0]
            if isinstance(project, dict):
                # Extract impact or title
                return project.get('impact') or project.get('title', '')

        # Priority 2: Check if profile has achievements field (legacy)
        achievements = getattr(profile, 'achievements', None)
        if achievements and isinstance(achievements, list) and len(achievements) > 0:
            return achievements[0]

        # Fallback: Generate generic based on role
        current_role = getattr(profile, 'current_role', 'your role')
        return f"led successful project in {current_role}"

    def _extract_challenge_story(self, profile: Any) -> str:
        """Extract a challenge/conflict story"""
        # Check if profile has challenges field
        challenges = getattr(profile, 'challenges', None)
        if challenges and isinstance(challenges, list) and len(challenges) > 0:
            return challenges[0]

        return "overcame significant technical/organizational challenge"

    def _extract_online_presence(self, profile: Any) -> str:
        """Extract online portfolio/website info"""
        # Check for portfolio URL
        portfolio = getattr(profile, 'portfolio_url', None)
        if portfolio:
            return portfolio

        # Check for GitHub
        github = getattr(profile, 'github_url', None)
        if github:
            return f"GitHub: {github}"

        return "LinkedIn profile"

    def _build_elevator_pitch(self, profile: Any, specs: Dict[str, Any]) -> str:
        """Build elevator pitch from profile"""
        current_role = getattr(profile, 'current_role', 'professional')
        years = getattr(profile, 'years_of_experience', 0) or 0  # Handle None
        target_role = specs.get('target_role', specs.get('targetRole', 'new role'))

        skills = self._extract_top_skills(profile)
        skill_str = ', '.join(skills[:2]) if isinstance(skills, list) else 'relevant skills'

        return f"I'm a {current_role} with {years} years specializing in {skill_str}, looking to transition to {target_role}"

    def _calculate_target_salary(self, market_rate: str, years: int) -> str:
        """Calculate target salary based on market rate and experience"""
        # Extract number from market rate string
        import re
        numbers = re.findall(r'\d+', market_rate)

        if numbers:
            base = int(numbers[0]) * 1000 if 'k' in market_rate.lower() else int(numbers[0])
            # Add 10-15% based on experience
            multiplier = 1.1 if (years and years > 5) else 1.05
            target = int(base * multiplier)

            # Format with k suffix
            if target >= 1000:
                return f"${target // 1000}k"
            return f"${target}"

        return "$85k"

    def _extract_unique_value(self, profile: Any) -> str:
        """Extract unique value proposition"""
        years = getattr(profile, 'years_of_experience', 0) or 0  # Handle None
        companies = self._extract_companies(profile)

        if companies and len(companies) > 0:
            return f"{years} years experience including work at {companies[0]}"

        skills = self._extract_top_skills(profile)
        if isinstance(skills, list) and len(skills) > 0:
            return f"strong background in {skills[0]}"

        return f"{years} years of relevant experience"

    def _extract_expertise_area(self, profile: Any) -> str:
        """Extract primary area of expertise"""
        field = getattr(profile, 'field_of_study', None)
        if field:
            return field

        skills = self._extract_top_skills(profile)
        if isinstance(skills, list) and len(skills) > 0:
            return skills[0]

        current_role = getattr(profile, 'current_role', 'your field')
        return current_role

    def _extract_connection_point(self, profile: Any, specs: Dict[str, Any]) -> str:
        """Extract connection point for networking"""
        # Check if there's a specific connection mentioned in specs
        connection = specs.get('connection_point')
        if connection:
            return connection

        # Check network for alumni connection
        network = getattr(profile, 'network', {}) or {}
        if isinstance(network, dict):
            contacts = network.get('contacts', [])
            if contacts and len(contacts) > 0:
                return f"we share a mutual connection: {contacts[0].get('name', 'a colleague')}"

        # Check prior_education for alumni connection
        prior_education = getattr(profile, 'prior_education', {}) or {}
        if isinstance(prior_education, dict):
            education_list = prior_education.get('education', [])
            if education_list and len(education_list) > 0:
                university = education_list[0].get('institution', '')
                return f"I'm a fellow {university} alumni"

        return "I found you through LinkedIn"

    def _extract_key_technical_skill(self, profile: Any, specs: Dict[str, Any]) -> str:
        """Extract key technical skill for interview prep"""
        # Check if specified in goal
        key_skill = specs.get('key_technical_skill') or specs.get('technical_skill')
        if key_skill:
            return key_skill

        # Extract from target role
        target_role = specs.get('target_role', specs.get('targetRole', '')).lower()

        role_skills = {
            'software engineer': 'data structures and algorithms',
            'data scientist': 'machine learning',
            'product manager': 'product strategy',
            'designer': 'design thinking',
        }

        for role, skill in role_skills.items():
            if role in target_role:
                return skill

        # Fallback to top skill
        skills = self._extract_top_skills(profile)
        if isinstance(skills, list) and len(skills) > 0:
            return skills[0]

        return 'relevant technical concepts'


# Singleton instance
profile_extractor = ProfileExtractor()
