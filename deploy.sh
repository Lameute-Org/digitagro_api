#!/bin/bash
set -e

APP_DIR="/home/digitagro/digitagro_api"
cd "$APP_DIR"

echo "📥 [GIT] Pull des dernières modifications..."
git reset --hard HEAD  # ← AJOUTER
git clean -fd          # ← AJOUTER
git pull origin main

echo "🐳 [DOCKER] Nettoyage des anciens conteneurs..."
docker ps -a --filter "name=digitagro_api" -q | xargs -r docker rm -f || true

echo "🐳 [DOCKER] Build et lancement du container..."
docker compose down -v || true
docker compose up -d --build

echo "🏥 [HEALTH] Vérification de l'état de l'API..."
sleep 5
if curl -fs http://localhost:8001/api/docs/ >/dev/null; then
    echo "✅ [SUCCESS] API accessible sur http://localhost:8001/api/docs/"
else
    echo "⚠️ [WARNING] API potentiellement non accessible (à vérifier)"
fi

echo "🔍 [LOGS] Affichage des logs récents..."
docker compose logs --tail=20 digitagro_api

echo "✅ [DEPLOY] Déploiement terminé avec succès 🎉"