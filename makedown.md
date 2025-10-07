# Fiche Technique Expert : Module User DIGITAGRO

**Spécifications Techniques Détaillées** : Authentification, Profils, JWT, Social Auth, Reset Hybride

## 1. Contexte du Projet et Prérequis Techniques

Le projet DIGITAGRO vise la modernisation du secteur agrosylvopastoral au Cameroun via une application mobile et une API REST robuste. Le module Utilisateur constitue la pierre angulaire de cette architecture, gérant l'identification sécurisée et les identités multi-rôles (Producteur, Transporteur, etc.).

### 1.1. Stack Technique et Versions

| Composant | Version Cible | Rôle |
|-----------|---------------|------|
| **Framework** | Django (5.0+) | Backend Core, Modèles de données |
| **API** | Django REST Framework (DRF) | Couche API REST pour sérialisation et vues |
| **Base de Données Principale** | PostgreSQL | Stockage transactionnel et structuré |
| **Base de Données Secondaire** | MongoDB | Base non-relationnelle pour Chat/Messagerie |
| **Authentification** | djangorestframework-simplejwt | Gestion des Tokens JWT (Access & Refresh) |
| **Documentation** | drf-spectacular | Génération de schémas OpenAPI 3.0 pour Swagger UI |
| **Social Auth** | social-auth-app-django | Authentification Google OAuth2 |

### 1.2. Architecture de Conteneurisation (Docker)

Le déploiement utilise Docker avec `docker-compose` pour orchestrer quatre services critiques :

- **web (Django/Gunicorn)** : Conteneur applicatif avec serveur WSGI
- **db (PostgreSQL)** : Service base de données principal avec volumes nommés
- **mongo (MongoDB)** : Service pour le module de chat futur
- **nginx (Reverse Proxy)** : Gestion des requêtes, SSL, fichiers statiques

**Configuration docker-compose.yml :**
```yaml
version: '3.8'
services:
  web:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - db
      - mongo
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/digitagro
      - MONGODB_URL=mongodb://mongo:27017/digitagro_chat
    volumes:
      - ./media:/app/media
      - ./static:/app/static

  db:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=digitagro
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password

  mongo:
    image: mongo:6
    volumes:
      - mongo_data:/data/db

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - web
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf

volumes:
  postgres_data:
  mongo_data:
```

**Sécurité** : Toutes les configurations sensibles via variables d'environnement (SECRET_KEY, identifiants DB) avec `django-environ`.

## 2. Modèle de Données et Manager

### 2.1. Choix du Modèle Utilisateur

**Architecture** : Modèle utilisateur personnalisé héritant d'`AbstractBaseUser` pour supporter l'authentification via email OU téléphone.

#### Implémentation du Modèle CustomUser

```python
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email requis')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractBaseUser):
    email = models.EmailField(unique=True)  # USERNAME_FIELD
    telephone = models.CharField(max_length=20, unique=True, null=True, blank=True)
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    adresse = models.CharField(max_length=255)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    profile_completed = models.BooleanField(default=False)
    date_creation = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nom', 'prenom']

    def get_role(self):
        """Retourne le rôle principal de l'utilisateur"""
        if hasattr(self, 'producteur'):
            return 'Producteur'
        elif hasattr(self, 'transporteur'):
            return 'Transporteur'
        # ... autres rôles
        return 'Consommateur'
```

#### Schéma du Modèle CustomUser

| Attribut | Type Django | Contraintes | Rôle / Notes |
|----------|-------------|-------------|--------------|
| `email` | EmailField | Unique, Requis | USERNAME_FIELD de Django |
| `telephone` | CharField(20) | Unique, null=True, blank=True | Identifiant de connexion alternatif |
| `nom` | CharField | Requis | Nom de famille |
| `prenom` | CharField | Requis | Prénom |
| `adresse` | CharField | Requis | Adresse physique |
| `avatar` | ImageField | Optionnel | Photo de profil |
| `profile_completed` | BooleanField | Default: False | Indicateur d'achèvement forcé du profil |
| `date_creation` | DateTimeField | Auto-Add | Date de création du compte |

