#!/bin/bash

# Local deployment script - bygger allt lokalt och pushar till GitHub
set -e

echo "🚀 Starting local deployment build..."

# Kontrollera att vi är i rätt katalog
if [ ! -f "package.json" ] && [ ! -d "frontend" ] && [ ! -d "backend" ]; then
    echo "❌ Kör från projektets root-katalog (där frontend/ och backend/ finns)"
    exit 1
fi

# Stash local changes if any
echo "💾 Stashing any uncommitted changes..."
git stash push -m "Auto-stash before deployment $(date)" || true

# Pull latest changes
echo "⬇️ Pulling latest changes from GitHub..."
git pull origin main

# Build frontend
echo "🔨 Building frontend..."
cd frontend
npm install
npm run build
cd ..

# Build backend Docker image
echo "🔨 Building backend Docker image..."
docker build -t cold-storage-backend ./backend

# Save backend image to backend folder
echo "💾 Saving backend image to backend/..."
docker save cold-storage-backend | gzip > backend/backend-image.tar.gz

# Build frontend Docker image
echo "🔨 Building frontend Docker image..."
docker build -f frontend/Dockerfile.prod -t cold-storage-frontend ./frontend

# Save frontend image to frontend folder  
echo "💾 Saving frontend image to frontend/..."
docker save cold-storage-frontend | gzip > frontend/frontend-image.tar.gz

# Add built files to git
echo "📦 Adding built files to git..."
git add backend/backend-image.tar.gz
git add frontend/frontend-image.tar.gz
git add .

# Check if there are changes to commit
if git diff --staged --quiet; then
    echo "ℹ️ No changes to commit"
else
    # Commit with timestamp
    TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")
    echo "💾 Committing build at $TIMESTAMP..."
    git commit -m "🚀 Deploy build - $TIMESTAMP

- Frontend built with latest changes
- Backend Docker image: $(docker images cold-storage-backend --format 'table {{.Size}}' | tail -1)
- Frontend Docker image: $(docker images cold-storage-frontend --format 'table {{.Size}}' | tail -1)
- Ready for server deployment"
fi

# Push to GitHub
echo "⬆️ Pushing to GitHub..."
git push origin main

# Clean up local images to save space
echo "🧹 Cleaning up local Docker images..."
docker rmi cold-storage-backend cold-storage-frontend || true

echo ""
echo "✅ Local deployment complete!"
echo "🌐 Built files and Docker images pushed to GitHub"
echo "🔧 Now run './deploy-server.sh' on the server to deploy"
echo ""
echo "📋 Image sizes committed:"
echo "   Backend: $(ls -lh backend/backend-image.tar.gz | awk '{print $5}')"
echo "   Frontend: $(ls -lh frontend/frontend-image.tar.gz | awk '{print $5}')"
echo ""
echo "📋 Next steps:"
echo "   1. SSH to server: ssh your-server"
echo "   2. Go to project: cd /path/to/cold-storage"
echo "   3. Deploy: ./deploy-server.sh"