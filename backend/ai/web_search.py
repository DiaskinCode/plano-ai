"""
Web Search Service using Tavily API
Provides intelligent web search capabilities for task enrichment
"""
import os
from typing import List, Dict, Optional
from django.conf import settings


class WebSearchService:
    """Web search service for finding real-world information"""

    def __init__(self):
        """Initialize Tavily client"""
        try:
            from tavily import TavilyClient
            api_key = settings.TAVILY_API_KEY

            if not api_key:
                print("WARNING: TAVILY_API_KEY not set. Web search will be disabled.")
                self.client = None
            else:
                self.client = TavilyClient(api_key=api_key)
        except ImportError:
            print("WARNING: tavily-python not installed. Run: pip install tavily-python")
            self.client = None

    def is_available(self) -> bool:
        """Check if web search is available"""
        return self.client is not None

    def search_linkedin_profiles(
        self,
        query: str,
        industry: str = "",
        location: str = "",
        max_results: int = 5
    ) -> List[Dict]:
        """
        Search for relevant professionals on LinkedIn

        Args:
            query: Search query (e.g., "fintech founders")
            industry: Industry filter (e.g., "financial technology")
            location: Location filter (e.g., "San Francisco")
            max_results: Maximum number of results

        Returns:
            List of dicts with profile information
        """
        if not self.is_available():
            return []

        try:
            # Build search query optimized for LinkedIn
            search_query = f"{query} {industry} {location} site:linkedin.com/in".strip()

            response = self.client.search(
                query=search_query,
                max_results=max_results,
                search_depth="basic"
            )

            # Parse results
            profiles = []
            for result in response.get('results', []):
                profiles.append({
                    'name': self._extract_name_from_linkedin_title(result.get('title', '')),
                    'url': result.get('url', ''),
                    'title': result.get('title', ''),
                    'snippet': result.get('content', ''),
                    'source': 'linkedin'
                })

            return profiles
        except Exception as e:
            print(f"LinkedIn search error: {e}")
            return []

    def search_events(
        self,
        industry: str,
        location: str = "",
        timeframe: str = "2025",
        max_results: int = 5
    ) -> List[Dict]:
        """
        Search for upcoming industry events

        Args:
            industry: Industry/topic (e.g., "fintech", "AI", "startup")
            location: Location (e.g., "San Francisco", "New York")
            timeframe: Time period (e.g., "2025", "Q1 2025")
            max_results: Maximum number of results

        Returns:
            List of dicts with event information
        """
        if not self.is_available():
            return []

        try:
            # Build search query for events
            search_query = f"{industry} events {location} {timeframe} conference meetup"

            response = self.client.search(
                query=search_query,
                max_results=max_results,
                search_depth="advanced"  # More comprehensive for events
            )

            # Parse results
            events = []
            for result in response.get('results', []):
                events.append({
                    'name': result.get('title', ''),
                    'url': result.get('url', ''),
                    'description': result.get('content', ''),
                    'snippet': result.get('content', ''),
                    'source': self._identify_event_platform(result.get('url', ''))
                })

            return events
        except Exception as e:
            print(f"Events search error: {e}")
            return []

    def search_courses(
        self,
        topic: str,
        level: str = "intermediate",
        platform: Optional[str] = None,
        max_results: int = 5
    ) -> List[Dict]:
        """
        Search for online courses

        Args:
            topic: Course topic (e.g., "fintech", "product management")
            level: Skill level (beginner, intermediate, advanced)
            platform: Specific platform (coursera, udemy, edx) or None for all
            max_results: Maximum number of results

        Returns:
            List of dicts with course information
        """
        if not self.is_available():
            return []

        try:
            # Build search query for courses
            if platform:
                search_query = f"{topic} {level} course site:{platform}.com"
            else:
                platforms = "site:coursera.org OR site:udemy.com OR site:edx.org OR site:linkedin.com/learning"
                search_query = f"{topic} {level} course {platforms}"

            response = self.client.search(
                query=search_query,
                max_results=max_results,
                search_depth="basic"
            )

            # Parse results
            courses = []
            for result in response.get('results', []):
                courses.append({
                    'name': result.get('title', ''),
                    'url': result.get('url', ''),
                    'description': result.get('content', ''),
                    'platform': self._identify_course_platform(result.get('url', '')),
                    'snippet': result.get('content', '')
                })

            return courses
        except Exception as e:
            print(f"Courses search error: {e}")
            return []

    def search_general(
        self,
        query: str,
        max_results: int = 5,
        search_depth: str = "basic"
    ) -> List[Dict]:
        """
        General web search

        Args:
            query: Search query
            max_results: Maximum number of results
            search_depth: "basic" or "advanced"

        Returns:
            List of dicts with search results
        """
        if not self.is_available():
            return []

        try:
            response = self.client.search(
                query=query,
                max_results=max_results,
                search_depth=search_depth
            )

            results = []
            for result in response.get('results', []):
                results.append({
                    'title': result.get('title', ''),
                    'url': result.get('url', ''),
                    'content': result.get('content', ''),
                    'snippet': result.get('content', '')
                })

            return results
        except Exception as e:
            print(f"General search error: {e}")
            return []

    def _extract_name_from_linkedin_title(self, title: str) -> str:
        """Extract person's name from LinkedIn page title"""
        # LinkedIn titles are usually in format: "Name - Title at Company | LinkedIn"
        if ' - ' in title:
            return title.split(' - ')[0].strip()
        elif ' | ' in title:
            return title.split(' | ')[0].strip()
        return title.strip()

    def _identify_event_platform(self, url: str) -> str:
        """Identify event platform from URL"""
        url_lower = url.lower()
        if 'eventbrite' in url_lower:
            return 'Eventbrite'
        elif 'meetup' in url_lower:
            return 'Meetup'
        elif 'luma' in url_lower:
            return 'Luma'
        elif 'linkedin.com/events' in url_lower:
            return 'LinkedIn Events'
        return 'Other'

    def _identify_course_platform(self, url: str) -> str:
        """Identify course platform from URL"""
        url_lower = url.lower()
        if 'coursera' in url_lower:
            return 'Coursera'
        elif 'udemy' in url_lower:
            return 'Udemy'
        elif 'edx' in url_lower:
            return 'edX'
        elif 'linkedin.com/learning' in url_lower:
            return 'LinkedIn Learning'
        elif 'udacity' in url_lower:
            return 'Udacity'
        elif 'pluralsight' in url_lower:
            return 'Pluralsight'
        return 'Other'


# Singleton instance
web_search_service = WebSearchService()
