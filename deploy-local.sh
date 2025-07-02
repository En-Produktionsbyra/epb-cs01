#!/bin/bash

# Local deployment script - bygger och pushar till GitHub Container Registry
set -e

echo "🚀 Starting local deployment build..."

# Kontrollera att vi är i rätt katalog
if [ ! -d "frontend" ] && [ ! -d "backend" ]; then
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

# Get timestamp for tagging
TIMESTAMP=$(date +"%Y%m%d-%H%M%S")

# Build and push backend Docker image
echo "🔨 Building and pushing backend Docker image..."
docker build -t cold-storage-backend ./backend
docker tag cold-storage-backend ghcr.io/en-produktionsbyra/cold-storage:backend-$TIMESTAMP
docker tag cold-storage-backend ghcr.io/en-produktionsbyra/cold-storage:backend-latest

# Build and push frontend Docker image
echo "🔨 Building and pushing frontend Docker image..."
docker build -f frontend/Dockerfile.prod -t cold-storage-frontend ./frontend
docker tag cold-storage-frontend ghcr.io/en-produktionsbyra/cold-storage:frontend-$TIMESTAMP
docker tag cold-storage-frontend ghcr.io/en-produktionsbyra/cold-storage:frontend-latest

# Push to GitHub Container Registry
echo "⬆️ Pushing images to GitHub Container Registry..."
docker push ghcr.io/en-produktionsbyra/cold-storage:backend-$TIMESTAMP
docker push ghcr.io/en-produktionsbyra/cold-storage:backend-latest
docker push ghcr.io/en-produktionsbyra/cold-storage:frontend-$TIMESTAMP
docker push ghcr.io/en-produktionsbyra/cold-storage:frontend-latest

# Commit source code changes (NO tar.gz files)
echo "📦 Adding source code changes to git..."
git add .

# Check if there are changes to commit
if git diff --staged --quiet; then
    echo "ℹ️ No changes to commit"
else
    # Commit with timestamp
    echo "💾 Committing source changes at $TIMESTAMP..."
    git commit -m "🚀 Deploy build - $TIMESTAMP

- Frontend built with latest changes
- Docker images pushed to ghcr.io/en-produktionsbyra/cold-storage
- Backend: ghcr.io/en-produktionsbyra/cold-storage:backend-$TIMESTAMP
- Frontend: ghcr.io/en-produktionsbyra/cold-storage:frontend-$TIMESTAMP"
fi

# Push to GitHub
echo "⬆️ Pushing to GitHub..."
git push origin main

# Clean up local images to save space
echo "🧹 Cleaning up local Docker images..."
docker rmi cold-storage-backend cold-storage-frontend || true

echo ""
echo "✅ Local deployment complete!"
echo "🌐 Docker images pushed to GitHub Container Registry"
echo "🔧 Now run './deploy-server.sh' on the server to deploy"
echo ""
echo "📋 Images available:"
echo "   Backend: ghcr.io/en-produktionsbyra/cold-storage:backend-latest"
echo "   Frontend: ghcr.io/en-produktionsbyra/cold-storage:frontend-latest"