# Procfile for Railway deployment
# Defines different process types for your application

# Web server process (main Django application)
# web: python manage.py migrate --noinput && gunicorn pathaibackend.wsgi:application --bind 0.0.0.0:8000 --workers 2 --threads 4 --timeout 120 --log-file - --access-logfile - --error-logfile -
web: bash -c "gunicorn pathaibackend.wsgi --bind 0.0.0.0:${PORT:-8000}"

# Celery worker process (for background tasks)
# Note: Deploy this as a separate Railway service
worker: celery -A pathaibackend worker --loglevel=info --concurrency=2

# Celery beat process (for scheduled tasks like reminders)
# Note: Deploy this as a separate Railway service
beat: celery -A pathaibackend beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
