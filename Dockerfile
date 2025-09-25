# Image de base Python
FROM python:3.11-slim

# Définir le répertoire de travail
WORKDIR /app

# Installer dépendances système utiles
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copier et installer les dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code Django
COPY . .

# Exposer le port interne
EXPOSE 8000

# Lancer avec Uvicorn (ASGI pour WebSockets)
CMD ["uvicorn", "digitagro_api.asgi:application", "--host", "0.0.0.0", "--port", "8000"]
