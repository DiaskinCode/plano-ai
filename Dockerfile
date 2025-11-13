# Dockerfile for PathAI Django Backend on Railway
# Python 3.11 base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DJANGO_SETTINGS_MODULE=pathaibackend.production

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy project files
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput || true

# Expose port (Railway will set PORT env variable)
EXPOSE 8000

# Run migrations and start server
CMD ["sh", "-c", "python manage.py migrate --noinput; gunicorn pathaibackend.wsgi:application --bind 0.0.0.0:8000 --workers 2 --threads 4 --timeout 120 --log-level debug"]
