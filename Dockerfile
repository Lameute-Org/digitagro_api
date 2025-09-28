# Image de base Python
FROM python:3.12-slim

# Définir le répertoire de travail
WORKDIR /app

# Installer dépendances système pour PostgreSQL et images
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    libjpeg-dev \
    libpng-dev \
    libwebp-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Copier et installer les dépendances Python avec timeout étendu
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir --timeout=1000 --retries=5 -r requirements.txt

# Copier le code Django
COPY . .

# Créer les répertoires pour les fichiers statiques et media
RUN mkdir -p /app/staticfiles /app/media

# Collecter les fichiers statiques
RUN python manage.py collectstatic --noinput

# Exposer le port interne
EXPOSE 8000

# Commande de démarrage avec Uvicorn (ASGI pour WebSockets futures)
CMD ["uvicorn", "digitagro_api.asgi:application", "--host", "0.0.0.0", "--port", "8000"]