#!/usr/bin/env bash
# Render build script for Portalyze backend

set -o errexit  # Exit on error

echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "🌐 Installing Playwright browsers..."
playwright install --with-deps chromium

echo "✅ Build complete!"
