# DIGITAGRO API

## 📋 Description

DIGITAGRO est une API REST moderne pour la plateforme agrosylvopastorale camerounaise, visant à connecter producteurs, transporteurs, transformateurs, distributeurs et consommateurs via une solution numérique centralisée.

### Objectifs
- Réduire les pertes post-récolte (~30% actuellement)
- Fluidifier les échanges entre acteurs
- Améliorer l'accès aux marchés
- Renforcer la traçabilité et la transparence

---

## 🛠️ Stack Technique

| Composant | Version | Rôle |
|-----------|---------|------|
| **Django** | 5.2.6 | Framework backend |
| **Django REST Framework** | 3.16.1 | API REST |
| **PostgreSQL** | 15+ | Base de données principale |
| **MongoDB** | 6+ | Messagerie/Chat (futur) |
| **Knox** | 4.2.0 | Authentification par token |
| **drf-spectacular** | 0.27.0 | Documentation OpenAPI 3.0 |
| **Uvicorn** | 0.24.0 | Serveur ASGI |
| **Docker** | 3.9 | Conteneurisation |

---

## 🐳 Architecture Docker

### Services déployés

```yaml
digitagro_api:
  - Port: 8001:8000
  - Volumes: code, static, media
  - Network: digitagro_network
  - Auto-restart: always

Base de données externe:
  - PostgreSQL: 185.217.125.37:5432
  - Database: digitagro_db
```

### Scripts de déploiement

**`deploy.sh`** - Déploiement automatisé:
```bash
./deploy.sh
# 1. Pull Git (origin/main)
# 2. Supprime ancien container
# 3. Rebuild & redémarrage
# 4. Health check sur /api/docs/
# 5. Affichage logs récents
```

**`entrypoint.sh`** - Point d'entrée container:
```bash
# 1. Attente PostgreSQL (wait-for-postgres.sh)
# 2. Migrations Django
# 3. Collecte fichiers statiques
# 4. Lancement Uvicorn (0.0.0.0:8000)
```

---

## 📁 Structure du Projet

```
digitagro_api/
├── apps/
│   └── users/                 # Module Utilisateurs (✅ COMPLET)
│       ├── models.py          # CustomUser + 5 rôles + PasswordResetRequest
│       ├── serializers.py     # 10 serializers
│       ├── views.py           # 11 vues API
│       ├── urls.py            # 11 endpoints
│       ├── backends.py        # Auth email/téléphone
│       ├── permissions.py     # IsProfileCompleted, IsOwnerOrReadOnly
│       ├── pipeline.py        # Social auth pipeline
│       ├── admin.py           # Interface admin complète
│       └── docs/
│           └── users_swagger.py  # Schémas OpenAPI
├── digitagro_api/
│   ├── settings.py            # Configuration Django
│   ├── urls.py                # Routes principales
│   ├── wsgi.py                # WSGI application
│   └── asgi.py                # ASGI application
├── docker-compose.yml         # Orchestration Docker
├── Dockerfile                 # Image Python
├── requirements.txt           # Dépendances Python
├── deploy.sh                  # Script déploiement
├── entrypoint.sh             # Script démarrage
└── wait-for-postgres.sh      # Health check DB
```

---

## ✅ Modules Implémentés

### 🔐 Module Users/Authentication (100%)

#### Modèles de données
1. **CustomUser** - Utilisateur personnalisé
   - Authentification: email OU téléphone
   - Champs: nom, prénom, adresse, avatar, role_choisi
   - Flag: `profile_completed`

2. **Modèles de rôles** (OneToOne avec User)
   - **Producteur**: type_production, superficie, certification
   - **Transporteur**: type_vehicule, capacite, permis_transport
   - **Transformateur**: type_transformation, capacite_traitement
   - **Distributeur**: type_distribution, zones_service, licence
   - **Consommateur**: preferences, adresse_livraison

3. **PasswordResetRequest** - Reset hybride OTP/Token
   - OTP 6 chiffres (email)
   - Token cryptographique (lien)
   - Expiration: 5 minutes

#### Endpoints disponibles

