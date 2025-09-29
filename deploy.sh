#!/bin/bash
set -e

APP_DIR="/home/digitagro/digitagro_api"

echo "🚀 [DEPLOY] Début du déploiement de Digitagro API"

cd $APP_DIR

echo "📥 [GIT] Pull des dernières modifications..."
git fetch origin main
git reset --hard origin/main

echo "🐳 [DOCKER] Suppression des anciens conteneurs si existants..."
docker ps -a -q --filter "name=digitagro_api" | xargs -r docker rm -f

echo "🐳 [DOCKER] Reconstruction et relance..."
docker-compose up -d --build

echo "⏳ [DOCKER] Attente du démarrage du conteneur..."
sleep 10

echo "🗄️ [DJANGO] Appliquer les migrations..."
docker-compose exec -T digitagro_api python manage.py makemigrations
docker-compose exec -T digitagro_api python manage.py migrate --noinput

echo "🔑 [KNOX] Création des tables Knox..."
docker-compose exec -T digitagro_api python manage.py migrate knox --noinput

echo "📦 [DJANGO] Collecter les fichiers statiques..."
docker-compose exec -T digitagro_api python manage.py collectstatic --noinput

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
echo "📊 [INFO] Swagger disponible: http://185.217.125.37:8001/api/docs/"
