#!/bin/sh
set -e

# Attendre PostgreSQL
/app/wait-for-postgres.sh $DB_HOST true

echo "⏳ [DJANGO] Appliquer les migrations..."
python manage.py migrate --noinput

echo "📦 [DJANGO] Collecter les fichiers statiques..."
python manage.py collectstatic --noinput

echo "🚀 [DJANGO] Lancer Uvicorn..."
exec uvicorn digitagro_api.asgi:application --host 0.0.0.0 --port 8000
