#!/bin/bash

# Local deployment script - bygger och pushar till GitHub
set -e

echo "🚀 Starting local deployment build..."

# Kontrollera att vi är i rätt katalog
if [ ! -f "package.json" ] && [ ! -d "frontend" ]; then
    echo "❌ Kör från projektets root-katalog (där frontend/ finns)"
    exit 1
fi

# Stash local changes if any
echo "💾 Stashing any uncommitted changes..."
git stash push -m "Auto-stash before deployment $(date)"

# Pull latest changes
echo "⬇️ Pulling latest changes from GitHub..."
git pull origin main

# Build frontend
echo "🔨 Building frontend..."
cd frontend
npm install
npm run build
cd ..

# Add built files to git
echo "📦 Adding built files to git..."
git add frontend/dist/
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
- Ready for server deployment"
fi

# Push to GitHub
echo "⬆️ Pushing to GitHub..."
git push origin main

echo ""
echo "✅ Local deployment complete!"
echo "🌐 Built files pushed to GitHub"
echo "🔧 Now run './deploy-server.sh' on the server to deploy"
echo ""
echo "📋 Next steps:"
echo "   1. SSH to server: ssh your-server"
echo "   2. Go to project: cd /path/to/cold-storage"
echo "   3. Deploy: ./deploy-server.sh"