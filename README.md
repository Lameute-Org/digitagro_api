# DIGITAGRO API v2.0 - Documentation Complète

## 📋 Description

DIGITAGRO est une API REST moderne pour la plateforme agrosylvopastorale camerounaise, connectant producteurs, transporteurs, transformateurs, distributeurs et consommateurs avec **activation dynamique des rôles**.

### 🎯 Innovation v2.0 : Système Multi-Rôles Dynamique
- **Tous les utilisateurs sont consommateurs par défaut**
- **Activation automatique** des rôles professionnels selon les actions
- **Zero friction** : Devenir producteur en déclarant sa première production

---

## 🚀 Installation Rapide

```bash
# 1. Cloner le projet
git clone https://github.com/digitagro/api.git
cd digitagro_api

# 2. Configuration environnement
cp .env.example .env
nano .env  # Éditer avec vos credentials

# 3. Lancer avec Docker
docker-compose up -d --build

# 4. Migrations base de données
docker exec -it digitagro_api python manage.py migrate

# 5. Créer superuser (optionnel)
docker exec -it digitagro_api python manage.py createsuperuser

# 6. Vérifier que l'API fonctionne
curl http://localhost:8001/api/docs/
```

---

## 📚 Documentation API Complète avec Exemples

### 🔐 Module Authentification

#### 1. Inscription Utilisateur
**POST** `/api/auth/register/`

Tout nouvel utilisateur est automatiquement consommateur.

```bash
curl -X POST http://localhost:8001/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "jean.dupont@example.com",
    "telephone": "+237690123456",
    "nom": "Dupont",
    "prenom": "Jean",
    "adresse": "Yaoundé, Quartier Bastos",
    "password": "SecurePass123!",
    "password_confirm": "SecurePass123!"
  }'
```

**Réponse (201):**
```json
{
  "user": {
    "id": 1,
    "email": "jean.dupont@example.com",
    "telephone": "+237690123456",
    "nom": "Dupont",
    "prenom": "Jean",
    "is_consommateur": true,
    "is_producteur": false,
    "is_transporteur": false,
    "profile_completed": true,
    "active_roles": ["consommateur"]
  },
  "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b",
  "expiry": "2025-12-31T23:59:59.999999Z"
}
```

#### 2. Connexion (Email ou Téléphone)
**POST** `/api/auth/login/`

```bash
# Connexion avec email
curl -X POST http://localhost:8001/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "identifier": "jean.dupont@example.com",
    "password": "SecurePass123!"
  }'

# OU connexion avec téléphone
curl -X POST http://localhost:8001/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "identifier": "+237690123456",
    "password": "SecurePass123!"
  }'
```

**Réponse (200):**
```json
{
  "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b",
  "expiry": "2025-12-31T23:59:59.999999Z",
  "user": {
    "id": 1,
    "email": "jean.dupont@example.com",
    "active_roles": ["consommateur"],
    "role_profiles": {}
  }
}
```

#### 3. Consulter Mon Profil
**GET** `/api/auth/me/`

```bash
curl -X GET http://localhost:8001/api/auth/me/ \
  -H "Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"
```

**Réponse (200):**
```json
{
  "id": 1,
  "email": "jean.dupont@example.com",
  "telephone": "+237690123456",
  "nom": "Dupont",
  "prenom": "Jean",
  "adresse": "Yaoundé, Quartier Bastos",
  "avatar": "/media/avatars/jean_photo.jpg",
  "is_consommateur": true,
  "is_producteur": true,
  "is_producteur_verified": false,
  "profile_completed": true,
  "active_roles": ["consommateur", "producteur"],
  "role_profiles": {
    "producteur": {
      "type_production": "Maraîchage",
      "superficie": 2.5,
      "certification": "bio",
      "total_productions": 3
    }
  }
}
```

#### 4. Mettre à Jour Profil avec Avatar
**PATCH** `/api/auth/me/`

```bash
curl -X PATCH http://localhost:8001/api/auth/me/ \
  -H "Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b" \
  -F "telephone=+237690999888" \
  -F "adresse=Douala, Bonanjo" \
  -F "avatar=@/path/to/photo.jpg"
```

#### 5. Vérifier Statut des Rôles
**GET** `/api/auth/roles-status/`

```bash
curl -X GET http://localhost:8001/api/auth/roles-status/ \
  -H "Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"
```

