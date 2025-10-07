#!/bin/bash
set -e

APP_DIR="/home/digitagro/digitagro_api"
cd $APP_DIR

echo "📥 [GIT] Pull des dernières modifications..."
git fetch origin main
git reset --hard origin/main

echo "🐳 [DOCKER] Supprimer l'ancien container si existant..."
docker ps -a -q --filter "name=digitagro_api" | xargs -r docker rm -f

echo "🐳 [DOCKER] Build et lancement du container..."
docker-compose up -d --build

echo "🏥 [HEALTH] Vérification de l'état de l'API..."
sleep 5
if curl -f http://localhost:8001/api/docs/ > /dev/null 2>&1; then
    echo "✅ [SUCCESS] API accessible sur http://localhost:8001/api/docs/"
else
    echo "⚠️ [WARNING] API potentiellement non accessible"
fi

echo "🔍 [LOGS] Affichage des logs récents..."
docker-compose logs --tail=20 digitagro_api

echo "✅ [DEPLOY] Déploiement terminé avec succès"