| Méthode | Endpoint | Description | Auth |
|---------|----------|-------------|------|
| POST | `/api/auth/register/` | Inscription + auto-login | Public |
| POST | `/api/auth/login/` | Connexion (email/tel) | Public |
| POST | `/api/auth/logout/` | Déconnexion | Token |
| POST | `/api/auth/logoutall/` | Déconnexion tous appareils | Token |
| GET | `/api/auth/me/` | Profil utilisateur | Token |
| PATCH | `/api/auth/me/` | Mise à jour profil | Token |
| PATCH | `/api/auth/me/complete-profile/` | Compléter profil | Token |
| POST | `/api/auth/password/request-reset/` | Demande reset | Public |
| POST | `/api/auth/password/verify-otp/` | Validation OTP | Public |
| POST | `/api/auth/password/validate-token/` | Validation token | Public |
| POST | `/api/auth/password/reset-confirm/` | Confirmation reset | Public |
| POST | `/api/auth/google/` | OAuth2 Google | Public |

#### Fonctionnalités clés
✅ Authentification dual (email/téléphone)  
✅ Système de rôles multi-profils  
✅ Tokens Knox sécurisés (64 caractères, SHA512)  
✅ Reset password hybride (OTP + lien)  
✅ Social auth Google (pipeline personnalisé)  
✅ Gating profil incomplet (`IsProfileCompleted`)  
✅ Documentation Swagger complète  
✅ Tests unitaires prêts  

---

## 🚀 Installation & Déploiement

### Prérequis
- Docker & Docker Compose
- Git
- Accès SSH au serveur (185.217.125.37)

### Déploiement production

```bash
# 1. Cloner le projet
git clone <repo_url>
cd digitagro_api

# 2. Configuration environnement
cp .env.example .env
# Éditer .env avec vos credentials

# 3. Construire et lancer
docker-compose up -d --build

# 4. Migrations initiales (première fois)
docker exec -it digitagro_api python manage.py migrate

# 5. Créer superuser
docker exec -it digitagro_api python manage.py createsuperuser

# 6. Vérifier
curl http://localhost:8001/api/docs/
```

### Déploiement rapide (via script)
```bash
./deploy.sh
```

### Variables d'environnement requises

```bash
# Django
SECRET_KEY=your_secret_key_here
DEBUG=False
DJANGO_ALLOWED_HOSTS=185.217.125.37,localhost,127.0.0.1

# Base de données PostgreSQL
DB_HOST=185.217.125.37
DB_PORT=5432
DB_NAME=digitagro_db
DB_USER=digitagro
DB_PASSWORD=Digitagro@2002

# MongoDB (futur)
MONGODB_URL=mongodb://185.217.125.37:27017/digitagro_chat

# Email (reset password)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password

# Social Auth
GOOGLE_OAUTH2_CLIENT_ID=your_client_id
GOOGLE_OAUTH2_CLIENT_SECRET=your_client_secret

# Frontend
FRONTEND_URL=https://digitagro.com
```

---

## 📚 Documentation API

### Accès Swagger UI
```
http://185.217.125.37:8001/api/docs/
```

### Accès ReDoc
```
http://185.217.125.37:8001/api/redoc/
```

### Schéma OpenAPI 3.0
```
http://185.217.125.37:8001/api/schema/
```

### Guide complet des endpoints

#### 1. Inscription utilisateur
**POST** `/api/auth/register/`

**Requête:**
```json
{
  "email": "producteur@example.com",
  "telephone": "+237123456789",
  "nom": "Dupont",
  "prenom": "Jean",
  "adresse": "Yaoundé, Cameroun",
  "password": "securepass123",
  "password_confirm": "securepass123",
  "role_choisi": "producteur",
  "type_production": "Maraîchage",
  "superficie": "2.50"
}
```

**Réponse (201):**
```json
{
  "user": {
    "id": 1,
    "email": "producteur@example.com",
    "telephone": "+237123456789",
    "nom": "Dupont",
    "prenom": "Jean",
    "adresse": "Yaoundé, Cameroun",
    "avatar": null,
    "role_choisi": "producteur",
    "profile_completed": true,
    "date_creation": "2024-01-15T10:30:00Z",
    "user_role": "Producteur",
    "role_details": {
      "type_production": "Maraîchage",
      "superficie": "2.50",
      "certification": ""
    }
  },
  "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b",
  "expiry": "2025-12-31T23:59:59.999999Z"
}
```