**Réponse (200):**
```json
{
  "active_roles": ["consommateur", "producteur"],
  "available_roles": {
    "producteur": {
      "active": true,
      "verified": false,
      "activated_at": "2025-01-15T10:30:00Z"
    },
    "transporteur": {
      "active": false,
      "verified": false,
      "activated_at": null
    },
    "transformateur": {
      "active": false,
      "verified": false,
      "activated_at": null
    },
    "distributeur": {
      "active": false,
      "verified": false,
      "activated_at": null
    }
  },
  "profile_completed": true
}
```

#### 6. Activer un Rôle Manuellement
**POST** `/api/auth/activate-role/`

Pour devenir transporteur par exemple:

```bash
curl -X POST http://localhost:8001/api/auth/activate-role/ \
  -H "Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b" \
  -H "Content-Type: application/json" \
  -d '{
    "role": "transporteur",
    "type_vehicule": "Camion frigorifique",
    "capacite": 5.0,
    "permis_transport": "TR-2024-1234"
  }'
```

#### 7. Reset Password - Demande
**POST** `/api/auth/password/request-reset/`

```bash
curl -X POST http://localhost:8001/api/auth/password/request-reset/ \
  -H "Content-Type: application/json" \
  -d '{
    "identifier": "jean.dupont@example.com"
  }'
```

**Réponse (200):**
```json
{
  "message": "Code de réinitialisation envoyé"
}
```
Un email avec code OTP 6 chiffres est envoyé.

#### 8. Reset Password - Vérifier OTP
**POST** `/api/auth/password/verify-otp/`

```bash
curl -X POST http://localhost:8001/api/auth/password/verify-otp/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "jean.dupont@example.com",
    "otp_code": "123456"
  }'
```

**Réponse (200):**
```json
{
  "message": "Code validé",
  "reset_token": "XyZ9_abcdefghijklmnopqrstuvwxyz1234567890"
}
```

#### 9. Reset Password - Confirmer
**POST** `/api/auth/password/reset-confirm/`

```bash
curl -X POST http://localhost:8001/api/auth/password/reset-confirm/ \
  -H "Content-Type: application/json" \
  -d '{
    "reset_token": "XyZ9_abcdefghijklmnopqrstuvwxyz1234567890",
    "new_password": "NouveauPass456!",
    "new_password_confirm": "NouveauPass456!"
  }'
```

#### 10. Déconnexion
**POST** `/api/auth/logout/`

```bash
curl -X POST http://localhost:8001/api/auth/logout/ \
  -H "Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"
```

---

### 🌾 Module Production

#### 1. Déclarer Première Production (Activation Automatique Producteur)
**POST** `/api/productions/`

⚠️ **Important**: Si pas encore producteur, inclure `type_production` pour activation automatique.

```bash
# Première production - Devient automatiquement producteur
curl -X POST http://localhost:8001/api/productions/ \
  -H "Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b" \
  -H "Content-Type: application/json" \
  -d '{
    "type_production": "Maraîchage",
    "superficie": 2.5,
    "certification": "bio",
    "produit": "Tomates fraîches",
    "type_production": "legumes",
    "quantite": 100,
    "unite_mesure": "kg",
    "prix_unitaire": 500,
    "latitude": 3.8667,
    "longitude": 11.5167,
    "adresse_complete": "Yaoundé, Quartier Melen",
    "date_recolte": "2025-02-15",
    "date_expiration": "2025-02-25",
    "description": "Tomates biologiques cultivées sans pesticides",
    "conditions_stockage": "Conserver au frais, température 10-15°C"
  }'
```

**Réponse (201):**
```json
{
  "id": 1,
  "message": "Production créée et rôle producteur activé",
  "produit": "Tomates fraîches",
  "quantite_disponible": 100
}
```

#### 2. Déclarer Productions Suivantes
**POST** `/api/productions/`

Une fois producteur, plus besoin de `type_production`:

```bash
curl -X POST http://localhost:8001/api/productions/ \
  -H "Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b" \
  -H "Content-Type: application/json" \
  -d '{
    "produit": "Carottes bio",
    "quantite": 50,
    "unite_mesure": "kg",
    "prix_unitaire": 400,
    "latitude": 3.8667,
    "longitude": 11.5167,
    "adresse_complete": "Yaoundé, Quartier Melen",
    "date_recolte": "2025-02-20",
    "description": "Carottes fraîches de saison"
  }'
```

#### 3. Lister Toutes les Productions
**GET** `/api/productions/`

