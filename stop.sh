#!/bin/bash

echo "🛑 Stopping Portalyze..."

# Stop backend (uvicorn)
echo "Stopping backend..."
pkill -f "uvicorn app.main:app"

# Stop frontend (vite)
echo "Stopping frontend..."
pkill -f "vite"

echo "✅ All services stopped!"
