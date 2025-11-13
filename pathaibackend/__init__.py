"""
PathAI Backend Init
Loads Celery app for async task processing
"""

# Import Celery app so it's loaded when Django starts
from .celery import app as celery_app

__all__ = ('celery_app',)
