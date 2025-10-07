#!/bin/sh
set -e

sh /app/wait-for-postgres.sh $DB_HOST true

python manage.py migrate --noinput
python manage.py collectstatic --noinput
exec uvicorn digitagro_api.asgi:application --host 0.0.0.0 --port 8000
