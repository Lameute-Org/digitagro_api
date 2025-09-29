FROM python:3.12-slim

WORKDIR /app

# Installer dépendances système et client PostgreSQL
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    postgresql-client \
    libjpeg-dev \
    libpng-dev \
    libwebp-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Copier et installer les dépendances Python
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir --timeout=1000 --retries=5 -r requirements.txt

# Copier le code Django
COPY . .

# Créer les répertoires statiques et media
RUN mkdir -p /app/staticfiles /app/media

# Collecter les fichiers statiques
RUN python manage.py collectstatic --noinput

# Copier le script wait-for-postgres
COPY wait-for-postgres.sh /app/wait-for-postgres.sh
RUN chmod +x /app/wait-for-postgres.sh

EXPOSE 8000

# Lancer les migrations et Uvicorn après que PostgreSQL soit prêt
CMD [ "sh", "/app/wait-for-postgres.sh", "185.217.125.37", "python manage.py migrate --noinput && python manage.py collectstatic --noinput && uvicorn digitagro_api.asgi:application --host 0.0.0.0 --port 8000" ]
