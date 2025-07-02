#!/bin/bash

# Server deployment script - laddar färdiga images från GitHub
set -e

echo "🚀 Starting server deployment..."

# Kontrollera att .env finns
if [ ! -f ".env" ]; then
    echo "❌ .env fil saknas! Skapa den först."
    echo "Exempel:"
    echo "DOMAINS=coldstorage.enproduktionsbyra.se"
    echo "LETSENCRYPT_EMAIL=admin@eapf.se"
    exit 1
fi

# Ladda miljövariabler
source .env

echo "📋 Deployment info:"
echo "   Domain: $DOMAINS"
echo "   Email: $LETSENCRYPT_EMAIL"

# Kontrollera att webproxy network finns
if ! docker network ls | grep -q webproxy; then
    echo "❌ webproxy network finns inte. Skapa det först:"
    echo "docker network create webproxy"
    exit 1
fi

# Stash any local changes
echo "💾 Stashing local changes..."
git stash push -m "Auto-stash before deployment $(date)" || true

# Hämta senaste från GitHub
echo "⬇️ Fetching latest from GitHub..."
git fetch origin

# Visa vilken commit vi är på nu vs senaste
CURRENT_COMMIT=$(git rev-parse HEAD)
LATEST_COMMIT=$(git rev-parse origin/main)

if [ "$CURRENT_COMMIT" = "$LATEST_COMMIT" ]; then
    echo "✅ Already on latest commit"
else
    echo "🔄 Updating from GitHub..."
    echo "   Current: ${CURRENT_COMMIT:0:8}"
    echo "   Latest:  ${LATEST_COMMIT:0:8}"
    git pull origin main
fi

# Kontrollera att Docker images finns (från GitHub)
if [ ! -f "backend/backend-image.tar.gz" ]; then
    echo "❌ backend/backend-image.tar.gz saknas!"
    echo "💡 Kör './deploy-local.sh' på din lokala maskin först"
    exit 1
fi

if [ ! -f "frontend/frontend-image.tar.gz" ]; then
    echo "❌ frontend/frontend-image.tar.gz saknas!"
    echo "💡 Kör './deploy-local.sh' på din lokala maskin först"
    exit 1
fi

echo "✅ Docker images found (från GitHub)"
echo "   Backend: $(ls -lh backend/backend-image.tar.gz | awk '{print $5}')"
echo "   Frontend: $(ls -lh frontend/frontend-image.tar.gz | awk '{print $5}')"

# Stoppa befintliga containers
echo "🛑 Stoppar befintliga containers..."
docker-compose -f docker-compose.prod.yml down || true

# Ladda Docker images
echo "📥 Loading backend image..."
docker load < backend/backend-image.tar.gz

echo "📥 Loading frontend image..."
docker load < frontend/frontend-image.tar.gz

# Starta services med production compose file
echo "🚀 Startar services..."
docker-compose -f docker-compose.prod.yml up -d

# Vänta på att services ska starta
echo "⏳ Väntar på services..."
sleep 15

# Kontrollera status
echo "📊 Container status:"
docker-compose -f docker-compose.prod.yml ps

# Kontrollera hälsa
echo "🏥 Kontrollerar backend hälsa..."
sleep 5
if docker-compose exec -T backend python -c "import requests; requests.get('http://localhost:8000/')" > /dev/null 2>&1; then
    echo "✅ Backend är redo"
else
    echo "⚠️ Backend svarar inte ännu, kolla loggarna"
fi

echo ""
echo "✅ Server deployment klart!"
echo "🌐 Frontend: https://$DOMAINS"
echo "🔧 Backend API: https://$DOMAINS/api/"
echo ""
echo "📋 Loaded images:"
echo "   Backend: $(docker images cold-storage-backend --format 'table {{.Repository}}:{{.Tag}} {{.Size}}' | tail -1)"
echo "   Frontend: $(docker images cold-storage-frontend --format 'table {{.Repository}}:{{.Tag}} {{.Size}}' | tail -1)"
echo ""
echo "📋 För att se loggar:"
echo "   docker-compose logs -f"
echo ""
echo "🔧 För att stoppa:"
echo "   docker-compose down"
echo ""
echo "🔄 För att deploya igen:"
echo "   1. Lokalt: ./deploy-local.sh"
echo "   2. Server: ./deploy-server.sh"