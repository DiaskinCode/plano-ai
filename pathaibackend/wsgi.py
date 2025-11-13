"""
WSGI config for pathaibackend project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

# Use production settings for Railway deployment, fallback to default for local dev
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pathaibackend.production')

application = get_wsgi_application()
