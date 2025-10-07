from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
import secrets
import string
from datetime import timedelta


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
        # Active tous les rôles pour le superuser
        extra_fields.setdefault('is_producteur', True)
        extra_fields.setdefault('is_transporteur', True)
        extra_fields.setdefault('is_transformateur', True)
        extra_fields.setdefault('is_distributeur', True)
        
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    # Champs de base
    email = models.EmailField(unique=True)
    telephone = models.CharField(max_length=20, unique=True, null=True, blank=True)
    nom = models.CharField(max_length=100, null=True, blank=True)  # Nullable pour compatibilité
    prenom = models.CharField(max_length=100, null=True, blank=True)  # Nullable pour compatibilité
    adresse = models.CharField(max_length=255, null=True, blank=True)  # Nullable pour compatibilité
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    
    # Système de rôles booléens
    is_consommateur = models.BooleanField(default=True)  # Toujours True
    is_producteur = models.BooleanField(default=False)
    is_transporteur = models.BooleanField(default=False)
    is_transformateur = models.BooleanField(default=False)
    is_distributeur = models.BooleanField(default=False)
    
    # Dates d'activation des rôles (traçabilité)
    producteur_activated_at = models.DateTimeField(null=True, blank=True)
    transporteur_activated_at = models.DateTimeField(null=True, blank=True)
    transformateur_activated_at = models.DateTimeField(null=True, blank=True)
    distributeur_activated_at = models.DateTimeField(null=True, blank=True)
    
    # Vérification des rôles professionnels
    is_producteur_verified = models.BooleanField(default=False)
    is_transporteur_verified = models.BooleanField(default=False)
    is_transformateur_verified = models.BooleanField(default=False)
    is_distributeur_verified = models.BooleanField(default=False)
    
    # Champs système
    profile_completed = models.BooleanField(default=False)
    date_creation = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    
    # DEPRECATED - Conservé pour compatibilité
    role_choisi = models.CharField(max_length=20, null=True, blank=True, 
                                  help_text="DEPRECATED - Utiliser les booléens is_*")

    objects = CustomUserManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  # Aucun champ requis pour flexibilité

    class Meta:
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['telephone']),
            models.Index(fields=['is_producteur']),
            models.Index(fields=['is_transporteur']),
        ]

    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"

    def get_full_name(self):
        if self.nom and self.prenom:
            return f"{self.prenom} {self.nom}"
        return self.email.split('@')[0]

    def get_short_name(self):
        return self.prenom or self.email.split('@')[0]
    
    def get_active_roles(self):
        """Retourne la liste des rôles actifs (optimisé)"""
        role_checks = [
            ('consommateur', self.is_consommateur),
            ('producteur', self.is_producteur),
            ('transporteur', self.is_transporteur),
            ('transformateur', self.is_transformateur),
            ('distributeur', self.is_distributeur)
        ]
        return [role for role, is_active in role_checks if is_active]
    
    def activate_role(self, role_name):
        """Active un rôle et enregistre la date d'activation"""
        role_field = f'is_{role_name}'
        if hasattr(self, role_field):
            setattr(self, role_field, True)
            setattr(self, f'{role_name}_activated_at', timezone.now())
            self.save(update_fields=[role_field, f'{role_name}_activated_at'])
            return True
        return False
    
    def check_profile_requirements(self):
        """Vérifie si le profil minimum est complété"""
        required = ['nom', 'prenom', 'telephone', 'adresse']
        return all(getattr(self, field) for field in required)


# ==================== PROFILS DE RÔLES (OneToOne) ====================

class Producteur(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, primary_key=True)
    type_production = models.CharField(max_length=100, blank=True)
    superficie = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    certification = models.CharField(max_length=100, blank=True)
    
    # Stats cache (éviter les COUNT)
    total_productions = models.IntegerField(default=0)
    last_production_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Profil Producteur'
        verbose_name_plural = 'Profils Producteurs'
    
    def __str__(self):
        return f"Producteur: {self.user.get_full_name()}"


class Transporteur(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, primary_key=True)
    type_vehicule = models.CharField(max_length=100, blank=True)
    capacite = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    permis_transport = models.CharField(max_length=50, blank=True)
    conditions_conservation = models.TextField(blank=True)
    
    # Stats cache
    total_trajets = models.IntegerField(default=0)
    note_moyenne = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    
    class Meta:
        verbose_name = 'Profil Transporteur'
        verbose_name_plural = 'Profils Transporteurs'
    
    def __str__(self):
        return f"Transporteur: {self.user.get_full_name()}"


class Transformateur(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, primary_key=True)
    type_transformation = models.CharField(max_length=100, blank=True)
    certification = models.CharField(max_length=100, blank=True)
    capacite_traitement = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    class Meta:
        verbose_name = 'Profil Transformateur'
        verbose_name_plural = 'Profils Transformateurs'
    
    def __str__(self):
        return f"Transformateur: {self.user.get_full_name()}"


class Distributeur(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, primary_key=True)
    type_distribution = models.CharField(max_length=100,  blank=True)
    zones_service = models.TextField(blank=True)
    licence = models.CharField(max_length=50, blank=True)
    
    class Meta:
        verbose_name = 'Profil Distributeur'
        verbose_name_plural = 'Profils Distributeurs'
    
    def __str__(self):
        return f"Distributeur: {self.user.get_full_name()}"


class Consommateur(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, primary_key=True)
    preferences = models.JSONField(default=dict, blank=True)
    adresse_livraison = models.TextField(blank=True)
    
    # Stats cache
    total_commandes = models.IntegerField(default=0)
    
    class Meta:
        verbose_name = 'Profil Consommateur'
        verbose_name_plural = 'Profils Consommateurs'
    
    def __str__(self):
        return f"Consommateur: {self.user.get_full_name()}"


class PasswordResetRequest(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    otp_code = models.CharField(max_length=6, db_index=True)
    reset_token = models.CharField(max_length=100, unique=True, db_index=True)
    expires_at = models.DateTimeField(db_index=True)  # Index pour requêtes rapides
    is_validated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Demande de réinitialisation'
        verbose_name_plural = 'Demandes de réinitialisation'
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['user', 'is_validated']),
        ]
        
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
        
    def __str__(self):
        return f"Reset for {self.user.email} - {self.created_at}"