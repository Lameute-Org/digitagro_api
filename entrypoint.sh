#!/bin/sh
set -e

# Vérifier si on est en mode DEBUG
if [ "$DEBUG" = "True" ] || [ "$DEBUG" = "true" ]; then
  echo "DEBUG=True -> on ne vérifie pas la base de données."
else
  echo "DEBUG=False -> attente de la base de données..."
  sh /app/wait-for-postgres.sh "$DB_HOST" true
fi

# Exécuter les migrations et collectstatic
python manage.py migrate --noinput
python manage.py collectstatic --noinput

# Lancer Uvicorn
exec uvicorn digitagro_api.asgi:application --host 0.0.0.0 --port 8000