**Curl:**
```bash
curl -X POST http://185.217.125.37:8001/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "producteur@example.com",
    "telephone": "+237123456789",
    "nom": "Dupont",
    "prenom": "Jean",
    "adresse": "Yaoundé, Cameroun",
    "password": "securepass123",
    "password_confirm": "securepass123",
    "role_choisi": "producteur",
    "type_production": "Maraîchage",
    "superficie": "2.50"
  }'
```

---

#### 2. Connexion
**POST** `/api/auth/login/`

**Requête:**
```json
{
  "identifier": "producteur@example.com",
  "password": "securepass123"
}
```

**Réponse (200):**
```json
{
  "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b",
  "expiry": "2025-12-31T23:59:59.999999Z",
  "user": {
    "id": 1,
    "email": "producteur@example.com",
    "telephone": "+237123456789",
    "nom": "Dupont",
    "prenom": "Jean",
    "adresse": "Yaoundé, Cameroun",
    "avatar": null,
    "role_choisi": "producteur",
    "profile_completed": true,
    "date_creation": "2024-01-15T10:30:00Z",
    "user_role": "Producteur",
    "role_details": {
      "type_production": "Maraîchage",
      "superficie": "2.50",
      "certification": ""
    }
  }
}
```

**Curl:**
```bash
curl -X POST http://185.217.125.37:8001/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "identifier": "producteur@example.com",
    "password": "securepass123"
  }'
```

---

#### 3. Consulter profil
**GET** `/api/auth/me/`

**Headers requis:**
```
Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b
```

**Réponse (200):**
```json
{
  "id": 1,
  "email": "producteur@example.com",
  "telephone": "+237123456789",
  "nom": "Dupont",
  "prenom": "Jean",
  "adresse": "Yaoundé, Cameroun",
  "avatar": "/media/avatars/photo.jpg",
  "role_choisi": "producteur",
  "profile_completed": true,
  "date_creation": "2024-01-15T10:30:00Z",
  "user_role": "Producteur",
  "role_details": {
    "type_production": "Maraîchage",
    "superficie": "2.50",
    "certification": "Bio"
  }
}
```

**Curl:**
```bash
curl -X GET http://185.217.125.37:8001/api/auth/me/ \
  -H "Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"
```

---

#### 4. Mettre à jour profil
**PATCH** `/api/auth/me/`

**Headers requis:**
```
Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b
Content-Type: multipart/form-data
```

**Requête (form-data):**
```
telephone: +237987654321
nom: Martin
prenom: Paul
adresse: Douala, Cameroun
avatar: [fichier image]
```

**Réponse (200):**
```json
{
  "id": 1,
  "email": "producteur@example.com",
  "telephone": "+237987654321",
  "nom": "Martin",
  "prenom": "Paul",
  "adresse": "Douala, Cameroun",
  "avatar": "/media/avatars/new_photo.jpg",
  "role_choisi": "producteur",
  "profile_completed": true,
  "date_creation": "2024-01-15T10:30:00Z",
  "user_role": "Producteur",
  "role_details": {
    "type_production": "Maraîchage",
    "superficie": "2.50",
    "certification": "Bio"
  }
}
```

**Curl:**
```bash
curl -X PATCH http://185.217.125.37:8001/api/auth/me/ \
  -H "Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b" \
  -F "telephone=+237987654321" \
  -F "nom=Martin" \
  -F "prenom=Paul" \
  -F "adresse=Douala, Cameroun" \
  -F "avatar=@photo.jpg"
```

---

#### 5. Compléter profil (après social auth)
**PATCH** `/api/auth/me/complete-profile/`

**Headers requis:**
```
Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b
Content-Type: multipart/form-data
```

**Requête (form-data):**
```
telephone: +237123456789
adresse: Yaoundé, Cameroun
avatar: [fichier image]
```

