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
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser doit avoir is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser doit avoir is_superuser=True.')
            
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ('producteur', 'Producteur'),
        ('transporteur', 'Transporteur'),
        ('transformateur', 'Transformateur'),
        ('distributeur', 'Distributeur'),
        ('consommateur', 'Consommateur'),
    ]
    
    email = models.EmailField(unique=True)
    telephone = models.CharField(max_length=20, unique=True, null=True, blank=True)
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    adresse = models.CharField(max_length=255)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    role_choisi = models.CharField(max_length=20, choices=ROLE_CHOICES, default='consommateur')
    profile_completed = models.BooleanField(default=False)
    date_creation = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nom', 'prenom']

    class Meta:
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'

    def __str__(self):
        return f"{self.prenom} {self.nom} ({self.email})"

    def get_role(self):
        """Retourne le rôle principal de l'utilisateur avec algorithme récursif"""
        def chercher_role_recursif(roles_possibles, index=0):
            if index >= len(roles_possibles):
                return 'Consommateur'
            
            role = roles_possibles[index]
            if hasattr(self, role):
                return role.capitalize()
            
            return chercher_role_recursif(roles_possibles, index + 1)
        
        roles = ['producteur', 'transporteur', 'transformateur', 'distributeur']
        return chercher_role_recursif(roles)

    def get_full_name(self):
        return f"{self.prenom} {self.nom}"

    def get_short_name(self):
        return self.prenom


# ==================== MODÈLES DE RÔLES SPÉCIFIQUES ====================

class Producteur(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, primary_key=True)
    type_production = models.CharField(max_length=100)  # Maraîchage, Élevage, etc.
    superficie = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    certification = models.CharField(max_length=100, blank=True)  # Bio, etc.
    
    class Meta:
        verbose_name = 'Producteur'
        verbose_name_plural = 'Producteurs'
    
    def __str__(self):
        return f"Producteur: {self.user.get_full_name()}"
    
    def calculer_productions_recursif(self, productions_list=None, index=0):
        """Calcule le nombre total de productions avec algorithme récursif"""
        if productions_list is None:
            productions_list = list(self.production_set.all())
        
        if index >= len(productions_list):
            return 0
        
        return 1 + self.calculer_productions_recursif(productions_list, index + 1)


class Transporteur(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, primary_key=True)
    type_vehicule = models.CharField(max_length=100)
    capacite = models.DecimalField(max_digits=10, decimal_places=2)  # en tonnes
    permis_transport = models.CharField(max_length=50)
    conditions_conservation = models.TextField(blank=True)  # Chaîne du froid, etc.
    
    class Meta:
        verbose_name = 'Transporteur'
        verbose_name_plural = 'Transporteurs'
    
    def __str__(self):
        return f"Transporteur: {self.user.get_full_name()}"
    
    def calculer_trajets_recursif(self, trajets_list=None, index=0):
        """Calcule le nombre de trajets effectués avec récursivité"""
        if trajets_list is None:
            trajets_list = list(self.servicetransport_set.all())
        
        if index >= len(trajets_list):
            return 0
        
        return 1 + self.calculer_trajets_recursif(trajets_list, index + 1)


class Transformateur(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, primary_key=True)
    type_transformation = models.CharField(max_length=100)
    certification = models.CharField(max_length=100, blank=True)
    capacite_traitement = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        verbose_name = 'Transformateur'
        verbose_name_plural = 'Transformateurs'
    
    def __str__(self):
        return f"Transformateur: {self.user.get_full_name()}"


class Distributeur(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, primary_key=True)
    type_distribution = models.CharField(max_length=100)
    zones_service = models.TextField()  # JSON des zones couvertes
    licence = models.CharField(max_length=50)
    
    class Meta:
        verbose_name = 'Distributeur'
        verbose_name_plural = 'Distributeurs'
    
    def __str__(self):
        return f"Distributeur: {self.user.get_full_name()}"


class Consommateur(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, primary_key=True)
    preferences = models.TextField(blank=True)  # JSON des préférences
    adresse_livraison = models.TextField()
    
    class Meta:
        verbose_name = 'Consommateur'
        verbose_name_plural = 'Consommateurs'
    
    def __str__(self):
        return f"Consommateur: {self.user.get_full_name()}"
    
    def calculer_commandes_recursif(self, commandes_list=None, index=0):
        """Calcule le nombre de commandes avec récursivité"""
        if commandes_list is None:
            commandes_list = list(self.commande_set.all())
        
        if index >= len(commandes_list):
            return 0
        
        return 1 + self.calculer_commandes_recursif(commandes_list, index + 1)


class PasswordResetRequest(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    otp_code = models.CharField(max_length=6, db_index=True)
    reset_token = models.CharField(max_length=100, unique=True, db_index=True)
    expires_at = models.DateTimeField()
    is_validated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Demande de réinitialisation'
        verbose_name_plural = 'Demandes de réinitialisation'
        
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
        return f"Reset request for {self.user.email} - {self.created_at}"