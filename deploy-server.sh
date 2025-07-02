#!/bin/bash

# Deployment script för Cold Storage på server med reverse proxy
set -e

echo "🚀 Deploying Cold Storage to production server..."

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
echo "   API Domain: api.$DOMAINS"
echo "   Email: $LETSENCRYPT_EMAIL"

# Kontrollera att webproxy network finns
if ! docker network ls | grep -q webproxy; then
    echo "❌ webproxy network finns inte. Skapa det först:"
    echo "docker network create webproxy"
    exit 1
fi

# Stoppa befintliga containers
echo "🛑 Stoppar befintliga containers..."
docker-compose down

# Bygga nya images
echo "🔨 Bygger nya images..."
docker-compose build --no-cache

# Starta services
echo "🚀 Startar services..."
docker-compose up -d

# Vänta på att services ska starta
echo "⏳ Väntar på services..."
sleep 15

# Kontrollera status
echo "📊 Container status:"
docker-compose ps

# Kontrollera hälsa
echo "🏥 Kontrollerar backend hälsa..."
sleep 5
if docker-compose exec -T backend curl -f http://localhost:8000/ > /dev/null 2>&1; then
    echo "✅ Backend är redo"
else
    echo "⚠️ Backend svarar inte ännu, kolla loggarna"
fi

echo ""
echo "✅ Deployment klart!"
echo "🌐 Frontend: https://$DOMAINS"
echo "🔧 Backend API: https://api.$DOMAINS"
echo ""
echo "📋 För att se loggar:"
echo "   docker-compose logs -f"
echo ""
echo "🔧 För att stoppa:"
echo "   docker-compose down"