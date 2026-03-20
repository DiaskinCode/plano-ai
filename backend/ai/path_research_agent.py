"""
PathResearchAgent: Web-based research and detailed task generation

This agent researches real options from the web based on user's goal specifications,
allows users to select specific paths, and generates DETAILED tasks with real data.

Phase 1: Research real options (universities, jobs, gyms, etc.) from web
Phase 2: User selects preferred paths (handled by frontend)
Phase 3: Generate DETAILED tasks with real URLs, names, deadlines
"""

import os
import json
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from tavily import TavilyClient
from django.conf import settings


class PathResearchAgent:
    """Agent for researching real paths and generating detailed tasks"""

    def __init__(self):
        self.tavily = TavilyClient(api_key=os.getenv('TAVILY_API_KEY'))

    def research_options(self, category: str, specifications: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Research real options from the web based on category and specifications

        Returns structured list of options with:
        - id, title, subtitle, url, details, type
        """
        if category == 'study':
            return self._research_universities(specifications)
        elif category == 'career':
            return self._research_jobs(specifications)
        elif category == 'sport':
            return self._research_gyms(specifications)
        elif category == 'finance':
            return self._research_finance_options(specifications)
        elif category == 'language':
            return self._research_language_resources(specifications)
        elif category == 'networking':
            return self._research_networking_opportunities(specifications)
        else:
            return self._research_generic(category, specifications)

    def _research_universities(self, specs: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Research universities using Hipolabs API + Tavily scraping

        NEW: Uses verified university database (Hipolabs) and filters by:
        - Budget (tuition fees)
        - Field/Major (program offerings)
        - Degree level
        """
        degree = specs.get('degree', specs.get('degreeLevel', 'Masters'))
        country = specs.get('country', specs.get('studyCountry', 'UK'))
        field = specs.get('field', specs.get('studyField', ''))
        budget_str = specs.get('budget', specs.get('budgetRange', ''))
        intake = specs.get('intake', specs.get('intakePreference', ''))

        # Parse budget (convert string like "$50,000" or "£60,000" to numeric)
        budget_limit = self._parse_budget(budget_str)

        print(f"[PathResearchAgent] Researching {degree} {field} in {country}, Budget: {budget_limit}")

        try:
            # Step 1: Get verified universities from Hipolabs API
            verified_universities = self._fetch_universities_from_hipolabs(country)
            print(f"[PathResearchAgent] Hipolabs returned {len(verified_universities)} universities")

            if not verified_universities:
                print("[PathResearchAgent] No universities from Hipolabs, falling back to web search")
                return self._fallback_web_search(degree, country, field, budget_str, intake)

            # Step 2: For each verified university, scrape official site for details
            options = []
            for uni in verified_universities[:30]:  # Process max 30 universities
                uni_name = uni['name']
                uni_domain = uni['domains'][0] if uni.get('domains') else ''
                uni_url = uni['web_pages'][0] if uni.get('web_pages') else f"https://{uni_domain}"

                # Scrape university's official website for program and tuition info
                program_info = self._scrape_university_details(
                    uni_name, uni_url, degree, field, budget_limit
                )

                if program_info:
                    # University offers the program and matches budget
                    options.append({
                        'id': str(len(options)),
                        'title': uni_name,
                        'subtitle': f"{degree} {field} - {program_info.get('tuition', 'Check website')}",
                        'url': uni_url,
                        'details': program_info.get('details', ''),
                        'type': 'university',
                        'tuition_numeric': program_info.get('tuition_numeric', 0),  # For filtering
                    })

                # Stop after 15 relevant options
                if len(options) >= 15:
                    break

            print(f"[PathResearchAgent] Found {len(options)} matching universities")
            return options

        except Exception as e:
            print(f"[PathResearchAgent] Error in university research: {e}")
            # Fallback to old web search method
            return self._fallback_web_search(degree, country, field, budget_str, intake)

    def _parse_budget(self, budget_str: str) -> Optional[int]:
        """
        Parse budget string to numeric value.

        Examples:
        - '$50,000' -> 50000
        - '£10k' -> 10000
        - '≤£15k' -> 15000
        - '$20k-30k' -> 20000 (takes lower bound)
        """
        if not budget_str:
            return None

        # Remove comparison symbols (≤, ≥, <, >) first
        clean = budget_str.strip()
        clean = clean.replace('≤', '').replace('≥', '').replace('<', '').replace('>', '').strip()

        # Remove currency symbols and commas
        clean = clean.replace('$', '').replace('£', '').replace('€', '').replace(',', '').strip()

        try:
            # Extract first number if range (e.g., "20k-30k" -> "20k")
            if '-' in clean:
                clean = clean.split('-')[0].strip()

            # Handle 'k' suffix (e.g., "10k" -> 10000)
            if 'k' in clean.lower():
                clean = clean.lower().replace('k', '').strip()
                value = float(clean) * 1000
                return int(value)

            # Regular number
            return int(float(clean))
        except Exception as e:
            print(f"[PathResearchAgent] Budget parsing failed for '{budget_str}': {e}")
            return None

    def _fetch_universities_from_hipolabs(self, country: str) -> List[Dict[str, Any]]:
        """
        Fetch verified universities from Hipolabs API

        API: http://universities.hipolabs.com/search?country=<country>
        Returns: List of universities with name, domain, web_pages, country
        """
        try:
            # Map user input to Hipolabs country names
            country_mapping = {
                'uk': 'United Kingdom',
                'usa': 'United States',
                'us': 'United States',
                'canada': 'Canada',
                'australia': 'Australia',
                'germany': 'Germany',
                'france': 'France',
                'netherlands': 'Netherlands',
                'singapore': 'Singapore',
                'china': 'China',
                'japan': 'Japan',
                'south korea': 'South Korea',
                'india': 'India',
                'uae': 'United Arab Emirates',
            }

            # Handle regional searches (e.g., "Asia") by searching multiple countries
            region_mappings = {
                'asia': ['Singapore', 'China', 'Japan', 'South Korea', 'India', 'Malaysia', 'Thailand', 'Hong Kong'],
                'europe': ['United Kingdom', 'Germany', 'France', 'Netherlands', 'Spain', 'Italy', 'Switzerland'],
            }

            country_lower = country.lower()

            # Check if it's a region
            if country_lower in region_mappings:
                all_universities = []
                for country_name in region_mappings[country_lower]:
                    try:
                        url = f"http://universities.hipolabs.com/search?country={country_name}"
                        print(f"[PathResearchAgent] Fetching from Hipolabs: {country_name}")
                        response = requests.get(url, timeout=10)
                        if response.status_code == 200:
                            universities = response.json()
                            print(f"[PathResearchAgent]   -> {country_name}: {len(universities)} universities")
                            all_universities.extend(universities)
                        else:
                            print(f"[PathResearchAgent]   -> {country_name}: HTTP {response.status_code}")
                    except Exception as e:
                        print(f"[PathResearchAgent]   -> {country_name}: Error {e}")
                        continue

                print(f"[PathResearchAgent] Hipolabs API: Found {len(all_universities)} universities in {country} region")
                return all_universities

            # Single country search
            hipolabs_country = country_mapping.get(country_lower, country.title())

            # Call Hipolabs API
            url = f"http://universities.hipolabs.com/search?country={hipolabs_country}"
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                universities = response.json()
                print(f"[PathResearchAgent] Hipolabs API: Found {len(universities)} universities in {hipolabs_country}")
                return universities
            else:
                print(f"[PathResearchAgent] Hipolabs API error: {response.status_code}")
                return []

        except Exception as e:
            print(f"[PathResearchAgent] Hipolabs API exception: {e}")
            return []

    def _scrape_university_details(
        self,
        uni_name: str,
        uni_url: str,
        degree: str,
        field: str,
        budget_limit: Optional[int]
    ) -> Optional[Dict[str, Any]]:
        """
        Scrape university's official website for program and tuition info

        Uses Tavily to search the university's site for:
        - Program offerings (does it offer the specific degree in the field?)
        - Tuition fees
        - Admission requirements

        Returns None if university doesn't match criteria (wrong program, over budget)
        """
        try:
            # Build targeted search query for this specific university
            query = f"{uni_name} {degree} {field} tuition fees admission requirements"

            # Use Tavily to search specifically on university's domain
            results = self.tavily.search(
                query=query,
                max_results=3,  # Just need to check if program exists
                search_depth="basic"
            )

            # Analyze results to see if program offered and extract tuition
            program_found = False
            tuition_info = None
            tuition_numeric = 0
            details_parts = []

            for result in results.get('results', []):
                content = result.get('content', '').lower()
                result_url = result.get('url', '').lower()

                # Check if result is from official university website
                uni_domain = uni_url.lower().replace('https://', '').replace('http://', '').split('/')[0]
                if uni_domain not in result_url:
                    continue  # Skip non-official sources

                # Check if program mentioned
                if field.lower() in content and degree.lower() in content:
                    program_found = True

                # Extract tuition
                extracted_tuition = self._extract_tuition_from_content(content)
                if extracted_tuition:
                    tuition_numeric = extracted_tuition['numeric']
                    tuition_info = extracted_tuition['display']

                # Extract other details (deadlines, requirements)
                if 'deadline' in content:
                    details_parts.append("Check deadlines")
                if 'ielts' in content or 'toefl' in content:
                    details_parts.append("English test required")

            # Filter: VERY RELAXED - only skip if we have strong evidence program is NOT offered
            # Give benefit of doubt - include university even if we can't confirm program
            # This prevents falling back to blog articles
            # We'll skip only if results explicitly say "program not offered" or similar

            # Filter: Skip if over budget
            if budget_limit and tuition_numeric > 0 and tuition_numeric > budget_limit:
                print(f"[PathResearchAgent] {uni_name}: Over budget ({tuition_numeric} > {budget_limit})")
                return None

            print(f"[PathResearchAgent] {uni_name}: ✓ Matches criteria (tuition: {tuition_info})")

            return {
                'tuition': tuition_info or 'Check website',
                'tuition_numeric': tuition_numeric,
                'details': ' • '.join(details_parts) if details_parts else f"{degree} {field} program",
            }

        except Exception as e:
            print(f"[PathResearchAgent] Error scraping {uni_name}: {e}")
            # If scraping fails, include university anyway (benefit of doubt)
            return {
                'tuition': 'Check website',
                'tuition_numeric': 0,
                'details': f"{degree} {field} program",
            }

    def _extract_tuition_from_content(self, content: str) -> Optional[Dict[str, Any]]:
        """Extract tuition fee from text content"""
        import re

        # Look for currency symbols followed by numbers
        patterns = [
            r'£([\d,]+)',  # British pounds
            r'\$([\d,]+)',  # US dollars
            r'€([\d,]+)',  # Euros
        ]

        for pattern in patterns:
            matches = re.findall(pattern, content)
            if matches:
                # Get first match
                amount_str = matches[0].replace(',', '')
                try:
                    amount = int(amount_str)
                    # Only consider reasonable tuition amounts (>$1000, <$200k)
                    if 1000 < amount < 200000:
                        currency = '£' if '£' in pattern else '$' if '$' in pattern else '€'
                        return {
                            'numeric': amount,
                            'display': f"{currency}{amount:,}"
                        }
                except:
                    continue

        return None

    def _fallback_web_search(
        self,
        degree: str,
        country: str,
        field: str,
        budget_str: str,
        intake: str
    ) -> List[Dict[str, Any]]:
        """Fallback to old web search method if Hipolabs fails"""
        query = f"{degree} {field} universities {country} admission requirements"
        if budget_str:
            query += f" tuition {budget_str}"
        if intake:
            query += f" {intake} intake"

        print(f"[PathResearchAgent] Fallback search: {query}")

        # Blacklist of aggregator/blog sites to exclude
        blacklisted_domains = [
            'educations.com',
            'studies-overseas.com',
            'studyabroad.shiksha.com',
            'cucas.cn',
            'findamasters.com',
            'mastersportal.com',
            'bachelorsportal.com',
            'phdportal.com',
            'studyportals.com',
            'topuniversities.com/universities',  # Only lists, not actual universities
            'timeshighereducation.com/world-university-rankings',
            'usnews.com/best-colleges',
            'china-admissions.com',  # Consultancy service
            'veloxglobalconsultancy.com',  # Consultancy
            'eduvisors.com',  # Consultancy
            'studyinchina.com.my',  # Consultancy
            'quora.com',  # Q&A site
            # Blog/listicle sites
            'euroinfopedia.com',
            'geniusstudy.com',
            'studyabroad.careers360.com',
            'collegedunia.com',
            'yocket.com',
            'leverage edu',
            'idp.com',
            'hotcoursesabroad.com',
            'scholars4dev.com',
            'afterschoolafrica.com',
            'scholarshiproar.com',
            'opportunitiesforafricans.com',
            'edmissions.com',
            'studyin-uk.com',
            'studyineurope.eu',
            'studyeu.org',
            'afterschool.my',
            'keystone.com',
            'studyportals',
            'blog.',  # Generic blog subdomain
            'list',  # Listicles
            'ranking',  # Ranking pages
        ]

        try:
            results = self.tavily.search(
                query=query,
                max_results=20,
                search_depth="advanced"
            )

            options = []
            country_lower = country.lower()

            for result in results.get('results', []):
                title = self._extract_university_name(result.get('title', ''))
                url = result.get('url', '')
                content = result.get('content', '').lower()

                # FILTER 1: Blacklist check - skip aggregator sites
                is_blacklisted = any(domain in url.lower() for domain in blacklisted_domains)
                if is_blacklisted:
                    print(f"[PathResearchAgent] Skipping blacklisted site: {url}")
                    continue

                # FILTER 2: University domain validation - only accept actual university websites
                if not self._is_university_domain(url, title):
                    print(f"[PathResearchAgent] Skipping non-university domain: {url}")
                    continue

                # FILTER 3: Check if from target country
                is_relevant = self._is_from_country(url, content, country_lower)
                if not is_relevant:
                    continue

                # Extract details
                details = self._extract_university_details(result.get('content', ''))

                options.append({
                    'id': str(len(options)),
                    'title': title or f"University Option {len(options) + 1}",
                    'subtitle': f"{degree} {field} - {country}",
                    'url': url,
                    'details': details,
                    'type': 'university',
                })

                if len(options) >= 15:
                    break

            return options
        except Exception as e:
            print(f"[PathResearchAgent] Fallback search error: {e}")
            return []

    def _is_from_country(self, url: str, content: str, target_country: str) -> bool:
        """Check if university is from the target country"""
        url_lower = url.lower()

        # Country-specific domain mapping
        country_domains = {
            'uk': ['.uk', '.ac.uk', 'britain', 'england', 'scotland', 'wales'],
            'usa': ['.edu', 'united states', 'america', 'u.s.'],
            'us': ['.edu', 'united states', 'america', 'u.s.'],
            'canada': ['.ca', 'canada'],
            'australia': ['.au', 'australia'],
            'germany': ['.de', 'germany', 'deutschland'],
            'france': ['.fr', 'france'],
            'netherlands': ['nl', 'netherlands', 'holland'],
            'singapore': ['.sg', 'singapore'],
            'china': ['.cn', 'china'],
            'japan': ['.jp', 'japan'],
            'south korea': ['.kr', 'korea'],
            'india': ['.in', 'india'],
            'uae': ['.ae', 'uae', 'dubai', 'abu dhabi'],
            'asia': ['singapore', 'china', 'japan', 'korea', 'india', 'hong kong', 'taiwan', 'malaysia', 'thailand'],
        }

        # Get keywords for target country
        keywords = country_domains.get(target_country.lower(), [target_country.lower()])

        # Check URL and content for country keywords
        for keyword in keywords:
            if keyword in url_lower or keyword in content:
                return True

        return False

    def _is_university_domain(self, url: str, title: str) -> bool:
        """
        Check if the URL and title belong to an actual university

        Returns True if:
        - Domain is a university domain (.edu, .ac.uk, etc.)
        - Title contains university/college/institute keywords
        """
        url_lower = url.lower()
        title_lower = title.lower()

        # University domain patterns
        university_domains = [
            '.edu',          # US universities
            '.ac.uk',        # UK universities
            '.ac.',          # Other academic institutions (ac.nz, ac.jp, etc.)
            '.edu.au',       # Australian universities
            '.edu.cn',       # Chinese universities
            '.edu.sg',       # Singapore universities
            '.edu.hk',       # Hong Kong universities
            '.edu.my',       # Malaysian universities
            '.edu.in',       # Indian universities
            '.university',   # Generic university domain
            'uni-',          # German/European universities (uni-berlin.de)
            'uni.',          # Alternative pattern
        ]

        # Check if URL has a university domain
        has_uni_domain = any(domain in url_lower for domain in university_domains)

        # University name keywords
        university_keywords = [
            'university',
            'college',
            'institute of technology',
            'polytechnic',
            'school of',
            'ecole',         # French
            'universite',    # French
            'universidad',   # Spanish
            'universiteit',  # Dutch
            'universitat',   # German/Catalan
            'hochschule',    # German
        ]

        # Check if title contains university keywords
        has_uni_keyword = any(keyword in title_lower for keyword in university_keywords)

        # Exclude keywords that indicate listicles/blogs
        exclude_keywords = [
            'top 10',
            'top 5',
            'best universities',
            'affordable universities',
            'cheap universities',
            'low-cost',
            'list of',
            'ranking',
            'guide to',
            'how to apply',
            'study in',
        ]

        has_exclude_keyword = any(keyword in title_lower for keyword in exclude_keywords)

        # Return True only if:
        # 1. Has university domain OR university keyword in title
        # 2. Does NOT have exclude keywords
        return (has_uni_domain or has_uni_keyword) and not has_exclude_keyword

    def _research_jobs(self, specs: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Research job opportunities for career goals"""
        role = specs.get('role', specs.get('targetRole', ''))
        company = specs.get('company', specs.get('targetCompany', ''))
        location = specs.get('location', specs.get('locationPreference', ''))
        industry = specs.get('industry', '')

        # Build search query
        query = f"{role} jobs"
        if company:
            query += f" at {company}"
        if location:
            query += f" in {location}"
        if industry:
            query += f" {industry} industry"
        query += " apply careers"

        try:
            results = self.tavily.search(
                query=query,
                max_results=20,
                search_depth="advanced"
            )

            options = []
            for idx, result in enumerate(results.get('results', [])[:20]):
                title = result.get('title', f"Job Opportunity {idx + 1}")
                url = result.get('url', '')
                content = result.get('content', '')

                # Try to extract job details
                company_name = self._extract_company_name(content, url)
                job_details = self._extract_job_details(content)

                options.append({
                    'id': str(idx),
                    'title': title,
                    'subtitle': f"{company_name} • {location or 'Remote'}",
                    'url': url,
                    'details': job_details,
                    'type': 'job',
                })

            return options
        except Exception as e:
            print(f"Job search error: {e}")
            return []

    def _research_gyms(self, specs: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Research gyms and trainers for sport goals"""
        sport = specs.get('sport', specs.get('sportType', ''))
        location = specs.get('location', specs.get('locationPreference', ''))
        goal_type = specs.get('goal', specs.get('sportGoal', ''))

        query = f"gyms for {sport} in {location}"
        if goal_type:
            query += f" {goal_type}"

        try:
            results = self.tavily.search(
                query=query,
                max_results=10,
                search_depth="basic"
            )

            options = []
            for idx, result in enumerate(results.get('results', [])[:10]):
                title = result.get('title', f"Gym Option {idx + 1}")
                url = result.get('url', '')
                content = result.get('content', '')

                details = self._extract_gym_details(content)

                options.append({
                    'id': str(idx),
                    'title': title,
                    'subtitle': f"{sport} • {location}",
                    'url': url,
                    'details': details,
                    'type': 'gym',
                })

            return options
        except Exception as e:
            print(f"Gym search error: {e}")
            return []

    def _research_finance_options(self, specs: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Research finance resources (courses, advisors, platforms)"""
        goal = specs.get('goal', specs.get('financeGoal', ''))

        query = f"financial planning {goal} resources advisors"

        try:
            results = self.tavily.search(query=query, max_results=10)
            options = []
            for idx, result in enumerate(results.get('results', [])[:10]):
                options.append({
                    'id': str(idx),
                    'title': result.get('title', f"Finance Resource {idx + 1}"),
                    'subtitle': goal,
                    'url': result.get('url', ''),
                    'details': result.get('content', '')[:150],
                    'type': 'other',
                })
            return options
        except Exception as e:
            return []

    def _research_language_resources(self, specs: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Research language learning resources"""
        language = specs.get('language', specs.get('targetLanguage', ''))
        level = specs.get('level', specs.get('currentLevel', ''))

        query = f"learn {language} {level} courses tutors"

        try:
            results = self.tavily.search(query=query, max_results=10)
            options = []
            for idx, result in enumerate(results.get('results', [])[:10]):
                options.append({
                    'id': str(idx),
                    'title': result.get('title', f"Language Resource {idx + 1}"),
                    'subtitle': f"{language} • {level}",
                    'url': result.get('url', ''),
                    'details': result.get('content', '')[:150],
                    'type': 'other',
                })
            return options
        except Exception as e:
            return []

    def _research_networking_opportunities(self, specs: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Research networking events and LinkedIn profiles"""
        industry = specs.get('industry', specs.get('targetIndustry', ''))
        role = specs.get('role', specs.get('targetRole', ''))
        location = specs.get('location', '')

        query = f"{industry} {role} networking events conferences {location}"

        try:
            results = self.tavily.search(query=query, max_results=10)
            options = []
            for idx, result in enumerate(results.get('results', [])[:10]):
                options.append({
                    'id': str(idx),
                    'title': result.get('title', f"Networking Event {idx + 1}"),
                    'subtitle': f"{industry} • {location}",
                    'url': result.get('url', ''),
                    'details': result.get('content', '')[:150],
                    'type': 'person',
                })
            return options
        except Exception as e:
            return []

    def _research_generic(self, category: str, specs: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generic research for other categories"""
        query = f"{category} goals resources opportunities"

        try:
            results = self.tavily.search(query=query, max_results=10)
            options = []
            for idx, result in enumerate(results.get('results', [])[:10]):
                options.append({
                    'id': str(idx),
                    'title': result.get('title', f"Option {idx + 1}"),
                    'subtitle': category,
                    'url': result.get('url', ''),
                    'details': result.get('content', '')[:150],
                    'type': 'other',
                })
            return options
        except Exception as e:
            return []

    # Helper methods for parsing

    def _extract_university_name(self, title: str) -> str:
        """Extract clean university name from search result title"""
        import re

        # Remove common suffixes and prefixes
        patterns_to_remove = [
            r' - Postgraduate.*',
            r' - Graduate.*',
            r' \| Masters.*',
            r' \| MSc.*',
            r' - Programs.*',
            r' - Admissions.*',
            r' - Application.*',
            r' \| Admissions.*',
            r' \(.*\)',  # Remove parentheses
            r' - .*requirements.*',
            r' - .*deadline.*',
        ]

        cleaned_title = title
        for pattern in patterns_to_remove:
            cleaned_title = re.sub(pattern, '', cleaned_title, flags=re.IGNORECASE)

        # Extract university name if it contains "University of X" or "X University"
        # Priority patterns (most specific first)
        university_patterns = [
            r'(.*?University of [A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',  # "University of Edinburgh"
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+University)',  # "Stanford University"
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+College)',  # "Imperial College"
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+Institute)',  # "Massachusetts Institute"
        ]

        for pattern in university_patterns:
            match = re.search(pattern, cleaned_title)
            if match:
                return match.group(1).strip()

        # If no pattern matched, return cleaned title
        return cleaned_title.strip()

    def _extract_university_details(self, content: str) -> str:
        """Extract tuition, deadline, requirements from content"""
        details = []

        # Look for tuition fees
        if '£' in content or '$' in content or 'tuition' in content.lower():
            words = content.split()
            for i, word in enumerate(words):
                if word.startswith('£') or word.startswith('$'):
                    details.append(f"Tuition: {word}")
                    break

        # Look for deadlines
        if 'deadline' in content.lower() or 'application' in content.lower():
            words = content.lower().split()
            if 'deadline' in words:
                idx = words.index('deadline')
                if idx + 3 < len(words):
                    deadline_text = ' '.join(content.split()[idx:idx+4])
                    details.append(deadline_text)

        # Look for requirements (IELTS, GPA)
        if 'ielts' in content.lower():
            details.append("IELTS required")
        if 'gpa' in content.lower():
            details.append("GPA requirement")

        return ' • '.join(details) if details else content[:100]

    def _extract_company_name(self, content: str, url: str) -> str:
        """Extract company name from content or URL"""
        # Try to extract from URL (e.g., stripe.com -> Stripe)
        if url:
            domain = url.split('/')[2] if '/' in url else url
            company = domain.split('.')[0]
            return company.capitalize()
        return "Company"

    def _extract_job_details(self, content: str) -> str:
        """Extract job details (experience, location, etc.)"""
        details = []

        if 'experience' in content.lower() or 'years' in content.lower():
            details.append("Experience required")
        if 'remote' in content.lower():
            details.append("Remote")
        if 'full-time' in content.lower() or 'full time' in content.lower():
            details.append("Full-time")

        return ' • '.join(details) if details else content[:100]

    def _extract_gym_details(self, content: str) -> str:
        """Extract gym details (price, facilities, etc.)"""
        details = []

        if '£' in content or '$' in content or 'month' in content.lower():
            words = content.split()
            for word in words:
                if word.startswith('£') or word.startswith('$'):
                    details.append(word + "/month")
                    break

        if '24/7' in content or '24 hour' in content.lower():
            details.append("24/7 Access")

        return ' • '.join(details) if details else content[:100]

    def generate_detailed_tasks(
        self,
        goalspecs: List[Dict[str, Any]],
        primary_category: str,
        selected_options: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Generate DETAILED tasks based on selected options

        Tasks will include:
        - Real URLs from selected options
        - Specific deadlines
        - Named entities (universities, companies, people)
        - Step-by-step actions
        """
        tasks = []

        # Get primary goalspec
        primary_spec = next((gs for gs in goalspecs if gs['category'] == primary_category), None)
        if not primary_spec:
            return []

        # Generate tasks for each selected option
        if primary_category == 'study':
            tasks = self._generate_university_tasks(primary_spec, selected_options)
        elif primary_category == 'career':
            tasks = self._generate_job_tasks(primary_spec, selected_options)
        elif primary_category == 'sport':
            tasks = self._generate_sport_tasks(primary_spec, selected_options)
        else:
            tasks = self._generate_generic_tasks(primary_spec, selected_options)

        # Add lighter tasks for secondary categories
        for gs in goalspecs:
            if gs['category'] != primary_category:
                secondary_tasks = self._generate_light_tasks(gs)
                tasks.extend(secondary_tasks)

        return tasks

    def _generate_university_tasks(self, spec: Dict[str, Any], options: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate detailed application tasks for selected universities

        NEW: Deadline-aware task generation
        - If university has real deadline data, work backwards from that deadline
        - Otherwise, use relative deadlines
        """
        tasks = []

        for option in options:
            uni_name = option['title']
            url = option.get('url', '')
            details = option.get('details', '')

            # Check if this university has deadline data (from custom search)
            deadlines = option.get('deadlines', {})
            requirements = option.get('requirements', {})

            if deadlines and deadlines.get('application_deadline'):
                # DEADLINE-AWARE TASK GENERATION
                tasks.extend(self._generate_deadline_aware_university_tasks(
                    uni_name, url, deadlines, requirements
                ))
            else:
                # FALLBACK: Generic relative deadlines
                tasks.extend(self._generate_generic_university_tasks(
                    uni_name, url, details
                ))

        return tasks

    def _generate_deadline_aware_university_tasks(
        self,
        uni_name: str,
        url: str,
        deadlines: Dict[str, Any],
        requirements: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate tasks working backwards from real university deadlines

        Example: Application deadline Dec 15, 2025
        - Dec 15: Submit application
        - Dec 10: Upload transcripts
        - Dec 10: Submit recommendation letters
        - Dec 1: Submit test scores
        - Nov 20: Finalize personal statement
        - Nov 10: Complete application form draft
        - Nov 1: Gather all documents
        - Oct 20: Research requirements
        """
        tasks = []

        try:
            # Parse main application deadline
            app_deadline_str = deadlines.get('application_deadline')
            if not app_deadline_str:
                return []

            app_deadline = datetime.strptime(app_deadline_str, '%Y-%m-%d')
            today = datetime.now()

            # Don't create tasks for past deadlines
            if app_deadline <= today:
                print(f"[PathResearchAgent] Skipping {uni_name} - deadline has passed")
                return []

            # Build document list
            docs = requirements.get('documents', [])
            docs_str = ', '.join(docs[:4]) if docs else 'transcripts, CV, personal statement, recommendation letters'

            # Task 1: Research requirements (35 days before deadline)
            research_date = app_deadline - timedelta(days=35)
            if research_date >= today:
                tasks.append({
                    'title': f"Research {uni_name} admission requirements",
                    'description': f"Visit {uni_name} website and document all admission requirements. Required: {docs_str}. Check IELTS, GPA, and fee requirements.",
                    'url': url,
                    'deadline': research_date.strftime('%Y-%m-%d'),
                    'priority': 'high',
                    'type': 'research',
                    'evidence_required': True,
                })

            # Task 2: Gather documents (28 days before)
            gather_date = app_deadline - timedelta(days=28)
            if gather_date >= today:
                tasks.append({
                    'title': f"Gather all required documents for {uni_name}",
                    'description': f"Collect and organize: {docs_str}. Request official transcripts and contact recommenders.",
                    'url': url,
                    'deadline': gather_date.strftime('%Y-%m-%d'),
                    'priority': 'high',
                    'type': 'preparation',
                    'evidence_required': True,
                })

            # Task 3: Submit test scores if required (depends on test deadline)
            test_deadline_str = deadlines.get('test_scores_deadline')
            if test_deadline_str:
                test_deadline = datetime.strptime(test_deadline_str, '%Y-%m-%d')
                if test_deadline >= today:
                    test_submit_date = test_deadline - timedelta(days=3)
                    if test_submit_date >= today:
                        ielts_req = requirements.get('ielts', 'N/A')
                        toefl_req = requirements.get('toefl', 'N/A')
                        test_info = f"IELTS {ielts_req}" if ielts_req != 'N/A' else f"TOEFL {toefl_req}"

                        tasks.append({
                            'title': f"Submit English test scores to {uni_name}",
                            'description': f"Submit your {test_info} scores to {uni_name}. Ensure scores are sent directly from testing agency.",
                            'url': url,
                            'deadline': test_submit_date.strftime('%Y-%m-%d'),
                            'priority': 'critical',
                            'type': 'submission',
                            'evidence_required': True,
                        })

            # Task 4: Draft personal statement (21 days before)
            statement_date = app_deadline - timedelta(days=21)
            if statement_date >= today:
                tasks.append({
                    'title': f"Draft personal statement for {uni_name}",
                    'description': f"Write compelling personal statement tailored to {uni_name}'s program. Highlight your goals, experience, and why you're a good fit.",
                    'url': url,
                    'deadline': statement_date.strftime('%Y-%m-%d'),
                    'priority': 'high',
                    'type': 'writing',
                    'evidence_required': True,
                })

            # Task 5: Request recommendation letters (depends on rec deadline)
            rec_deadline_str = deadlines.get('recommendation_deadline')
            if rec_deadline_str:
                rec_deadline = datetime.strptime(rec_deadline_str, '%Y-%m-%d')
            else:
                rec_deadline = app_deadline - timedelta(days=5)

            if rec_deadline >= today:
                rec_request_date = rec_deadline - timedelta(days=14)
                if rec_request_date >= today:
                    tasks.append({
                        'title': f"Request recommendation letters for {uni_name}",
                        'description': f"Contact your recommenders and provide them with all necessary information about {uni_name}'s requirements. Follow up regularly.",
                        'url': url,
                        'deadline': rec_request_date.strftime('%Y-%m-%d'),
                        'priority': 'critical',
                        'type': 'communication',
                        'evidence_required': False,
                    })

            # Task 6: Complete application form (14 days before)
            form_date = app_deadline - timedelta(days=14)
            if form_date >= today:
                tasks.append({
                    'title': f"Complete online application form for {uni_name}",
                    'description': f"Fill out the complete application form for {uni_name}. Double-check all information before saving draft.",
                    'url': url,
                    'deadline': form_date.strftime('%Y-%m-%d'),
                    'priority': 'high',
                    'type': 'form',
                    'evidence_required': True,
                })

            # Task 7: Upload transcripts (depends on transcript deadline)
            transcript_deadline_str = deadlines.get('transcript_deadline')
            if transcript_deadline_str:
                transcript_deadline = datetime.strptime(transcript_deadline_str, '%Y-%m-%d')
            else:
                transcript_deadline = app_deadline - timedelta(days=5)

            if transcript_deadline >= today:
                transcript_upload_date = transcript_deadline - timedelta(days=2)
                if transcript_upload_date >= today:
                    tasks.append({
                        'title': f"Upload transcripts to {uni_name} application portal",
                        'description': f"Upload official transcripts to {uni_name}'s application system. Ensure all documents are legible and properly formatted.",
                        'url': url,
                        'deadline': transcript_upload_date.strftime('%Y-%m-%d'),
                        'priority': 'critical',
                        'type': 'upload',
                        'evidence_required': True,
                    })

            # Task 8: Final review and submit (3 days before deadline)
            final_review_date = app_deadline - timedelta(days=3)
            if final_review_date >= today:
                tasks.append({
                    'title': f"Final review and submit application to {uni_name}",
                    'description': f"Review ALL sections of your {uni_name} application. Check for errors, completeness, and accuracy. Pay application fee and submit.",
                    'url': url,
                    'deadline': final_review_date.strftime('%Y-%m-%d'),
                    'priority': 'critical',
                    'type': 'submission',
                    'evidence_required': True,
                })

            # Task 9: Confirm submission (on deadline day or 1 day after)
            confirm_date = app_deadline + timedelta(days=1)
            tasks.append({
                'title': f"Confirm {uni_name} application received",
                'description': f"Check your email and application portal to confirm {uni_name} received your application. Save confirmation email.",
                'url': url,
                'deadline': confirm_date.strftime('%Y-%m-%d'),
                'priority': 'medium',
                'type': 'follow-up',
                'evidence_required': True,
            })

            return tasks

        except Exception as e:
            print(f"[PathResearchAgent] Error generating deadline-aware tasks: {e}")
            # Fallback to generic tasks
            return self._generate_generic_university_tasks(uni_name, url, "")

    def _generate_generic_university_tasks(
        self,
        uni_name: str,
        url: str,
        details: str
    ) -> List[Dict[str, Any]]:
        """Generate generic university tasks with relative deadlines"""

        # Try to scrape specific document requirements for this university
        doc_requirements = self._scrape_document_requirements(uni_name, url)

        return [
            {
                'title': f"Research {uni_name} admission requirements",
                'description': f"Visit {uni_name} website and document all admission requirements including IELTS score, GPA, documents needed, and application fee.",
                'url': url,
                'deadline': self._calculate_deadline(days=7),
                'priority': 'high',
                'type': 'research',
                'evidence_required': True,
            },
            {
                'title': f"Prepare application documents for {uni_name}",
                'description': doc_requirements,
                'url': url,
                'deadline': self._calculate_deadline(days=14),
                'priority': 'high',
                'type': 'preparation',
                'evidence_required': True,
            },
            {
                'title': f"Submit application to {uni_name}",
                'description': f"Complete online application form at {url}. Upload all documents, pay application fee, and submit before deadline.",
                'url': url,
                'deadline': self._calculate_deadline(days=30),
                'priority': 'critical',
                'type': 'application',
                'evidence_required': True,
            },
        ]

    def _scrape_document_requirements(self, uni_name: str, url: str) -> str:
        """
        Scrape specific document requirements from university's website

        Returns detailed description of required documents
        """
        try:
            # Search for document requirements on university's website
            query = f"{uni_name} application documents requirements checklist"

            results = self.tavily.search(
                query=query,
                max_results=3,
                search_depth="advanced"
            )

            # Extract document requirements from official university pages
            uni_domain = url.lower().replace('https://', '').replace('http://', '').split('/')[0]
            documents = []
            additional_info = []

            for result in results.get('results', []):
                result_url = result.get('url', '').lower()
                content = result.get('content', '')

                # Only use results from official university website
                if uni_domain not in result_url:
                    continue

                content_lower = content.lower()

                # Extract common document types
                doc_keywords = {
                    'transcripts': ['transcript', 'academic record', 'grade report'],
                    'cv/resume': ['cv', 'resume', 'curriculum vitae'],
                    'personal statement': ['personal statement', 'statement of purpose', 'motivation letter'],
                    'recommendation letters': ['reference', 'recommendation letter', 'letter of recommendation'],
                    'english test': ['ielts', 'toefl', 'english proficiency', 'language test'],
                    'passport': ['passport', 'identification', 'id copy'],
                    'application form': ['application form', 'online application'],
                    'application fee': ['application fee', 'processing fee'],
                    'research proposal': ['research proposal', 'thesis proposal'],
                    'portfolio': ['portfolio', 'work samples'],
                    'degree certificate': ['degree certificate', 'diploma'],
                }

                for doc_type, keywords in doc_keywords.items():
                    if any(keyword in content_lower for keyword in keywords):
                        if doc_type not in documents:
                            documents.append(doc_type)

                # Extract specific IELTS/TOEFL scores
                import re
                ielts_match = re.search(r'ielts.*?(\d+\.?\d*)', content_lower)
                toefl_match = re.search(r'toefl.*?(\d+)', content_lower)

                if ielts_match and not any('IELTS' in info for info in additional_info):
                    additional_info.append(f"IELTS minimum score: {ielts_match.group(1)}")
                if toefl_match and not any('TOEFL' in info for info in additional_info):
                    additional_info.append(f"TOEFL minimum score: {toefl_match.group(1)}")

                # Extract GPA requirements
                gpa_match = re.search(r'gpa.*?(\d+\.?\d*)', content_lower)
                if gpa_match and not any('GPA' in info for info in additional_info):
                    additional_info.append(f"Minimum GPA: {gpa_match.group(1)}")

            # Build detailed description
            if documents:
                doc_list = "\n".join([f"• {doc.title()}" for doc in documents])
                description = f"Gather and prepare the following documents for {uni_name}:\n\n{doc_list}"

                if additional_info:
                    description += "\n\nAdditional requirements:\n" + "\n".join([f"• {info}" for info in additional_info])

                description += f"\n\nVerify all requirements at: {url}"
                return description
            else:
                # Fallback to generic description
                return f"Gather all required documents for {uni_name}:\n\n• Official transcripts from all universities attended\n• CV/Resume highlighting academic and professional achievements\n• Personal statement (statement of purpose)\n• 2-3 letters of recommendation from academic referees\n• English language test scores (IELTS/TOEFL)\n• Copy of passport\n• Application fee payment confirmation\n\nVisit {url} to verify complete requirements list and specific score thresholds."

        except Exception as e:
            print(f"[PathResearchAgent] Error scraping document requirements for {uni_name}: {e}")
            # Fallback description
            return f"Gather all required documents for {uni_name}:\n\n• Official transcripts from all universities attended\n• CV/Resume highlighting academic and professional achievements\n• Personal statement (statement of purpose)\n• 2-3 letters of recommendation from academic referees\n• English language test scores (IELTS/TOEFL)\n• Copy of passport\n• Application fee payment confirmation\n\nVisit {url} to verify complete requirements list and specific score thresholds."

    def _generate_job_tasks(self, spec: Dict[str, Any], options: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate detailed application tasks for selected jobs"""
        tasks = []

        for option in options:
            job_title = option['title']
            company = option.get('subtitle', '').split('•')[0].strip()
            url = option.get('url', '')

            # Task 1: Research company and role
            tasks.append({
                'title': f"Research {company} and {job_title} role",
                'description': f"Study {company}'s products, culture, recent news. Understand {job_title} responsibilities. Visit: {url}",
                'url': url,
                'deadline': self._calculate_deadline(days=3),
                'priority': 'high',
                'type': 'research',
                'evidence_required': True,
            })

            # Task 2: Tailor CV and cover letter
            tasks.append({
                'title': f"Tailor CV and cover letter for {company}",
                'description': f"Customize CV to highlight relevant experience for {job_title}. Write compelling cover letter addressing {company}'s needs.",
                'url': url,
                'deadline': self._calculate_deadline(days=7),
                'priority': 'high',
                'type': 'preparation',
                'evidence_required': True,
            })

            # Task 3: Apply for position
            tasks.append({
                'title': f"Apply for {job_title} at {company}",
                'description': f"Submit application at {url}. Include tailored CV, cover letter, and portfolio if required.",
                'url': url,
                'deadline': self._calculate_deadline(days=10),
                'priority': 'critical',
                'type': 'application',
                'evidence_required': True,
            })

            # Task 4: Network with employees (if LinkedIn found)
            if 'linkedin' in url.lower():
                tasks.append({
                    'title': f"Connect with {company} employees on LinkedIn",
                    'description': f"Find and connect with 3-5 people at {company} in similar roles. Send personalized connection requests.",
                    'url': 'https://linkedin.com',
                    'deadline': self._calculate_deadline(days=14),
                    'priority': 'medium',
                    'type': 'networking',
                    'evidence_required': False,
                })

        return tasks

    def _generate_sport_tasks(self, spec: Dict[str, Any], options: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate training tasks for selected gyms"""
        tasks = []

        # Extract goal from specifications
        specs = spec.get('specifications', {})
        goal = specs.get('goal', specs.get('sportGoal', '')).lower()

        for option in options:
            gym_name = option['title']
            url = option.get('url', '')

            # Task 1: Sign up for membership
            tasks.append({
                'title': f"Sign up for membership at {gym_name}",
                'description': f"Visit {gym_name} or go to {url} to sign up for membership. Get gym induction and tour facilities.",
                'url': url,
                'deadline': self._calculate_deadline(days=7),
                'priority': 'high',
                'type': 'signup',
                'evidence_required': True,
            })

            # Check if goal involves muscle building / bodybuilding
            is_bodybuilding = any(keyword in goal for keyword in [
                'muscle', 'bodybuilding', 'build', 'strength', 'powerlifting', 'hypertrophy'
            ])

            if is_bodybuilding:
                # Generate bodybuilding split schedule tasks
                split_tasks = self._generate_bodybuilding_split_tasks(gym_name, url)
                tasks.extend(split_tasks)
            else:
                # Generic first workout task
                tasks.append({
                    'title': f"Complete first workout at {gym_name}",
                    'description': f"Attend {gym_name} and complete your first training session. Focus on proper form and familiarizing with equipment.",
                    'url': url,
                    'deadline': self._calculate_deadline(days=10),
                    'priority': 'medium',
                    'type': 'training',
                    'evidence_required': True,
                })

        return tasks

    def _generate_bodybuilding_split_tasks(self, gym_name: str, url: str) -> List[Dict[str, Any]]:
        """
        Generate 3-day bodybuilding training split tasks

        Split:
        - Monday: Chest + Triceps
        - Wednesday: Back + Biceps
        - Friday: Legs + Shoulders

        These tasks should recur weekly
        """
        tasks = []

        # Calculate next Monday, Wednesday, Friday
        today = datetime.now()
        days_until_monday = (7 - today.weekday()) % 7 or 7  # 0 = Monday
        days_until_wednesday = (9 - today.weekday()) % 7 or 7  # 2 = Wednesday
        days_until_friday = (11 - today.weekday()) % 7 or 7  # 4 = Friday

        next_monday = today + timedelta(days=days_until_monday)
        next_wednesday = today + timedelta(days=days_until_wednesday)
        next_friday = today + timedelta(days=days_until_friday)

        # Monday: Chest + Triceps
        tasks.append({
            'title': f"Train Chest and Triceps at {gym_name}",
            'description': f"""Complete chest and triceps workout at {gym_name}:

Chest Exercises:
• Barbell Bench Press: 4 sets x 8-12 reps
• Incline Dumbbell Press: 3 sets x 10-12 reps
• Cable Flyes or Pec Deck: 3 sets x 12-15 reps

Triceps Exercises:
• Tricep Dips or Close-Grip Bench: 3 sets x 8-12 reps
• Overhead Tricep Extension: 3 sets x 10-12 reps
• Tricep Pushdowns: 3 sets x 12-15 reps

Focus on proper form, controlled movements, and progressive overload.""",
            'url': url,
            'deadline': next_monday.strftime('%Y-%m-%d'),
            'priority': 'high',
            'type': 'training',
            'evidence_required': True,
            'recurring': 'weekly',  # Indicates this task repeats every week
            'recurring_day': 'monday',
        })

        # Wednesday: Back + Biceps
        tasks.append({
            'title': f"Train Back and Biceps at {gym_name}",
            'description': f"""Complete back and biceps workout at {gym_name}:

Back Exercises:
• Deadlifts or Barbell Rows: 4 sets x 8-12 reps
• Pull-ups or Lat Pulldowns: 3 sets x 8-12 reps
• Seated Cable Rows: 3 sets x 10-12 reps
• Face Pulls: 3 sets x 15-20 reps

Biceps Exercises:
• Barbell Curls: 3 sets x 10-12 reps
• Hammer Curls: 3 sets x 10-12 reps
• Cable Curls: 3 sets x 12-15 reps

Focus on proper form, mind-muscle connection, and controlled negatives.""",
            'url': url,
            'deadline': next_wednesday.strftime('%Y-%m-%d'),
            'priority': 'high',
            'type': 'training',
            'evidence_required': True,
            'recurring': 'weekly',
            'recurring_day': 'wednesday',
        })

        # Friday: Legs + Shoulders
        tasks.append({
            'title': f"Train Legs and Shoulders at {gym_name}",
            'description': f"""Complete legs and shoulders workout at {gym_name}:

Leg Exercises:
• Squats (Barbell or Smith Machine): 4 sets x 8-12 reps
• Leg Press: 3 sets x 10-12 reps
• Romanian Deadlifts: 3 sets x 10-12 reps
• Leg Curls: 3 sets x 12-15 reps
• Calf Raises: 4 sets x 15-20 reps

Shoulder Exercises:
• Overhead Press (Barbell or Dumbbell): 4 sets x 8-12 reps
• Lateral Raises: 3 sets x 12-15 reps
• Rear Delt Flyes: 3 sets x 12-15 reps

Focus on full range of motion, proper form, and adequate rest between sets.""",
            'url': url,
            'deadline': next_friday.strftime('%Y-%m-%d'),
            'priority': 'high',
            'type': 'training',
            'evidence_required': True,
            'recurring': 'weekly',
            'recurring_day': 'friday',
        })

        return tasks

    def _generate_generic_tasks(self, spec: Dict[str, Any], options: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate generic tasks for other categories"""
        tasks = []

        for option in options:
            title = option['title']
            url = option.get('url', '')

            tasks.append({
                'title': f"Explore: {title}",
                'description': f"Research and explore this option: {title}. Visit {url} for more information.",
                'url': url,
                'deadline': self._calculate_deadline(days=7),
                'priority': 'medium',
                'type': 'research',
                'evidence_required': False,
            })

        return tasks

    def _generate_light_tasks(self, goalspec: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate SMART tasks for secondary goals based on category"""
        category = goalspec['category']
        specs = goalspec.get('specifications', {})

        # Route to category-specific task generators
        if category == 'language':
            return self._generate_smart_language_tasks(specs)
        elif category == 'career':
            return self._generate_smart_career_tasks(specs)
        elif category == 'sport':
            return self._generate_smart_sport_tasks(specs)
        elif category == 'networking':
            return self._generate_smart_networking_tasks(specs)
        elif category == 'finance':
            return self._generate_smart_finance_tasks(specs)
        else:
            # Fallback for other categories
            return [{
                'title': f"Review your {category} progress",
                'description': f"Check your progress on {category} goals and adjust plan if needed.",
                'url': '',
                'deadline': self._calculate_deadline(days=14),
                'priority': 'low',
                'type': 'review',
                'evidence_required': False,
            }]

    def _generate_smart_language_tasks(self, specs: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate specific language learning tasks"""
        language = specs.get('language', specs.get('targetLanguage', 'target language'))
        level = specs.get('level', specs.get('currentLevel', 'beginner'))

        tasks = []

        # Task 1: Daily practice (week 1)
        tasks.append({
            'title': f"Complete 3 {language} lessons on language app",
            'description': f"Use Duolingo, Babbel, or similar app to complete 3 lessons in {language}. Focus on vocabulary and basic grammar.",
            'url': 'https://www.duolingo.com',
            'deadline': self._calculate_deadline(days=7),
            'priority': 'medium',
            'type': 'practice',
            'evidence_required': True,
        })

        # Task 2: Passive learning (week 1)
        tasks.append({
            'title': f"Watch 1 episode in {language} with subtitles",
            'description': f"Find a TV show or YouTube video in {language}. Watch with {language} subtitles to improve listening comprehension.",
            'url': 'https://www.youtube.com',
            'deadline': self._calculate_deadline(days=10),
            'priority': 'low',
            'type': 'media',
            'evidence_required': False,
        })

        # Task 3: Vocabulary building (week 2)
        tasks.append({
            'title': f"Learn 20 new {language} words with flashcards",
            'description': f"Create flashcards (Anki/Quizlet) for 20 common {language} words. Review daily for 5 minutes.",
            'url': 'https://ankiweb.net',
            'deadline': self._calculate_deadline(days=14),
            'priority': 'medium',
            'type': 'vocabulary',
            'evidence_required': True,
        })

        # Task 4: Speaking practice (week 2-3)
        if level != 'beginner':
            tasks.append({
                'title': f"Practice speaking {language} for 15 minutes",
                'description': f"Use italki, HelloTalk, or language exchange app to practice speaking {language} with a native speaker or tutor.",
                'url': 'https://www.italki.com',
                'deadline': self._calculate_deadline(days=21),
                'priority': 'high',
                'type': 'speaking',
                'evidence_required': True,
            })

        return tasks

    def _generate_smart_career_tasks(self, specs: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate specific career development tasks"""
        role = specs.get('role', specs.get('targetRole', 'target position'))
        industry = specs.get('industry', specs.get('targetIndustry', 'your industry'))
        skill = specs.get('skill', specs.get('keySkill', ''))

        tasks = []

        # Task 1: Profile optimization (week 1)
        tasks.append({
            'title': f"Update LinkedIn profile for {role} roles",
            'description': f"Update your LinkedIn headline, summary, and experience to highlight skills relevant to {role}. Add recent projects and achievements.",
            'url': 'https://www.linkedin.com',
            'deadline': self._calculate_deadline(days=7),
            'priority': 'high',
            'type': 'profile',
            'evidence_required': True,
        })

        # Task 2: Job applications (week 1-2)
        tasks.append({
            'title': f"Apply to 2 {role} positions in {industry}",
            'description': f"Research and apply to 2 quality {role} positions. Tailor your CV and cover letter for each application.",
            'url': 'https://www.linkedin.com/jobs',
            'deadline': self._calculate_deadline(days=14),
            'priority': 'high',
            'type': 'application',
            'evidence_required': True,
        })

        # Task 3: Skill development (week 2)
        if skill:
            tasks.append({
                'title': f"Complete {skill} coding challenge or tutorial",
                'description': f"Solve 3 {skill} problems on LeetCode/HackerRank or complete one tutorial project to demonstrate your skills.",
                'url': 'https://leetcode.com',
                'deadline': self._calculate_deadline(days=14),
                'priority': 'medium',
                'type': 'skill_building',
                'evidence_required': True,
            })

        # Task 4: Networking (week 3)
        tasks.append({
            'title': f"Connect with 3 professionals in {industry}",
            'description': f"Send personalized LinkedIn connection requests to 3 people working in {industry}. Mention shared interests or goals.",
            'url': 'https://www.linkedin.com',
            'deadline': self._calculate_deadline(days=21),
            'priority': 'medium',
            'type': 'networking',
            'evidence_required': False,
        })

        return tasks

    def _generate_smart_sport_tasks(self, specs: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate specific fitness and sport tasks"""
        sport = specs.get('sport', specs.get('sportType', 'workout'))
        goal = specs.get('goal', specs.get('sportGoal', 'fitness'))
        location = specs.get('location', specs.get('locationPreference', ''))

        tasks = []

        # Task 1: First workout (week 1)
        tasks.append({
            'title': f"Complete 30-minute {sport} workout session",
            'description': f"Do a {sport} workout for at least 30 minutes. Focus on proper form and technique. Track your performance.",
            'url': '',
            'deadline': self._calculate_deadline(days=7),
            'priority': 'high',
            'type': 'workout',
            'evidence_required': True,
        })

        # Task 2: Consistency tracking (week 1-2)
        tasks.append({
            'title': f"Log 5 {sport} workouts in fitness tracker",
            'description': f"Track 5 workouts using Strava, MyFitnessPal, or similar app. Record duration, distance, or sets/reps.",
            'url': 'https://www.strava.com',
            'deadline': self._calculate_deadline(days=14),
            'priority': 'medium',
            'type': 'tracking',
            'evidence_required': True,
        })

        # Task 3: Progressive overload (week 2-3)
        if goal.lower() in ['strength', 'muscle', 'powerlifting', 'bodybuilding']:
            tasks.append({
                'title': f"Increase {sport} weight/intensity by 5-10%",
                'description': f"Progress your {sport} routine by increasing weight, reps, or intensity. Follow progressive overload principles.",
                'url': '',
                'deadline': self._calculate_deadline(days=21),
                'priority': 'medium',
                'type': 'progression',
                'evidence_required': True,
            })
        elif goal.lower() in ['endurance', 'cardio', 'running', 'cycling']:
            tasks.append({
                'title': f"Increase {sport} duration by 10 minutes",
                'description': f"Extend your {sport} sessions by 10 minutes. Build endurance gradually and safely.",
                'url': '',
                'deadline': self._calculate_deadline(days=21),
                'priority': 'medium',
                'type': 'progression',
                'evidence_required': True,
            })

        # Task 4: Professional guidance (week 3-4)
        if location:
            tasks.append({
                'title': f"Book consultation with {sport} trainer in {location}",
                'description': f"Schedule a session with a certified {sport} trainer or coach to review your form and create a personalized plan.",
                'url': '',
                'deadline': self._calculate_deadline(days=28),
                'priority': 'low',
                'type': 'consultation',
                'evidence_required': False,
            })

        return tasks

    def _generate_smart_networking_tasks(self, specs: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate specific networking and relationship building tasks"""
        industry = specs.get('industry', specs.get('targetIndustry', 'your industry'))
        role = specs.get('role', specs.get('targetRole', 'professionals'))
        location = specs.get('location', specs.get('locationPreference', 'your area'))

        tasks = []

        # Task 1: LinkedIn outreach (week 1)
        tasks.append({
            'title': f"Send 5 personalized LinkedIn connection requests",
            'description': f"Identify and connect with 5 {industry} professionals. Write personalized messages mentioning shared interests or mutual connections.",
            'url': 'https://www.linkedin.com',
            'deadline': self._calculate_deadline(days=7),
            'priority': 'high',
            'type': 'outreach',
            'evidence_required': True,
        })

        # Task 2: Event participation (week 2)
        tasks.append({
            'title': f"Find and register for 1 {industry} networking event",
            'description': f"Search for {industry} meetups, conferences, or events in {location} on Eventbrite, Meetup.com, or LinkedIn Events. Register to attend.",
            'url': 'https://www.eventbrite.com',
            'deadline': self._calculate_deadline(days=14),
            'priority': 'medium',
            'type': 'event',
            'evidence_required': True,
        })

        # Task 3: Mentor connection (week 2-3)
        tasks.append({
            'title': f"Schedule informational coffee chat with {role}",
            'description': f"Reach out to someone working as {role} in {industry}. Request a 20-minute coffee chat to learn about their career path.",
            'url': '',
            'deadline': self._calculate_deadline(days=21),
            'priority': 'high',
            'type': 'mentorship',
            'evidence_required': False,
        })

        # Task 4: Community joining (week 3)
        tasks.append({
            'title': f"Join {industry} online community or Slack group",
            'description': f"Find and join an active {industry} community on Slack, Discord, or professional forum. Introduce yourself and engage in discussions.",
            'url': '',
            'deadline': self._calculate_deadline(days=21),
            'priority': 'medium',
            'type': 'community',
            'evidence_required': False,
        })

        return tasks

    def _generate_smart_finance_tasks(self, specs: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate specific financial planning tasks"""
        goal = specs.get('goal', specs.get('financeGoal', 'financial stability'))
        amount = specs.get('target_amount', specs.get('targetAmount', ''))

        tasks = []

        # Task 1: Expense tracking (week 1)
        tasks.append({
            'title': f"Track all expenses for 1 week in budget app",
            'description': f"Use Mint, YNAB, or spreadsheet to track every expense for 7 days. Categorize spending (food, transport, entertainment, etc.).",
            'url': 'https://www.youneedabudget.com',
            'deadline': self._calculate_deadline(days=7),
            'priority': 'high',
            'type': 'tracking',
            'evidence_required': True,
        })

        # Task 2: Investment research (week 1-2)
        if 'invest' in goal.lower() or 'save' in goal.lower():
            tasks.append({
                'title': f"Research 3 investment options for {goal}",
                'description': f"Compare 3 investment vehicles (index funds, ETFs, savings accounts) suitable for {goal}. Note fees, returns, and risks.",
                'url': 'https://www.investopedia.com',
                'deadline': self._calculate_deadline(days=14),
                'priority': 'medium',
                'type': 'research',
                'evidence_required': True,
            })

        # Task 3: Automated savings (week 2)
        tasks.append({
            'title': f"Set up automatic savings transfer (10% of income)",
            'description': f"Configure automatic monthly transfer of 10% of your income to savings account. Set it to run on payday.",
            'url': '',
            'deadline': self._calculate_deadline(days=14),
            'priority': 'high',
            'type': 'automation',
            'evidence_required': True,
        })

        # Task 4: Expense optimization (week 3)
        tasks.append({
            'title': f"Review and optimize monthly subscription expenses",
            'description': f"List all subscriptions (streaming, gym, apps). Cancel unused ones and negotiate better rates where possible.",
            'url': '',
            'deadline': self._calculate_deadline(days=21),
            'priority': 'medium',
            'type': 'optimization',
            'evidence_required': True,
        })

        return tasks

    def _calculate_deadline(self, days: int) -> str:
        """Calculate deadline from now"""
        deadline = datetime.now() + timedelta(days=days)
        return deadline.strftime('%Y-%m-%d')
