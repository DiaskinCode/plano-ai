"""
UniversityResearchAgent: Deep research on specific universities

This agent performs detailed research on specific universities to extract:
- Application deadlines (multiple types)
- Admission requirements (IELTS, GPA, documents)
- Tuition fees
- Program details

Uses Tavily for web search and AI for structured data extraction.
"""

import os
import json
import re
from typing import Dict, Any, Optional, List
from datetime import datetime
from tavily import TavilyClient
from .services import AIService


class UniversityResearchAgent:
    """Agent for deep research on specific universities"""

    def __init__(self):
        self.tavily = TavilyClient(api_key=os.getenv('TAVILY_API_KEY'))
        self.ai_service = AIService()

    def research_university_program(
        self,
        university_name: str,
        program: str,
        intake: str = "2026"
    ) -> Dict[str, Any]:
        """
        Deep research on specific university program

        Args:
            university_name: e.g., "Stanford University", "MIT"
            program: e.g., "MSc Computer Science", "MS CS"
            intake: e.g., "Sep 2026", "Fall 2026"

        Returns:
            Structured university data with deadlines and requirements
        """
        print(f"[UniversityResearch] Researching {university_name} - {program}")

        # Step 1: Search for official admission pages
        search_results = self._search_university_admission(university_name, program, intake)

        if not search_results:
            return self._create_fallback_result(university_name, program)

        # Step 2: Extract structured data using AI
        university_data = self._extract_structured_data(
            university_name,
            program,
            intake,
            search_results
        )

        return university_data

    def _search_university_admission(
        self,
        university_name: str,
        program: str,
        intake: str
    ) -> List[Dict[str, Any]]:
        """Search for university admission information"""
        # Clean program name (remove MSc, MS, etc.)
        program_clean = re.sub(r'\b(MSc|MS|BSc|BS|PhD)\b', '', program, flags=re.IGNORECASE).strip()

        # Build search query
        query = f"{university_name} {program} admission requirements deadlines {intake}"

        try:
            results = self.tavily.search(
                query=query,
                max_results=5,
                search_depth="advanced"
            )

            search_results = results.get('results', [])
            print(f"[UniversityResearch] Found {len(search_results)} search results")

            return search_results

        except Exception as e:
            print(f"[UniversityResearch] Search error: {e}")
            return []

    def _extract_structured_data(
        self,
        university_name: str,
        program: str,
        intake: str,
        search_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Use AI to extract structured data from search results"""

        # Combine search results into context
        context = ""
        primary_url = ""

        for idx, result in enumerate(search_results[:3]):  # Use top 3 results
            if idx == 0:
                primary_url = result.get('url', '')
            context += f"\n\n=== Source {idx + 1}: {result.get('title', '')} ===\n"
            context += f"URL: {result.get('url', '')}\n"
            context += f"Content: {result.get('content', '')}\n"

        # Build AI prompt for extraction
        extraction_prompt = f"""You are extracting structured university admission data for:
UNIVERSITY: {university_name}
PROGRAM: {program}
INTAKE: {intake}

SEARCH RESULTS:
{context}

Extract the following information in JSON format:

1. **Deadlines** (all in YYYY-MM-DD format):
   - application_deadline: Main application deadline
   - transcript_deadline: When transcripts must be submitted
   - recommendation_deadline: When recommendation letters are due
   - test_scores_deadline: When IELTS/GRE/etc scores must be submitted
   - financial_docs_deadline: When financial documents are due

2. **Requirements**:
   - ielts_score: Minimum IELTS score (e.g., "7.0") or null
   - toefl_score: Minimum TOEFL score or null
   - gre_score: GRE requirement or null
   - gpa_min: Minimum GPA (e.g., "3.5") or null
   - documents: Array of required documents (e.g., ["Transcript", "CV", "Statement of Purpose", "2 Recommendation Letters"])

3. **Financial**:
   - tuition_per_year: Annual tuition (e.g., "$55,000", "£32,000")
   - program_duration: Duration (e.g., "2 years", "1 year")

4. **Program Details**:
   - program_url: Direct URL to program page
   - application_portal: URL to application portal if found

IMPORTANT:
- Extract actual dates from the content
- If a deadline is not found, use null
- For documents, list ALL mentioned requirements
- Be precise with numbers (IELTS, GPA, tuition)
- If information is not in the content, return null for that field

Return ONLY valid JSON, no additional text:
{{
  "deadlines": {{...}},
  "requirements": {{...}},
  "financial": {{...}},
  "urls": {{...}}
}}"""

        try:
            response = self.ai_service.call_llm(
                system_prompt="You are a structured data extraction expert.",
                user_prompt=extraction_prompt,
                response_format='json'
            )

            extracted_data = json.loads(response)

            # Build final result
            result = self._build_result(
                university_name,
                program,
                extracted_data,
                primary_url
            )

            return result

        except Exception as e:
            print(f"[UniversityResearch] AI extraction error: {e}")
            return self._create_fallback_result(university_name, program)

    def _build_result(
        self,
        university_name: str,
        program: str,
        extracted_data: Dict[str, Any],
        primary_url: str
    ) -> Dict[str, Any]:
        """Build final structured result"""

        deadlines = extracted_data.get('deadlines', {})
        requirements = extracted_data.get('requirements', {})
        financial = extracted_data.get('financial', {})
        urls = extracted_data.get('urls', {})

        # Build subtitle
        tuition = financial.get('tuition_per_year', 'TBD')
        subtitle = f"{program} - {tuition}/year"

        # Build details string
        details_parts = []

        if deadlines.get('application_deadline'):
            deadline_str = self._format_deadline(deadlines['application_deadline'])
            details_parts.append(f"Deadline: {deadline_str}")

        if requirements.get('ielts_score'):
            details_parts.append(f"IELTS {requirements['ielts_score']}")

        if requirements.get('gpa_min'):
            details_parts.append(f"GPA {requirements['gpa_min']}+")

        details = ' • '.join(details_parts) if details_parts else 'Requirements TBD'

        return {
            'title': university_name,
            'subtitle': subtitle,
            'url': urls.get('program_url') or primary_url,
            'details': details,
            'type': 'university',
            'deadlines': {
                'application_deadline': deadlines.get('application_deadline'),
                'transcript_deadline': deadlines.get('transcript_deadline'),
                'recommendation_deadline': deadlines.get('recommendation_deadline'),
                'test_scores_deadline': deadlines.get('test_scores_deadline'),
                'financial_docs_deadline': deadlines.get('financial_docs_deadline'),
            },
            'requirements': {
                'ielts': requirements.get('ielts_score'),
                'toefl': requirements.get('toefl_score'),
                'gre': requirements.get('gre_score'),
                'gpa': requirements.get('gpa_min'),
                'documents': requirements.get('documents', []),
            },
            'financial': {
                'tuition': financial.get('tuition_per_year'),
                'duration': financial.get('program_duration'),
            },
            'application_portal': urls.get('application_portal'),
        }

    def _format_deadline(self, deadline_str: str) -> str:
        """Format deadline for display (e.g., '2025-12-15' -> 'Dec 15, 2025')"""
        try:
            dt = datetime.strptime(deadline_str, '%Y-%m-%d')
            return dt.strftime('%b %d, %Y')
        except:
            return deadline_str

    def _create_fallback_result(
        self,
        university_name: str,
        program: str
    ) -> Dict[str, Any]:
        """Create fallback result when research fails"""

        # Try to guess/format the URL
        uni_slug = university_name.lower().replace(' ', '').replace('university', '').replace('of', '')
        guessed_url = f"https://www.{uni_slug}.edu/graduate-admissions"

        return {
            'title': university_name,
            'subtitle': f"{program} - TBD",
            'url': guessed_url,
            'details': 'Requirements to be determined - please visit university website',
            'type': 'university',
            'deadlines': {
                'application_deadline': None,
                'transcript_deadline': None,
                'recommendation_deadline': None,
                'test_scores_deadline': None,
                'financial_docs_deadline': None,
            },
            'requirements': {
                'ielts': None,
                'toefl': None,
                'gre': None,
                'gpa': None,
                'documents': ['Transcript', 'CV', 'Statement of Purpose', 'Recommendation Letters'],
            },
            'financial': {
                'tuition': None,
                'duration': None,
            },
            'application_portal': None,
        }
