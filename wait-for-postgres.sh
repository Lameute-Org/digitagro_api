#!/bin/bash
# wait-for-postgres.sh

set -e

host="$1"
shift
cmd="$@"

until PGPASSWORD=$DB_PASSWORD psql -h "$host" -U "$DB_USER" -d "$DB_NAME" -c '\q'; do
  echo "⏳ Attente de PostgreSQL ($host)..."
  sleep 2
done

echo "✅ PostgreSQL est prêt !"
exec $cmd
