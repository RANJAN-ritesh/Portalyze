#!/bin/bash

# Portalyze Frontend Deployment Script
# This script builds and prepares the frontend for production deployment

set -e

echo "🚀 Portalyze Production Deployment"
echo "=================================="
echo ""

# Navigate to frontend directory
cd "$(dirname "$0")/frontend"

echo "📦 Installing dependencies..."
npm install

echo ""
echo "🔨 Building for production..."
npm run build

echo ""
echo "✅ Build complete!"
echo ""
echo "📊 Build output:"
ls -lh dist/

echo ""
echo "=================================="
echo "✨ Frontend is ready for deployment!"
echo ""
echo "Next steps:"
echo ""
echo "Option 1 - Automatic (if Git connected):"
echo "  git add ."
echo "  git commit -m 'fix: Production deployment ready'"
echo "  git push origin main"
echo ""
echo "Option 2 - Manual Drag & Drop:"
echo "  1. Go to https://app.netlify.com/drop"
echo "  2. Drag the 'frontend/dist' folder"
echo ""
echo "Option 3 - CLI:"
echo "  cd frontend"
echo "  netlify deploy --prod --dir=dist"
echo ""
echo "⚠️  IMPORTANT: Update Render environment variables:"
echo "  ALLOWED_ORIGINS=https://portalyze.netlify.app"
echo "  ENVIRONMENT=production"
echo ""
echo "📖 Full guide: See PRODUCTION_DEPLOYMENT.md"
echo "=================================="
