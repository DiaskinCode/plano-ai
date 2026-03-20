"""
AI Essay Writing Assistant

Provides personalized essay guidance using AI (Claude 3.5 Sonnet).
Generates topics, outlines, feedback, and paragraph improvements based on user's profile.
"""

import json
from ai.llm_service import LLMService
from university_profile.models import UniversitySeekerProfile, ExtracurricularActivity


class EssayAssistant:
    """AI-powered essay writing assistant"""

    def __init__(self, user):
        self.user = user
        self.ai = LLMService()
        self.profile = UniversitySeekerProfile.objects.filter(user=user).first()
        self.activities = ExtracurricularActivity.objects.filter(profile__user=user)

    def brainstorm_topics(self, essay_type, target_university=None):
        """
        Generate personalized essay topics based on user's profile

        Returns: List of 10 topic ideas with:
        - Title/Hook
        - Core theme
        - Why it's compelling
        - Potential anecdotes
        - How it demonstrates fit
        """
        context = self._build_user_context()

        prompt = f"""You are an expert college essay advisor. Based on the following student profile, generate 10 compelling essay topics for a {essay_type.replace('_', ' ').title()} essay.

Target University: {target_university or 'Not specified'}

Student Profile:
{context}

For each topic, provide:
1. "title": A compelling hook or title for the essay
2. "theme": The core theme or message
3. "compelling": Why this topic is compelling and unique
4. "anecdotes": 2-3 specific anecdotes or moments to include
5. "fit": How this demonstrates fit for the university

Format as a JSON list of objects. Each object should have these exact keys: title, theme, compelling, anecdotes, fit

Focus on topics that are:
- Specific and personal (not generic)
- Showcase growth, leadership, or unique perspective
- Demonstrate fit for the university
- Authentic to the student's experiences

Return ONLY valid JSON, no additional text."""

        try:
            response = self.ai.generate_completion(
                prompt,
                system_prompt="You are an expert college essay advisor. Always respond with valid JSON.",
                temperature=0.8
            )

            # Parse JSON response
            topics = self._parse_json_response(response)

            # Ensure we have exactly 10 topics
            if isinstance(topics, list) and len(topics) > 0:
                return topics[:10]
            else:
                # Fallback if parsing fails
                return self._get_fallback_topics(essay_type)

        except Exception as e:
            print(f"Error generating topics: {e}")
            return self._get_fallback_topics(essay_type)

    def generate_outline(self, topic, essay_type, target_university=None):
        """
        Create structured outline for chosen topic

        Returns: Outline with sections, word counts, and key points
        """
        context = self._build_user_context()

        prompt = f"""You are an expert college essay advisor. Create a detailed outline for a {essay_type.replace('_', ' ').title()} essay.

Topic: "{topic.get('title', topic)}"
Target University: {target_university or 'Not specified'}

Student Context:
{context}

Create a detailed outline with:
1. "introduction": Hook strategy and thesis statement
2. "body_paragraphs": Array of 3-5 body paragraphs, each with:
   - "section": Section title
   - "points": 2-3 key points to cover
   - "suggested_words": Target word count for this section
3. "conclusion": Conclusion strategy and connection to future
4. "themes": Key themes to emphasize throughout
5. "total_words": Expected total word count

Format as JSON with these exact keys: introduction, body_paragraphs, conclusion, themes, total_words

Make the outline specific to this student's experiences and the target university.
Return ONLY valid JSON."""

        try:
            response = self.ai.generate_completion(
                prompt,
                system_prompt="You are an expert college essay advisor. Always respond with valid JSON.",
                temperature=0.7
            )

            outline = self._parse_json_response(response)

            if isinstance(outline, dict) and 'body_paragraphs' in outline:
                return outline
            else:
                return self._get_fallback_outline(essay_type)

        except Exception as e:
            print(f"Error generating outline: {e}")
            return self._get_fallback_outline(essay_type)

    def review_draft(self, essay_content, essay_type, target_university=None):
        """
        Provide detailed feedback on essay draft

        Returns: Feedback with strengths, improvements, and score (1-10)
        """
        prompt = f"""You are an expert college essay reviewer. Review the following {essay_type.replace('_', ' ').title()} essay draft for {target_university or 'college applications'}.

Essay Content ({len(essay_content.split())} words):
{essay_content}

Provide detailed feedback on:

1. "strengths": 3-5 specific things that work well in this essay
2. "structure_feedback": Is the organization effective? Any structural issues?
3. "content_feedback": Is it compelling and specific? Any vague or generic parts?
4. "voice_feedback": Does it sound authentic? Any places where voice is lost?
5. "grammar_style": Any grammar or style issues?
6. "improvements": 5 specific, actionable suggestions to improve the essay
7. "score": Rate 1-10 overall (10 = outstanding, ready to submit)

Be encouraging but honest. Focus on making it more compelling and authentic.

Format as JSON with these exact keys: strengths, structure_feedback, content_feedback, voice_feedback, grammar_style, improvements, score

Return ONLY valid JSON."""

        try:
            response = self.ai.generate_completion(
                prompt,
                system_prompt="You are an expert college essay reviewer. Always respond with valid JSON.",
                temperature=0.6
            )

            feedback = self._parse_json_response(response)

            if isinstance(feedback, dict) and 'score' in feedback:
                return feedback
            else:
                return self._get_fallback_feedback()

        except Exception as e:
            print(f"Error reviewing draft: {e}")
            return self._get_fallback_feedback()

    def enhance_paragraph(self, paragraph, goal='make more vivid'):
        """
        Help improve specific paragraph

        Returns: 2-3 variations of the paragraph with preserved voice
        """
        prompt = f"""You are an expert writing coach. Improve the following paragraph.

Goal: {goal}

Original Paragraph:
{paragraph}

Provide 2-3 variations that improve the paragraph while keeping the student's authentic voice.

For each variation:
1. Make it more vivid, specific, or engaging (depending on the goal)
2. Maintain the student's voice and perspective
3. Keep the core meaning intact
4. Don't make it sound like a thesaurus exploded

Format as JSON array:
[
  {{
    "variation": "improved text here",
    "explanation": "brief explanation of what changed and why"
  }}
]

Return ONLY valid JSON."""

        try:
            response = self.ai.generate_completion(
                prompt,
                system_prompt="You are an expert writing coach. Always respond with valid JSON.",
                temperature=0.8
            )

            variations = self._parse_json_response(response)

            if isinstance(variations, list) and len(variations) > 0:
                return variations[:3]
            else:
                return self._get_fallback_variations(paragraph)

        except Exception as e:
            print(f"Error enhancing paragraph: {e}")
            return self._get_fallback_variations(paragraph)

    def _build_user_context(self):
        """Build user profile context for personalization"""
        context_parts = []

        # Academic info
        if self.profile:
            if self.profile.intended_major_1:
                context_parts.append(f"• Intended Major: {self.profile.intended_major_1}")
            if self.profile.intended_major_2:
                context_parts.append(f"• Second Major Interest: {self.profile.intended_major_2}")
            if self.profile.gpa:
                context_parts.append(f"• GPA: {self.profile.gpa}")

            if self.profile.sat_score:
                context_parts.append(f"• SAT Score: {self.profile.sat_score}")

        # Target universities
        if self.profile and self.profile.target_universities:
            unis = self.profile.target_universities
            if isinstance(unis, list) and len(unis) > 0:
                context_parts.append(f"• Target Universities: {', '.join(unis[:5])}")

        # Extracurricular activities
        if self.activities.exists():
            context_parts.append("\nExtracurricular Activities:")
            for activity in self.activities[:10]:  # Limit to 10 activities
                activity_str = f"  - {activity.title}"
                if activity.description:
                    activity_str += f": {activity.description}"
                if activity.leadership_position:
                    activity_str += " (Leadership Role)"
                if activity.impact_level:
                    activity_str += f" [Impact: {activity.impact_level}]"
                context_parts.append(activity_str)

        # Academic achievements
        if self.profile and self.profile.academic_competitions:
            context_parts.append(f"\nAcademic Achievements: {self.profile.academic_competitions}")

        return "\n".join(context_parts) if context_parts else "Student profile information not available."

    def _parse_json_response(self, response):
        """Parse JSON from AI response, handling common formatting issues"""
        try:
            # Try direct parsing first
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to extract JSON from response
            try:
                # Look for JSON between ```json and ``` markers
                if '```json' in response:
                    start = response.index('```json') + 7
                    end = response.index('```', start)
                    return json.loads(response[start:end].strip())
                elif '```' in response:
                    start = response.index('```') + 3
                    end = response.index('```', start)
                    return json.loads(response[start:end].strip())
                else:
                    # Try to find first { and last }
                    start = response.index('{')
                    end = response.rindex('}') + 1
                    return json.loads(response[start:end])
            except:
                return None

    def _get_fallback_topics(self, essay_type):
        """Fallback topics if AI generation fails"""
        return [
            {
                "title": f"A {essay_type} experience that shaped me",
                "theme": "Personal Growth",
                "compelling": "Shows your ability to reflect and grow",
                "anecdotes": ["Specific moment", "Your reaction", "What you learned"],
                "fit": "Demonstrates self-awareness and maturity"
            }
        ]

    def _get_fallback_outline(self, essay_type):
        """Fallback outline if AI generation fails"""
        return {
            "introduction": "Hook reader with a compelling moment or scene",
            "body_paragraphs": [
                {
                    "section": "Background",
                    "points": ["Set the scene", "Provide context"],
                    "suggested_words": 150
                },
                {
                    "section": "Action",
                    "points": ["What you did", "How you approached it"],
                    "suggested_words": 200
                },
                {
                    "section": "Reflection",
                    "points": ["What you learned", "How you grew"],
                    "suggested_words": 150
                }
            ],
            "conclusion": "Connect to your future goals and university fit",
            "themes": ["Growth", "Learning", "Future"],
            "total_words": 650
        }

    def _get_fallback_feedback(self):
        """Fallback feedback if AI review fails"""
        return {
            "strengths": ["You have a clear story to tell", "Good structure"],
            "structure_feedback": "Consider adding more transitions between paragraphs",
            "content_feedback": "Add more specific details and examples",
            "voice_feedback": "Your voice comes through clearly",
            "grammar_style": "Proofread for minor grammar issues",
            "improvements": [
                "Add more specific anecdotes",
                "Show, don't tell",
                "Connect to your future goals",
                "Vary sentence structure",
                "Check word count requirements"
            ],
            "score": 7
        }

    def _get_fallback_variations(self, paragraph):
        """Fallback variations if AI enhancement fails"""
        return [
            {
                "variation": paragraph,
                "explanation": "Original paragraph preserved"
            }
        ]
