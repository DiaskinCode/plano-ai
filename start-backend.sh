#!/bin/bash
# PathAI Backend Startup Script
# This script ensures the backend starts from the correct directory

echo "🛑 Stopping any existing backend on port 8000..."
lsof -ti:8000 | xargs kill -9 2>/dev/null

echo "🚀 Starting Django backend server..."
cd backend
source venv/bin/activate
python manage.py runserver 0.0.0.0:8000
