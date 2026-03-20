"""
AI Task Enhancer Service

Enriches Todo records with AI-generated detailed instructions, deadlines, and university-specific context.

Key features:
1. Batch AI calls (group by requirement_key to reduce cost)
2. University deadline lookup from University model
3. Step-by-step instruction generation
4. University-specific context and tips
"""

import json
import logging
from datetime import timedelta
from django.core.cache import cache
from django.utils import timezone
from django.db.models import Q

logger = logging.getLogger(__name__)


class AITaskEnhancer:
    """
    Enhance Todo records with AI-generated detailed instructions.

    Strategy:
    - Batch todos by requirement_key (e.g., all 'application_portal' tasks)
    - Single AI call per batch (cost optimization)
    - Parse response and update each Todo with detailed steps
    - Apply real university deadlines from University model
    """

    def __init__(self, user):
        self.user = user

    def enhance_todos(self, todos, shortlist, requirement_instances):
        """
        Enhance todos with AI-generated details.

        Args:
            todos: List of Todo objects to enhance
            shortlist: User's university shortlist
            requirement_instances: User's requirement instances

        Returns:
            dict: {enhanced_count, cost, cached_count, errors}
        """
        # Group todos by requirement_key
        todo_groups = self._group_by_requirement_key(todos)

        stats = {
            'enhanced': 0,
            'cost': 0.0,
            'cached': 0,
            'errors': []
        }

        # Enhance each group with single AI call
        for requirement_key, group_todos in todo_groups.items():
            try:
                result = self._enhance_group(
                    requirement_key=requirement_key,
                    todos=group_todos,
                    shortlist=shortlist
                )
                stats['enhanced'] += result.get('enhanced', 0)
                # Convert Decimal to float for addition
                cost = result.get('cost', 0.0)
                if hasattr(cost, '__float__'):
                    stats['cost'] += float(cost)
                else:
                    stats['cost'] += cost
                if result.get('cached'):
                    stats['cached'] += result.get('enhanced', 0)

            except Exception as e:
                stats['errors'].append(f"{requirement_key}: {str(e)}")
                logger.error(f"Failed to enhance {requirement_key}: {e}", exc_info=True)

        logger.info(f"AI enhancement complete: {stats['enhanced']} enhanced, {stats['cached']} cached, ${stats['cost']:.4f}")
        return stats

    def _enhance_group(self, requirement_key, todos, shortlist):
        """
        Enhance a group of todos with same requirement_key.

        Example: All 'application_portal' tasks for 4 universities
        """
        # Build university context map (only for university-specific tasks)
        uni_context = {}
        for todo in todos:
            if todo.university:
                uni_context[todo.university.id] = {
                    'id': todo.university.id,
                    'name': todo.university.name,
                    'short_name': todo.university.short_name,
                    'portal': todo.university.application_portal or '',
                    'deadline': self._get_deadline(todo.university).isoformat(),
                    'country': todo.university.location_country,
                    'location_city': todo.university.location_city or ''
                }

        # Skip global tasks (no universities)
        if not uni_context:
            logger.info(f"No universities found for {requirement_key}, skipping AI enhancement (global task)")
            return {'enhanced': 0, 'cost': 0.0}

        # Check cache first
        university_ids = list(uni_context.keys())
        cache_key = self._get_cache_key(requirement_key, university_ids)

        cached_enhancements = cache.get(cache_key)
        if cached_enhancements:
            logger.info(f"Cache hit for {requirement_key}, applying cached enhancements")
            self._apply_enhancements(todos, cached_enhancements, uni_context)
            return {'enhanced': len(todos), 'cost': 0.0, 'cached': True}

        # Build AI prompt
        prompt = self._build_enhancement_prompt(
            requirement_key=requirement_key,
            universities=uni_context,
            user_profile=self._get_user_profile()
        )

        # Call LLM
        try:
            from ai.llm_service import LLMService
            llm_service = LLMService()

            result = llm_service.generate(
                prompt=prompt,
                max_tokens=3000,
                temperature=0.7
            )

            # Parse response
            enhancements = self._parse_enhancement_response(
                response=result.get('text', ''),
                requirement_key=requirement_key
            )

            if not enhancements:
                logger.warning(f"No enhancements parsed for {requirement_key}")
                return {'enhanced': 0, 'cost': result.get('cost', 0.0)}

            # Cache for 24 hours
            cache.set(cache_key, enhancements, timeout=86400)

            # Apply to todos
            self._apply_enhancements(todos, enhancements, uni_context)

            return {
                'enhanced': len(todos),
                'cost': result.get('cost', 0.0),
                'cached': False
            }

        except ImportError:
            logger.error("LLMService not available, skipping AI enhancement")
            return {'enhanced': 0, 'cost': 0.0}

    def _apply_enhancements(self, todos, enhancements, uni_context):
        """Apply parsed enhancements to todos."""
        for todo in todos:
            # Skip todos without universities
            if not todo.university:
                logger.debug(f"Skipping enhancement for todo without university: {todo.title}")
                continue

            uni_id = str(todo.university.id)

            if uni_id not in enhancements:
                logger.warning(f"No enhancement found for university {uni_id} ({todo.university.name})")
                continue

            enhancement = enhancements[uni_id]

            # Update description
            if enhancement.get('description'):
                todo.description = enhancement['description']

            # Update notes with steps, context, tips
            notes = {
                'steps': enhancement.get('steps', []),
                'university_context': enhancement.get('university_context', ''),
                'tips': enhancement.get('tips', []),
            }

            # Add estimated cost if provided
            if enhancement.get('estimated_cost'):
                notes['estimated_cost'] = enhancement['estimated_cost']

            # Add document checklist if provided
            if enhancement.get('document_checklist'):
                notes['document_checklist'] = enhancement['document_checklist']

            todo.notes = notes

            # Update scheduled date if provided
            if enhancement.get('deadline'):
                try:
                    from datetime import datetime
                    todo.scheduled_date = datetime.strptime(
                        enhancement['deadline'],
                        '%Y-%m-%d'
                    ).date()
                except (ValueError, TypeError):
                    pass  # Keep existing date

            # Update priority if provided
            if enhancement.get('priority'):
                try:
                    todo.priority = int(enhancement['priority'])
                    # Ensure priority is in valid range
                    todo.priority = max(1, min(3, todo.priority))
                except (ValueError, TypeError):
                    pass  # Keep existing priority

            # Update timebox if provided
            if enhancement.get('estimated_minutes'):
                try:
                    todo.timebox_minutes = int(enhancement['estimated_minutes'])
                except (ValueError, TypeError):
                    pass

            todo.save(update_fields=[
                'description', 'notes', 'scheduled_date',
                'priority', 'timebox_minutes'
            ])

    def _build_enhancement_prompt(self, requirement_key, universities, user_profile):
        """Build detailed prompt for task enhancement."""
        # Format requirement key for display
        req_display = requirement_key.replace('_', ' ').title()

        # Build university list
        uni_list = []
        for uni_id, uni in universities.items():
            uni_list.append(f"\nID {uni_id}: {uni['name']} ({uni['country']})")
            if uni.get('portal'):
                uni_list.append(f"  Portal: {uni['portal']}")
            if uni.get('deadline'):
                uni_list.append(f"  Deadline: {uni['deadline']}")
            if uni.get('location_city'):
                uni_list.append(f"  City: {uni['location_city']}")

        uni_text = "\n".join(uni_list)

        prompt = f"""You are an expert college application advisor with 20 years of experience helping international students.

USER PROFILE:
- IELTS Score: {user_profile.get('ielts_score', 'N/A')}
- SAT Score: {user_profile.get('sat_score', 'N/A')}
- GPA: {user_profile.get('gpa', 'N/A')}
- Intended Major: {user_profile.get('intended_major', 'N/A')}
- Citizenship: {user_profile.get('citizenship', 'N/A')}

TASK: Generate detailed step-by-step instructions for "{req_display}".

REQUIREMENT:
This task must be completed for EACH university. Provide university-specific instructions.

UNIVERSITIES ({len(universities)}):
{uni_text}

For EACH university, provide:
1. description: Detailed description (2-3 sentences explaining what this task involves)
2. steps: Step-by-step instructions (numbered list, 5-12 specific actionable steps)
3. university_context: University-specific information (e.g., "Uses portal called 'Servizi Online'", "Requires documents in Italian")
4. tips: 3-5 specific tips for this university (e.g., "Portfolio should highlight 10-15 works", "Use Chrome browser")
5. deadline: The actual deadline (use format YYYY-MM-DD)
6. estimated_minutes: Realistic time estimate to complete this task
7. priority: Priority level 1-3 (3=critical/deadline soon, 2=important, 1=can wait)
8. estimated_cost: Any fees (e.g., "€50 application fee") or "No fee"

OUTPUT FORMAT:
Return ONLY valid JSON with university ID as string key:
{{
  "68": {{
    "description": "Create account on Politecnico di Milano's online application portal...",
    "steps": [
      "1. Go to https://www.polimi.it/servizionline/",
      "2. Click 'Register' to create account",
      "3. Fill in personal information",
      "4. Upload academic transcripts in PDF format",
      "5. Upload architecture portfolio (max 10MB PDF)"
    ],
    "university_context": "Politecnico di Milano uses 'Servizi Online' portal for all applications...",
    "tips": [
      "Portfolio should highlight 10-15 best architectural works",
      "All documents must be in PDF format under 10MB",
      "Portal supports English and Italian"
    ],
    "deadline": "2025-01-15",
    "estimated_minutes": 120,
    "priority": 3,
    "estimated_cost": "€50 application fee"
  }},
  "73": {{...}}
}}

CRITICAL REQUIREMENTS:
- Return ONLY valid JSON, no markdown, no code blocks
- Use EXACT university IDs: {list(universities.keys())}
- Steps must be actionable (use imperative verbs: "Go to", "Click", "Upload")
- Include specific URLs when available
- Mention document formats and size limits
- Highlight university-specific requirements
- Set realistic time estimates
- Priority 3 = deadline within 30 days, 2 = within 60 days, 1 = later
"""

        return prompt

    def _get_deadline(self, university):
        """
        Get appropriate deadline for university.

        Priority:
        1. early_decision_deadline (if exists and in future)
        2. regular_decision_deadline
        """
        now = timezone.now().date()

        if university.early_decision_deadline:
            if university.early_decision_deadline > now:
                return university.early_decision_deadline

        if university.regular_decision_deadline:
            return university.regular_decision_deadline

        # Fallback: 60 days from now
        return now + timedelta(days=60)

    def _get_user_profile(self):
        """Get user profile for personalization."""
        try:
            from university_profile.models import UniversitySeekerProfile
            profile = UniversitySeekerProfile.objects.filter(user=self.user).first()

            if not profile:
                return {}

            return {
                'ielts_score': profile.ielts_score,
                'sat_score': profile.sat_score,
                'gpa': profile.gpa,
                'intended_major': profile.intended_major_1 or 'Architecture',
                'citizenship': profile.citizenship or 'Kazakhstan',
            }

        except Exception as e:
            logger.warning(f"Could not get user profile: {e}")
            return {}

    def _parse_enhancement_response(self, response, requirement_key):
        """Parse JSON response from LLM."""
        try:
            # Clean up response
            text = response.strip()

            # Remove markdown code blocks if present
            if text.startswith('```'):
                first = text.find('```')
                last = text.rfind('```')
                if last > first:
                    text = text[first+3:last]
                    text = text.strip()
                    if text.startswith('json'):
                        text = text[4:].strip()

            enhancements = json.loads(text)
            logger.info(f"Successfully parsed enhancements for {requirement_key}: {list(enhancements.keys())}")
            return enhancements

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response for {requirement_key}: {e}")
            logger.debug(f"Response text: {response[:500]}")
            return {}

    def _group_by_requirement_key(self, todos):
        """Group todos by requirement_key for batch processing."""
        groups = {}
        for todo in todos:
            key = todo.requirement_key or 'other'
            if key not in groups:
                groups[key] = []
            groups[key].append(todo)
        return groups

    def _get_cache_key(self, requirement_key, university_ids):
        """Generate cache key for AI enhancement."""
        import hashlib
        # Sort IDs for consistent key
        sorted_ids = sorted(university_ids)
        key_data = f"{requirement_key}:{','.join(map(str, sorted_ids))}"
        return f"ai_task_enhance:{hashlib.md5(key_data.encode()).hexdigest()}"
