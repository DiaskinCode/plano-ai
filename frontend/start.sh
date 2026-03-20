#!/bin/bash

# PathAI Development Startup Script
echo "🚀 Starting PathAI Development Environment..."

# Start Backend
echo "📦 Starting Django Backend..."
cd backend
./venv/bin/python3 manage.py runserver 0.0.0.0:8000 &
BACKEND_PID=$!
echo "✓ Backend started (PID: $BACKEND_PID)"

# Start Frontend
echo "📱 Starting Expo Frontend..."
cd frontend
npx expo start --dev-client --clear &
FRONTEND_PID=$!
echo "✓ Frontend started (PID: $FRONTEND_PID)"

echo ""
echo "✅ Both servers started!"
echo "   Backend: http://localhost:8000"
echo "   Frontend: http://localhost:8081"
echo ""
echo "Press Ctrl+C to stop both servers"
echo ""

# Wait for either process
wait $BACKEND_PID $FRONTEND_PID