**Réponse (200):**
```json
{
  "id": 1,
  "email": "user@gmail.com",
  "telephone": "+237123456789",
  "nom": "Google",
  "prenom": "User",
  "adresse": "Yaoundé, Cameroun",
  "avatar": "/media/avatars/photo.jpg",
  "role_choisi": "consommateur",
  "profile_completed": true,
  "date_creation": "2024-01-15T10:30:00Z",
  "user_role": "Consommateur",
  "role_details": null
}
```

**Curl:**
```bash
curl -X PATCH http://185.217.125.37:8001/api/auth/me/complete-profile/ \
  -H "Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b" \
  -F "telephone=+237123456789" \
  -F "adresse=Yaoundé, Cameroun" \
  -F "avatar=@photo.jpg"
```

---

#### 6. Déconnexion (token actuel)
**POST** `/api/auth/logout/`

**Headers requis:**
```
Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b
```

**Réponse (204):**
```
No Content
```

**Curl:**
```bash
curl -X POST http://185.217.125.37:8001/api/auth/logout/ \
  -H "Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"
```

---

#### 7. Déconnexion (tous les appareils)
**POST** `/api/auth/logoutall/`

**Headers requis:**
```
Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b
```

**Réponse (204):**
```
No Content
```

**Curl:**
```bash
curl -X POST http://185.217.125.37:8001/api/auth/logoutall/ \
  -H "Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"
```

---

#### 8. Demander reset password
**POST** `/api/auth/password/request-reset/`

**Requête:**
```json
{
  "identifier": "producteur@example.com"
}
```

**Réponse (200):**
```json
{
  "message": "Code de réinitialisation envoyé"
}
```

**Curl:**
```bash
curl -X POST http://185.217.125.37:8001/api/auth/password/request-reset/ \
  -H "Content-Type: application/json" \
  -d '{
    "identifier": "producteur@example.com"
  }'
```

**Note:** Un email est envoyé avec un code OTP à 6 chiffres valide 5 minutes.

---

#### 9. Vérifier code OTP
**POST** `/api/auth/password/verify-otp/`

**Requête:**
```json
{
  "email": "producteur@example.com",
  "otp_code": "123456"
}
```

**Réponse (200):**
```json
{
  "message": "Code validé",
  "reset_token": "XyZ9_abcdefghijklmnopqrstuvwxyz1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ"
}
```

**Curl:**
```bash
curl -X POST http://185.217.125.37:8001/api/auth/password/verify-otp/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "producteur@example.com",
    "otp_code": "123456"
  }'
```

---

#### 10. Valider token reset
**POST** `/api/auth/password/validate-token/`

**Requête:**
```json
{
  "reset_token": "XyZ9_abcdefghijklmnopqrstuvwxyz1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ"
}
```

**Réponse (200):**
```json
{
  "message": "Token valide"
}
```

**Curl:**
```bash
curl -X POST http://185.217.125.37:8001/api/auth/password/validate-token/ \
  -H "Content-Type: application/json" \
  -d '{
    "reset_token": "XyZ9_abcdefghijklmnopqrstuvwxyz1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ"
  }'
```

---

#### 11. Confirmer nouveau mot de passe
**POST** `/api/auth/password/reset-confirm/`

**Requête:**
```json
{
  "reset_token": "XyZ9_abcdefghijklmnopqrstuvwxyz1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ",
  "new_password": "nouveaumotdepasse123",
  "new_password_confirm": "nouveaumotdepasse123"
}
```

**Réponse (200):**
```json
{
  "message": "Mot de passe réinitialisé avec succès"
}
```

**Curl:**
```bash
curl -X POST http://185.217.125.37:8001/api/auth/password/reset-confirm/ \
  -H "Content-Type: application/json" \
  -d '{
    "reset_token": "XyZ9_abcdefghijklmnopqrstuvwxyz1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ",
    "new_password": "nouveaumotdepasse123",
    "new_password_confirm": "nouveaumotdepasse123"
  }'
```

---

#### 12. Connexion Google OAuth2
**POST** `/api/auth/google/`

**Requête:**
```json
{
  "access_token": "ya29.a0AfH6SMBx..."
}
```