```bash
curl -X GET http://localhost:8001/api/productions/ \
  -H "Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"
```

**Avec pagination:**
```bash
curl -X GET "http://localhost:8001/api/productions/?page=2&page_size=20" \
  -H "Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"
```

#### 4. Recherche Productions à Proximité
**GET** `/api/productions/nearby/`

```bash
curl -X GET "http://localhost:8001/api/productions/nearby/?lat=3.8667&lon=11.5167&radius=10" \
  -H "Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"
```

**Réponse (200):**
```json
[
  {
    "id": 1,
    "produit": "Tomates fraîches",
    "distance_km": 2.3,
    "producteur_nom": "Jean Dupont",
    "prix_unitaire": 500,
    "quantite_disponible": 85
  },
  {
    "id": 3,
    "produit": "Bananes plantain",
    "distance_km": 4.7,
    "producteur_nom": "Marie Kotto",
    "prix_unitaire": 300,
    "quantite_disponible": 200
  }
]
```

#### 5. Détail d'une Production
**GET** `/api/productions/{id}/`

```bash
curl -X GET http://localhost:8001/api/productions/1/ \
  -H "Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"
```

#### 6. Modifier une Production (Propriétaire uniquement)
**PATCH** `/api/productions/{id}/`

```bash
curl -X PATCH http://localhost:8001/api/productions/1/ \
  -H "Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b" \
  -H "Content-Type: application/json" \
  -d '{
    "prix_unitaire": 450,
    "quantite": 80,
    "description": "Promotion spéciale cette semaine!"
  }'
```

#### 7. Ajouter Photo à une Production
**POST** `/api/productions/{id}/upload_photo/`

```bash
curl -X POST http://localhost:8001/api/productions/1/upload_photo/ \
  -H "Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b" \
  -F "image=@/path/to/tomates.jpg" \
  -F "ordre=0"
```

---

### 📦 Module Commandes

#### 1. Passer une Commande
**POST** `/api/commandes/`

```bash
curl -X POST http://localhost:8001/api/commandes/ \
  -H "Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b" \
  -H "Content-Type: application/json" \
  -d '{
    "production": 1,
    "quantite": 10,
    "adresse_livraison": "Douala, Akwa Nord, Rue des Fleurs",
    "notes": "Livrer avant 10h du matin svp",
    "date_livraison_souhaitee": "2025-02-18"
  }'
```

**Réponse (201):**
```json
{
  "id": 1,
  "production_info": {
    "id": 1,
    "produit": "Tomates fraîches",
    "prix_unitaire": 500,
    "producteur_nom": "Jean Dupont"
  },
  "quantite": 10,
  "montant_total": 5000,
  "statut": "en_attente",
  "adresse_livraison": "Douala, Akwa Nord, Rue des Fleurs",
  "date_creation": "2025-01-15T14:30:00Z"
}
```

#### 2. Lister Mes Commandes
**GET** `/api/commandes/`

```bash
# Client voit ses achats, Producteur voit ses ventes
curl -X GET http://localhost:8001/api/commandes/ \
  -H "Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"
```

#### 3. Confirmer une Commande (Producteur uniquement)
**POST** `/api/commandes/{id}/confirm/`

```bash
curl -X POST http://localhost:8001/api/commandes/1/confirm/ \
  -H "Authorization: Token PRODUCTEUR_TOKEN"
```

**Réponse (200):**
```json
{
  "status": "confirmée",
  "message": "Notification envoyée au client"
}
```

#### 4. Marquer comme Expédiée (Producteur)
**POST** `/api/commandes/{id}/ship/`

```bash
curl -X POST http://localhost:8001/api/commandes/1/ship/ \
  -H "Authorization: Token PRODUCTEUR_TOKEN"
```

#### 5. Marquer comme Livrée
**POST** `/api/commandes/{id}/deliver/`

```bash
curl -X POST http://localhost:8001/api/commandes/1/deliver/ \
  -H "Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"
```

#### 6. Annuler une Commande
**POST** `/api/commandes/{id}/cancel/`

```bash
curl -X POST http://localhost:8001/api/commandes/1/cancel/ \
  -H "Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b" \
  -H "Content-Type: application/json" \
  -d '{
    "raison": "Changement de plans"
  }'
```

---

### ⭐ Module Évaluations

#### Créer une Évaluation après Livraison
**POST** `/api/evaluations/`