### 2.2. Manager et Backend d'Authentification Personnalisé

#### Backend d'Authentification Flexible

```python
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q

class CustomAuthenticationBackend(ModelBackend):
    """Permet connexion via email OU téléphone"""
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = CustomUser.objects.get(
                Q(email=username) | Q(telephone=username)
            )
            if user.check_password(password):
                return user
        except CustomUser.DoesNotExist:
            return None
        return None
```

**Configuration dans settings.py :**
```python
AUTHENTICATION_BACKENDS = [
    'apps.users.backends.CustomAuthenticationBackend',
    'django.contrib.auth.backends.ModelBackend',
]
```

## 3. Flux d'Authentification Standard (JWT)

### 3.1. Configuration JWT

```python
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'TOKEN_OBTAIN_SERIALIZER': 'apps.users.serializers.CustomTokenObtainPairSerializer',
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
}
```

### 3.2. Endpoint d'Enregistrement

**POST /api/auth/register/**

**Input :**
```json
{
  "email": "user@example.com",
  "telephone": "+237123456789", 
  "nom": "Nom",
  "prenom": "Prénom",
  "adresse": "Adresse complète",
  "password": "motdepasse123"
}
```

**Output (201) :**
```json
{
  "user": {
    "id": 1,
    "email": "user@example.com",
    "nom": "Nom",
    "prenom": "Prénom",
    "profile_completed": true
  },
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Implémentation :**
```python
class UserRegistrationView(CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Auto-génération des tokens JWT
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserProfileSerializer(user).data,
            'access': str(refresh.access_token),
            'refresh': str(refresh)
        }, status=status.HTTP_201_CREATED)
```

### 3.3. Endpoint de Connexion

**POST /api/auth/login/**

**Input :**
```json
{
  "identifier": "user@example.com",  // email OU téléphone
  "password": "motdepasse123"
}
```

**Implémentation :**
```python
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = 'identifier'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['identifier'] = serializers.CharField()
        del self.fields['username']

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        # Claims personnalisés requis
        token['user_id'] = user.id
        token['date_connexion'] = int(timezone.now().timestamp())
        token['profile_completed'] = user.profile_completed
        token['user_role'] = user.get_role()
        
        return token

    def validate(self, attrs):
        identifier = attrs.get('identifier')
        password = attrs.get('password')
        
        if identifier and password:
            user = authenticate(
                request=self.context.get('request'),
                username=identifier,
                password=password
            )
            if not user:
                raise serializers.ValidationError('Identifiants invalides')
            
            attrs['user'] = user
            return attrs
        
        raise serializers.ValidationError('Identifier et password requis')
```

### 3.4. Endpoint de Rafraîchissement

**POST /api/auth/token/refresh/**

- Utilise `TokenRefreshView` standard
- Configuration `ROTATE_REFRESH_TOKENS: True` pour sécurité renforcée

## 4. Personnalisation Avancée du JWT

### 4.1. Payload JWT Personnalisé (Access Token)

| Claim | Type | Valeur Exemple | Notes |
|-------|------|----------------|-------|
| `user_id` | Integer | 123 | Identifiant utilisateur |
| `date_connexion` | Integer (Timestamp) | 1700000000 | **Claim personnalisé requis** |
| `user_role` | String | "Producteur" | Rôle principal (optimisation permissions) |
| `profile_completed` | Boolean | True/False | Gating d'accès post-Social Auth |

## 5. Flux d'Authentification Sociale (Google OAuth2)

### 5.1. Configuration

**Installation et Configuration :**
```python
# settings.py
INSTALLED_APPS = [
    # ...
    'social_django',
]

AUTHENTICATION_BACKENDS = [
    'social_core.backends.google.GoogleOAuth2',
    'apps.users.backends.CustomAuthenticationBackend',
]

SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = env('GOOGLE_OAUTH2_CLIENT_ID')
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = env('GOOGLE_OAUTH2_CLIENT_SECRET')

SOCIAL_AUTH_PIPELINE = (
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.auth_allowed',
    'social_core.pipeline.social_auth.social_user',
    'social_core.pipeline.user.get_username',
    'social_core.pipeline.user.create_user',
    'apps.users.pipeline.check_profile_completion',  # Custom pipeline
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    'social_core.pipeline.user.user_details',
)
```

### 5.2. Endpoint Social Auth

**POST /api/auth/google/**

**Input :**
```json
{
  "access_token": "google_access_token_from_frontend"
}
```

### 5.3. Stratégie d'Achèvement Forcé du Profil

**Pipeline personnalisé :**
```python
def check_profile_completion(strategy, details, user=None, *args, **kwargs):
    if user:
        required_fields = ['telephone', 'adresse', 'nom', 'prenom']
        missing_fields = [field for field in required_fields if not getattr(user, field)]
        
        if missing_fields:
            user.profile_completed = False
        else:
            user.profile_completed = True
        user.save()
```

**Permission IsProfileCompleted :**
```python
class IsProfileCompleted(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.profile_completed
    
    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)
```

### 5.4. Endpoint d'Achèvement

**PATCH /api/users/me/complete-profile/**

```python
class CompleteProfileView(UpdateAPIView):
    serializer_class = ProfileCompletionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        # Marquer le profil comme complété
        request.user.profile_completed = True
        request.user.save()
        return response
```

## 6. Gestion du Profil Utilisateur

### 6.1. Consultation du Profil

**GET /api/users/me/**

**Réponse :**
```json
{
  "id": 1,
  "email": "user@example.com",
  "telephone": "+237123456789",
  "nom": "Nom",
  "prenom": "Prénom",
  "adresse": "Adresse",
  "avatar": "/media/avatars/photo.jpg",
  "profile_completed": true,
  "date_creation": "2024-01-15T10:30:00Z",
  "user_role": "Producteur"
}
```

### 6.2. Sérializers

```python
class UserProfileSerializer(serializers.ModelSerializer):
    user_role = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'telephone', 'nom', 'prenom', 'adresse', 
                 'avatar', 'profile_completed', 'date_creation', 'user_role']
        read_only_fields = ['id', 'email', 'date_creation', 'profile_completed']
    
    def get_user_role(self, obj):
        return obj.get_role()

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    
    class Meta:
        model = CustomUser
        fields = ['email', 'telephone', 'nom', 'prenom', 'adresse', 'password']
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        user = CustomUser.objects.create_user(password=password, **validated_data)
        # Marquer automatiquement comme complété si tous les champs requis sont présents
        user.profile_completed = True
        user.save()
        return user
```

## 7. Flux de Récupération de Mot de Passe (Hybride OTP & Lien)

### 7.1. Modèle Temporaire PasswordResetRequest

```python
import secrets
import string

class PasswordResetRequest(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    otp_code = models.CharField(max_length=6, db_index=True)
    reset_token = models.CharField(max_length=100, unique=True, db_index=True)
    expires_at = models.DateTimeField()
    is_validated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        if not self.otp_code:
            self.otp_code = ''.join(secrets.choice(string.digits) for _ in range(6))
        if not self.reset_token:
            self.reset_token = secrets.token_urlsafe(64)
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=5)
        super().save(*args, **kwargs)
    
    @property
    def is_expired(self):
        return timezone.now() > self.expires_at
```

### 7.2. Endpoints Reset Password

**1. Demande de reset (POST /api/auth/password/request-reset/)**
```json
{
  "identifier": "user@example.com"  // email ou téléphone
}
```

**2. Validation OTP (POST /api/auth/password/verify-otp/)**
```json
{
  "email": "user@example.com",
  "otp_code": "123456"
}
```

**3. Validation Token (POST /api/auth/password/validate-token/)**
```json
{
  "reset_token": "long_crypto_token"
}
```

**4. Confirmation finale (POST /api/auth/password/reset-confirm/)**
```json
{
  "reset_token": "token_ou_email_si_otp_validé",
  "new_password": "nouveau_motdepasse123"
}
```

## 8. Configuration et Variables d'Environnement

```bash
# Django Core
SECRET_KEY=your_super_secret_key_here
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,digitagro.com

# Bases de données
DATABASE_URL=postgresql://user:password@db:5432/digitagro
MONGODB_URL=mongodb://mongo:27017/digitagro_chat

# JWT
JWT_SECRET_KEY=your_jwt_secret_key

# Google OAuth2
GOOGLE_OAUTH2_CLIENT_ID=your_google_client_id
GOOGLE_OAUTH2_CLIENT_SECRET=your_google_client_secret

# Email (pour OTP)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_email_password

# URLs Frontend (pour liens reset)
FRONTEND_URL=https://digitagro.com
```

## 9. Documentation Swagger/OpenAPI

### Configuration drf-spectacular

```python
SPECTACULAR_SETTINGS = {
    'TITLE': 'DIGITAGRO API',
    'DESCRIPTION': 'API REST pour la plateforme agrosylvopastorale DIGITAGRO',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'SCHEMA_PATH_PREFIX': '/api',
}
```

## 10. Synthèse des Endpoints

| Flux | Méthode | Endpoint | Sécurité | Notes |
|------|---------|----------|----------|-------|
| **Enregistrement** | POST | /api/auth/register/ | Public | Retourne JWT (Auto-login) |
| **Connexion Standard** | POST | /api/auth/login/ | Public | `identifier` + `password` |
| **Rafraîchissement** | POST | /api/auth/token/refresh/ | Public | Rotation activée |
| **Connexion Sociale** | POST | /api/auth/google/ | Public | Échange token Google |
| **Consulter Profil** | GET | /api/users/me/ | IsAuthenticated | JWT requis |
| **Mettre à Jour Profil** | PATCH | /api/users/me/ | IsAuthenticated | Mise à jour partielle |
| **Achèvement Forcé** | PATCH | /api/users/me/complete-profile/ | IsAuthenticated | `profile_completed=True` |
| **Reset - Demande** | POST | /api/auth/password/request-reset/ | Public | Initialise flux OTP/Lien |
| **Reset - Validation OTP** | POST | /api/auth/password/verify-otp/ | Public | Valide code alphanumérique |
| **Reset - Validation Token** | POST | /api/auth/password/validate-token/ | Public | Valide lien cryptographique |
| **Reset - Confirmation** | POST | /api/auth/password/reset-confirm/ | Public | Finalise réinitialisation |

## 11. Tests Recommandés

```python
class UserAuthTestCase(APITestCase):
    def test_user_registration_auto_login(self):
        """Test registration avec auto-génération JWT"""
        
    def test_login_with_email_and_phone(self):
        """Test connexion avec email ET téléphone"""
        
    def test_jwt_custom_claims(self):
        """Test présence des claims personnalisés"""
        
    def test_google_auth_profile_gating(self):
        """Test gating après inscription Google"""
        
    def test_password_reset_otp_flow(self):
        """Test flux reset avec OTP"""
        
    def test_password_reset_link_flow(self):
        """Test flux reset avec lien"""
```

## 12. Recommandations Architecturales

### Points Critiques

1. **Dualité de Connexion** : `AbstractBaseUser` + `CustomAuthenticationBackend` obligatoires
2. **Sécurité Post-Social Auth** : Mécanisme de gating via `IsProfileCompleted`
3. **Optimisation JWT** : Claims personnalisés (`profile_completed`, `user_role`) pour permissions sans état
4. **Reset Hybride** : Modèle temporaire unique pour cohérence des états

### Avantages de l'Architecture

- **Performance** : Vérification permissions sans requête DB (JWT stateless)
- **Sécurité** : Invalidation simultanée OTP/Lien, rotation tokens
- **UX** : Double option reset, auto-login post-inscription
- **Maintenabilité** : Logique centralisée, documentation OpenAPI complète
- **Scalabilité** : Architecture stateless adaptée au déploiement containerisé