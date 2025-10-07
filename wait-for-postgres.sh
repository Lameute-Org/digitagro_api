#!/bin/sh
set -e

host="$1"
shift
cmd="$@"

until PGPASSWORD=$DB_PASSWORD psql -h "$host" -U "$DB_USER" -d "$DB_NAME" -c '\q' 2>/dev/null; do
  echo "⏳ Attente de PostgreSQL ($host)..."
  sleep 2
done

echo "✅ PostgreSQL est prêt !"
exec sh -c "$cmd"