```bash
curl -X POST http://localhost:8001/api/evaluations/ \
  -H "Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b" \
  -F "commande=1" \
  -F "note=5" \
  -F "commentaire=Excellente qualité, livraison rapide!" \
  -F "photos=@/path/to/photo1.jpg" \
  -F "photos=@/path/to/photo2.jpg"
```

**Réponse (201):**
```json
{
  "id": 1,
  "commande": 1,
  "note": 5,
  "commentaire": "Excellente qualité, livraison rapide!",
  "date_creation": "2025-01-20T16:00:00Z"
}
```

---

### 🔔 Module Notifications WebSocket

#### Connexion WebSocket
```javascript
// JavaScript/React Native
const token = "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b";
const ws = new WebSocket(`ws://localhost:8001/ws/notifications/?token=${token}`);

ws.onopen = () => {
  console.log("Connecté aux notifications");
};

ws.onmessage = (event) => {
  const notification = JSON.parse(event.data);
  console.log("Nouvelle notification:", notification);
  
  // Afficher notification à l'utilisateur
  if (notification.type === 'new_order') {
    showNotification("Nouvelle commande reçue!", notification.message);
  }
};

// Marquer comme lue
ws.send(JSON.stringify({
  action: 'mark_read',
  notification_id: 123
}));
```

#### Récupérer Notifications Non Lues (HTTP)
**GET** `/api/notifications/unread/`

```bash
curl -X GET http://localhost:8001/api/notifications/unread/ \
  -H "Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"
```

**Réponse (200):**
```json
{
  "count": 3,
  "results": [
    {
      "id": 123,
      "type": "new_order",
      "icon": "📋",
      "title": "Nouvelle commande reçue",
      "message": "Marie Martin - 10 kg Tomates fraîches",
      "data": {
        "order_id": 45,
        "amount": 5000
      },
      "is_read": false,
      "created_at": "2025-01-15T14:30:00Z"
    }
  ]
}
```

#### Marquer Toutes comme Lues
**POST** `/api/notifications/mark_all_read/`

```bash
curl -X POST http://localhost:8001/api/notifications/mark_all_read/ \
  -H "Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"
```

---

## 🔧 Configuration Environnement

### Fichier `.env` complet

```bash
# === Django Core ===
SECRET_KEY=django-insecure-&*)@#$%^&*()_+very_secret_key_here
DEBUG=False
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,185.217.125.37,digitagro.com

# === Database PostgreSQL ===
DB_HOST=185.217.125.37
DB_PORT=5432
DB_NAME=digitagro_db
DB_USER=digitagro
DB_PASSWORD=Digitagro@2002

# === MongoDB (pour chat futur) ===
MONGODB_URL=mongodb://185.217.125.37:27017/digitagro_chat

# === Email Configuration (pour OTP) ===
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=noreply@digitagro.com
EMAIL_HOST_PASSWORD=app_specific_password_here

# === Frontend URLs ===
FRONTEND_URL=https://digitagro.com
FRONTEND_RESET_URL=https://digitagro.com/reset-password

# === Redis (pour WebSocket) ===
REDIS_URL=redis://localhost:6379/0

# === AWS S3 (optionnel pour media) ===
USE_S3=False
AWS_ACCESS_KEY_ID=your_key_here
AWS_SECRET_ACCESS_KEY=your_secret_here
AWS_STORAGE_BUCKET_NAME=digitagro-media

# === Sentry (monitoring production) ===
SENTRY_DSN=https://your_key@sentry.io/project_id

# === Elasticsearch ===
ELASTICSEARCH_DSL_HOST=localhost:9200
```

---

## 🐳 Docker Commands Utiles

```bash
# Voir logs en temps réel
docker-compose logs -f digitagro_api

# Accéder au shell Django
docker exec -it digitagro_api python manage.py shell

# Créer superuser
docker exec -it digitagro_api python manage.py createsuperuser

# Faire migrations
docker exec -it digitagro_api python manage.py makemigrations
docker exec -it digitagro_api python manage.py migrate

# Collecter fichiers statiques
docker exec -it digitagro_api python manage.py collectstatic --noinput

# Restart container
docker-compose restart digitagro_api

# Rebuild après changements
docker-compose up -d --build digitagro_api
```

---

## 📊 Monitoring & Health Checks

### Health Check Endpoint
```bash
curl http://localhost:8001/api/health/

