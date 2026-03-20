"""
AI Services for PathAI platform.

This module provides AI-powered services for:
- University suggestions and matching
- Personalized plan generation
- Academic profile analysis
"""

from .university_database import (
    UNIVERSITY_DATABASE,
    UNIVERSITY_ALIASES,
    get_university_data,
    search_universities,
    categorize_student_profile,
)

from .university_suggester import (
    UniversitySuggester,
    get_quick_suggestions,
)

from .plan_generator import (
    PlanGenerator,
    generate_application_plan,
)

__all__ = [
    # University Database
    'UNIVERSITY_DATABASE',
    'UNIVERSITY_ALIASES',
    'get_university_data',
    'search_universities',
    'categorize_student_profile',
    # University Suggester
    'UniversitySuggester',
    'get_quick_suggestions',
    # Plan Generator
    'PlanGenerator',
    'generate_application_plan',
]

# Import AIService from parent services.py for backward compatibility
# This is needed for existing code that imports from ai.services
import sys
import importlib

# Get the parent ai package
parent_package = sys.modules.get('ai')
if parent_package is None:
    parent_package = importlib.import_module('ai')

# Import services module from parent ai package
try:
    ai_services_module = importlib.import_module('ai.services')
    if hasattr(ai_services_module, 'AIService'):
        AIService = ai_services_module.AIService
        __all__.append('AIService')
except (ImportError, AttributeError):
    pass
