#!/bin/bash

# Server deployment script - hämtar från GitHub Container Registry
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

# Hämta senaste från GitHub
echo "⬇️ Pulling latest changes from GitHub..."
git pull origin main

# Pull latest Docker images från GitHub Container Registry
echo "📥 Pulling latest Docker images..."
docker pull ghcr.io/en-produktionsbyra/cold-storage:backend-latest
docker pull ghcr.io/en-produktionsbyra/cold-storage:frontend-latest

# Tag images för lokal användning
docker tag ghcr.io/en-produktionsbyra/cold-storage:backend-latest cold-storage-backend:latest
docker tag ghcr.io/en-produktionsbyra/cold-storage:frontend-latest cold-storage-frontend:latest

# Stoppa befintliga containers
echo "🛑 Stoppar befintliga containers..."
docker-compose -f docker-compose.prod.yml down || true

# Starta services med nya images
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
if docker-compose -f docker-compose.prod.yml exec -T backend python -c "import requests; requests.get('http://localhost:8000/')" > /dev/null 2>&1; then
    echo "✅ Backend är redo"
else
    echo "⚠️ Backend svarar inte ännu, kolla loggarna"
fi

echo ""
echo "✅ Server deployment klart!"
echo "🌐 Frontend: https://$DOMAINS"
echo "🔧 Backend API: https://$DOMAINS/api/"
echo ""
echo "📋 Deployed images:"
echo "   Backend: ghcr.io/en-produktionsbyra/cold-storage:backend-latest"
echo "   Frontend: ghcr.io/en-produktionsbyra/cold-storage:frontend-latest"
echo ""
echo "📋 För att se loggar:"
echo "   docker-compose -f docker-compose.prod.yml logs -f"