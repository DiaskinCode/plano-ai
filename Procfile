# Procfile for Railway deployment
# Defines different process types for your application

# Web server process (main Django application)
web: bash -c "python manage.py migrate --noinput && echo 'Starting Gunicorn on port ${PORT:-8000}...' && gunicorn pathaibackend.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 2 --threads 4 --timeout 120 --log-level debug --capture-output --enable-stdio-inheritance"

# Celery worker process (for background tasks)
# Note: Deploy this as a separate Railway service
worker: celery -A pathaibackend worker --loglevel=info --concurrency=2

# Celery beat process (for scheduled tasks like reminders)
# Note: Deploy this as a separate Railway service
beat: celery -A pathaibackend beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
