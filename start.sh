#!/bin/bash

echo "🚀 Starting Portalyze 2.0..."

# Start backend
echo "Starting backend..."
cd backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > ../backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend started (PID: $BACKEND_PID)"
cd ..

# Wait for backend to be ready
echo "Waiting for backend to start..."
sleep 5

# Start frontend
echo "Starting frontend..."
cd frontend
npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
echo "Frontend started (PID: $FRONTEND_PID)"
cd ..

echo ""
echo "✅ Portalyze is running!"
echo "📝 Backend: http://localhost:8000"
echo "🌐 Frontend: http://localhost:5173"
echo ""
echo "📊 Logs:"
echo "  - Backend: tail -f backend.log"
echo "  - Frontend: tail -f frontend.log"
echo ""
echo "To stop: ./stop.sh"
