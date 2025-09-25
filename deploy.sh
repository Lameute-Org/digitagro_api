#!/bin/bash
set -e

APP_DIR="/home/digitagro/digitagro_api"

echo "🚀 [DEPLOY] Début du déploiement de Digitagro API"

cd $APP_DIR

echo "📥 [GIT] Pull des dernières modifications..."
git fetch origin main
git reset --hard origin/main

echo "🐳 [DOCKER] Reconstruction et relance..."
docker-compose down
docker-compose up -d --build

echo "🗄️ [DJANGO] Appliquer les migrations..."
docker-compose exec -T django_app python manage.py migrate --noinput

echo "📦 [DJANGO] Collecter les fichiers statiques..."
docker-compose exec -T django_app python manage.py collectstatic --noinput

echo "✅ [DEPLOY] Déploiement terminé avec succès"