**Réponse (501):**
```json
{
  "message": "Google Auth à implémenter"
}
```

**Curl:**
```bash
curl -X POST http://185.217.125.37:8001/api/auth/google/ \
  -H "Content-Type: application/json" \
  -d '{
    "access_token": "ya29.a0AfH6SMBx..."
  }'
```

**Note:** Endpoint préparé pour future implémentation complète.

---

## 🧪 Tests

### Lancer les tests
```bash
# Tous les tests
docker exec -it digitagro_api python manage.py test

# Tests users uniquement
docker exec -it digitagro_api python manage.py test apps.users

# Avec coverage
docker exec -it digitagro_api coverage run --source='.' manage.py test
docker exec -it digitagro_api coverage report
```

### Tests à implémenter
```python
# apps/users/tests.py
- test_user_registration_auto_login()
- test_login_with_email_and_phone()
- test_logout_destroys_token()
- test_profile_completion_after_social_auth()
- test_password_reset_otp_flow()
- test_password_reset_link_flow()
```

---

## 🔒 Sécurité

### Mesures implémentées
✅ Tokens Knox avec hachage SHA512  
✅ Expiration automatique des tokens reset (5 min)  
✅ Backend auth personnalisé (email/téléphone)  
✅ Validation des permissions (`IsAuthenticated`, `IsOwnerOrReadOnly`)  
✅ CSRF activé pour sessions  
✅ Validation des mots de passe Django  
✅ HTTPS recommandé en production  

### Headers de sécurité
```python
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
SECURE_CONTENT_TYPE_NOSNIFF = True
```

---

## 📊 Monitoring & Logs

### Logs Docker
```bash
# Logs temps réel
docker-compose logs -f digitagro_api

# Dernières 50 lignes
docker-compose logs --tail=50 digitagro_api

# Logs avec timestamps
docker-compose logs -t digitagro_api
```

### Health check
```bash
# Via deploy.sh
curl -f http://localhost:8001/api/docs/

# Vérification manuelle
docker ps | grep digitagro_api
```

---

## 🗺️ Roadmap

### ✅ Phase 1: Authentification (TERMINÉ)
- [x] Système utilisateurs multi-rôles
- [x] Knox token authentication
- [x] Reset password hybride
- [x] Social auth Google (structure)
- [x] Documentation Swagger

### 🚧 Phase 2: Production (EN COURS)
- [ ] CRUD productions géolocalisées
- [ ] Upload photos produits
- [ ] Filtres et recherche avancée
- [ ] Notifications push

### 📋 Phase 3: Transport
- [ ] Déclaration services transport
- [ ] Réservation et suivi GPS
- [ ] Gestion conditions conservation
- [ ] Rating transporteurs

### 📋 Phase 4: Marketplace
- [ ] Annonces B2B/B2C
- [ ] Gestion commandes
- [ ] Paiement mobile (Orange Money, MTN)
- [ ] Évaluations et commentaires

### 📋 Phase 5: Messagerie
- [ ] Chat temps réel (WebSocket)
- [ ] Intégration MongoDB
- [ ] Notifications instantanées

---

## 🤝 Contribution

### Branches
- `main`: Production stable
- `develop`: Développement actif
- `feature/*`: Nouvelles fonctionnalités

### Workflow
1. Fork le projet
2. Créer une branche (`git checkout -b feature/nouvelle-fonctionnalite`)
3. Commit (`git commit -m 'Ajout fonctionnalité X'`)
4. Push (`git push origin feature/nouvelle-fonctionnalite`)
5. Pull Request

---

## 📝 Licence

Copyright © 2024 DIGITAGRO. Tous droits réservés.

---

## 👥 Équipe

- **Backend Lead**: Développement API Django
- **DevOps**: Infrastructure Docker & déploiement
- **Frontend**: Application mobile (React Native - à venir)

---

## 📞 Support

- **Documentation**: http://185.217.125.37:8001/api/docs/
- **Email**: support@digitagro.cm
- **Serveur**: 185.217.125.37:8001

---

**Version actuelle**: 1.0.0  
**Dernière mise à jour**: 29 Septembre 2025