# Réponse attendue
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "version": "2.0.0"
}
```

### Métriques Prometheus (si configuré)
```bash
curl http://localhost:8001/metrics/
```

---

## 🧪 Tests Automatisés

### Lancer tous les tests
```bash
docker exec -it digitagro_api python manage.py test
```

### Tests avec coverage
```bash
docker exec -it digitagro_api coverage run --source='.' manage.py test
docker exec -it digitagro_api coverage report
docker exec -it digitagro_api coverage html  # Génère rapport HTML
```

### Test spécifique module
```bash
# Tester uniquement users
docker exec -it digitagro_api python manage.py test apps.users

# Tester uniquement production
docker exec -it digitagro_api python manage.py test apps.production
```

---

## 🚀 Déploiement Production

### Script automatisé
```bash
./deploy.sh

# Le script effectue:
# 1. Git pull origin main
# 2. Docker-compose down
# 3. Docker-compose up -d --build
# 4. Migrations automatiques
# 5. Collect static
# 6. Health check
# 7. Affiche logs
```

### Déploiement manuel étape par étape
```bash
# 1. Se connecter au serveur
ssh user@185.217.125.37

# 2. Aller dans le dossier projet
cd /home/digitagro/digitagro_api

# 3. Pull derniers changements
git pull origin main

# 4. Rebuild et restart
docker-compose down
docker-compose up -d --build

# 5. Vérifier logs
docker-compose logs --tail=50 digitagro_api
```

---

## 🔍 Debugging

### Activer mode DEBUG temporairement
```bash
docker exec -it digitagro_api bash
export DEBUG=True
python manage.py runserver 0.0.0.0:8000
```

### Voir requêtes SQL
```python
# Dans Django shell
from django.db import connection
from django.conf import settings
settings.DEBUG = True

# Faire requête
from apps.users.models import CustomUser
CustomUser.objects.all()

# Voir SQL
for query in connection.queries:
    print(query['sql'])
```

### Tester WebSocket manuellement
```bash
# Installer wscat
npm install -g wscat

# Se connecter
wscat -c "ws://localhost:8001/ws/notifications/?token=YOUR_TOKEN"
```

---

## 📈 Optimisations Performance

### Index Database créés
```sql
-- Index pour recherche rapide
CREATE INDEX idx_production_produit ON production_production(produit);
CREATE INDEX idx_production_disponible ON production_production(disponible);
CREATE INDEX idx_production_date ON production_production(date_creation);
CREATE INDEX idx_user_email ON users_customuser(email);
CREATE INDEX idx_user_telephone ON users_customuser(telephone);
```

### Cache Redis (si activé)
```python
# settings.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}
```

---

## 🤝 Contribution

### Workflow Git
```bash
# 1. Fork le projet
# 2. Clone votre fork
git clone https://github.com/votre-username/digitagro-api.git

# 3. Créer branche feature
git checkout -b feature/nouvelle-fonctionnalite

# 4. Faire modifications et commit
git add .
git commit -m "feat: ajout nouvelle fonctionnalité"

# 5. Push vers votre fork
git push origin feature/nouvelle-fonctionnalite

# 6. Créer Pull Request sur GitHub
```

### Conventions de commit
- `feat:` Nouvelle fonctionnalité
- `fix:` Correction bug
- `docs:` Documentation
- `style:` Formatage code
- `refactor:` Refactoring
- `test:` Ajout tests
- `chore:` Maintenance

---

## 🐛 Problèmes Fréquents

### Erreur "Port already in use"
```bash
# Trouver processus sur port 8001
sudo lsof -i :8001
# Tuer le processus
sudo kill -9 <PID>
```

### Erreur "Cannot connect to database"
```bash
# Vérifier PostgreSQL
docker-compose logs db
# Restart PostgreSQL
docker-compose restart db
```

### Migrations en conflit
```bash
# Réinitialiser migrations
docker exec -it digitagro_api python manage.py migrate app_name zero
docker exec -it digitagro_api python manage.py migrate
```

---

## 📄 Licence

Copyright © 2025 DIGITAGRO. Tous droits réservés.

---

## 💬 Support & Contact

- **Documentation API**: http://localhost:8001/api/docs/
- **Email Support**: support@digitagro.cm
- **WhatsApp Business**: +237 6XX XXX XXX
- **Serveur Production**: https://api.digitagro.cm

---

**Version**: 2.0.0  
**Dernière mise à jour**: Janvier 2025  
**Statut**: Production Ready ✅  
**Mainteneur**: Équipe Backend DIGITAGRO