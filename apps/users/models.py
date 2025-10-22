# apps/users/models.py
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
        extra_fields.setdefault('is_producteur', True)
        extra_fields.setdefault('is_transporteur', True)
        extra_fields.setdefault('is_transformateur', True)
        extra_fields.setdefault('is_distributeur', True)
        
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    # Champs de base
    email = models.EmailField(unique=True)
    telephone = models.CharField(max_length=20, unique=True, null=True, blank=True)
    nom = models.CharField(max_length=100, null=True, blank=True)
    prenom = models.CharField(max_length=100, null=True, blank=True)
    adresse = models.CharField(max_length=255, null=True, blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    
    # Système de rôles booléens
    is_consommateur = models.BooleanField(default=True)
    is_producteur = models.BooleanField(default=False)
    is_transporteur = models.BooleanField(default=False)
    is_transformateur = models.BooleanField(default=False)
    is_distributeur = models.BooleanField(default=False)
    
    # Dates d'activation des rôles
    producteur_activated_at = models.DateTimeField(null=True, blank=True)
    transporteur_activated_at = models.DateTimeField(null=True, blank=True)
    transformateur_activated_at = models.DateTimeField(null=True, blank=True)
    distributeur_activated_at = models.DateTimeField(null=True, blank=True)
    
    # Vérification des rôles professionnels
    is_producteur_verified = models.BooleanField(default=False)
    is_transporteur_verified = models.BooleanField(default=False)
    is_transformateur_verified = models.BooleanField(default=False)
    is_distributeur_verified = models.BooleanField(default=False)
    
    # ========== NOUVEAUX CHAMPS VÉRIFICATION SMS ==========
    phone_verified = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Téléphone vérifié par SMS"
    )
    phone_verified_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date de vérification du téléphone"
    )
    sms_attempts_count = models.IntegerField(
        default=0,
        help_text="Nombre de tentatives d'envoi SMS"
    )
    last_sms_attempt = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Dernière tentative d'envoi SMS"
    )
    
    # Champs système
    profile_completed = models.BooleanField(default=False)
    date_creation = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    
    # DEPRECATED
    role_choisi = models.CharField(
        max_length=20, 
        null=True, 
        blank=True,
        help_text="DEPRECATED - Utiliser les booléens is_*"
    )

    objects = CustomUserManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['telephone']),
            models.Index(fields=['is_producteur']),
            models.Index(fields=['is_transporteur']),
            models.Index(fields=['phone_verified']),  # Nouvel index
        ]

    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"

    def get_full_name(self):
        return f"{self.prenom} {self.nom}" if self.nom and self.prenom else self.email.split('@')[0]

    def get_short_name(self):
        return self.prenom or self.email.split('@')[0]
    
    def get_active_roles(self):
        """Retourne la liste des rôles actifs (optimisé avec list comprehension)"""
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
        return all(getattr(self, field) for field in ['nom', 'prenom', 'telephone', 'adresse'])
    
    # ========== NOUVELLES MÉTHODES VÉRIFICATION SMS ==========
    def can_request_sms(self):
        """
        Vérifie si l'utilisateur peut demander un nouveau SMS.
        Rate limit : 3 tentatives par heure.
        """
        if not self.last_sms_attempt:
            return True
        
        time_since_last = timezone.now() - self.last_sms_attempt
        
        # Reset compteur après 1 heure
        if time_since_last.total_seconds() > 3600:
            self.sms_attempts_count = 0
            self.save(update_fields=['sms_attempts_count'])
            return True
        
        # Limite 3 tentatives
        return self.sms_attempts_count < 3
    
    def get_active_badges(self):
        """
        Retourne tous les badges actifs et valides de l'utilisateur.
        Optimisé avec filter et list comprehension.
        """
        now = timezone.now()
        return self.badges.filter(
            is_active=True
        ).filter(
            models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=now)
        )
    
    def has_badge(self, badge_type):
        """Vérifie si l'utilisateur possède un badge actif"""
        return self.get_active_badges().filter(badge_type=badge_type).exists()
    
    def check_producer_requirements(self):
        """
        Vérifie les prérequis pour devenir producteur.
        
        OBLIGATOIRE :
        - Profil complété (nom, prénom, téléphone, adresse)
        - Téléphone vérifié par SMS
        
        Returns:
            tuple: (bool, str) - (autorisé, message_erreur)
        """
        if not self.check_profile_requirements():
            return False, "Complétez votre profil (nom, prénom, téléphone, adresse)"
        
        if not self.phone_verified:
            return False, "Vous devez vérifier votre numéro de téléphone par SMS"
        
        return True, ""


# ==================== NOUVEAU MODÈLE VÉRIFICATION SMS ====================

class PhoneVerification(models.Model):
    """
    Gestion des codes SMS de vérification.
    Expiration : 5 minutes
    Rate limit : 3 tentatives
    """
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='phone_verifications'
    )
    phone_number = models.CharField(
        max_length=20,
        help_text="Numéro à vérifier (format international)"
    )
    code = models.CharField(
        max_length=5,
        help_text="Code 5 chiffres"
    )
    
    # Sécurité
    expires_at = models.DateTimeField(
        db_index=True,
        help_text="Expiration 5 minutes"
    )
    verified = models.BooleanField(
        default=False,
        db_index=True
    )
    attempts = models.IntegerField(
        default=0,
        help_text="Nombre de tentatives de vérification"
    )
    
    # Twilio tracking
    twilio_sid = models.CharField(
        max_length=100,
        blank=True,
        help_text="ID message Twilio"
    )
    
    # Traçabilité
    created_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Vérification Téléphone'
        verbose_name_plural = 'Vérifications Téléphone'
        indexes = [
            models.Index(fields=['phone_number', 'verified']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['user', '-created_at'])
        ]
    
    def save(self, *args, **kwargs):
        if not self.code:
            # Génération code 5 chiffres aléatoire
            self.code = ''.join(secrets.choice(string.digits) for _ in range(5))
        
        if not self.expires_at:
            # Expiration 5 minutes
            self.expires_at = timezone.now() + timedelta(minutes=5)
        
        super().save(*args, **kwargs)
    
    @property
    def is_expired(self):
        """Vérifie si le code a expiré"""
        return timezone.now() > self.expires_at
    
    @property
    def is_valid(self):
        """Vérifie si le code est encore utilisable"""
        return not self.verified and not self.is_expired and self.attempts < 3
    
    def __str__(self):
        status = '✓' if self.verified else ('⏰' if self.is_expired else '✗')
        return f"SMS {self.phone_number} - {self.code} ({status})"


# ==================== PROFILS DE RÔLES (Modifications) ====================

class Producteur(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, primary_key=True)
    type_production = models.CharField(max_length=100, blank=True)
    superficie = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    certification = models.CharField(max_length=100, blank=True)
    
    # ========== NOUVEAUX CHAMPS GIC/COOPÉRATIVE ==========
    is_in_gic = models.BooleanField(
        default=False,
        verbose_name="Membre d'un GIC",
        help_text="Groupement d'Intérêt Communautaire"
    )
    gic_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Nom du GIC"
    )
    gic_registration_number = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Numéro d'enregistrement GIC"
    )
    
    is_in_cooperative = models.BooleanField(
        default=False,
        verbose_name="Membre d'une coopérative agricole"
    )
    cooperative_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Nom de la coopérative"
    )
    cooperative_registration_number = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Numéro d'enregistrement coopérative"
    )
    
    # Stats cache
    total_productions = models.IntegerField(default=0)
    last_production_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Profil Producteur'
        verbose_name_plural = 'Profils Producteurs'
    
    @property
    def has_organization_badge(self):
        """Badge 🏢 si membre GIC ou Coopérative"""
        return self.is_in_gic or self.is_in_cooperative
    
    @property
    def organization_info(self):
        """Informations structure pour affichage"""
        if self.is_in_gic:
            return {
                'type': 'GIC',
                'name': self.gic_name,
                'registration': self.gic_registration_number
            }
        if self.is_in_cooperative:
            return {
                'type': 'Coopérative',
                'name': self.cooperative_name,
                'registration': self.cooperative_registration_number
            }
        return None
    
    def __str__(self):
        return f"Producteur: {self.user.get_full_name()}"


# ==================== AUTRES MODÈLES (Inchangés) ====================

class Transporteur(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, primary_key=True)
    type_vehicule = models.CharField(max_length=100, blank=True)
    capacite = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    permis_transport = models.CharField(max_length=50, blank=True)
    conditions_conservation = models.TextField(blank=True)
    
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
    type_distribution = models.CharField(max_length=100, blank=True)
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
    expires_at = models.DateTimeField(db_index=True)
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
    
class UserBadge(models.Model):
    """
    Système de badges utilisateur.
    Certains automatiques, d'autres attribués manuellement par admin.
    """
    BADGE_TYPES = [
        # Badges de vérification (automatiques)
        ('phone_verified', '📱 Téléphone Vérifié'),
        ('documents_verified', '✅ Documents Vérifiés'),
        ('organization_member', '🏢 Membre GIC/Coopérative'),
        
        # Badges de réputation (futurs - manuels pour l'instant)
        ('top_seller', '⭐ Top Vendeur'),
        ('lightning_fast', '⚡ Livraison Express'),
        ('veteran', '🎖️ Vétéran'),
        ('trusted_partner', '🤝 Partenaire de Confiance'),
    ]
    
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='badges'
    )
    badge_type = models.CharField(
        max_length=50,
        choices=BADGE_TYPES,
        db_index=True
    )
    
    # Attribution
    awarded_at = models.DateTimeField(auto_now_add=True)
    awarded_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='badges_awarded',
        help_text="Admin qui a attribué le badge (si manuel)"
    )
    
    # Validité
    is_active = models.BooleanField(
        default=True,
        db_index=True
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date d'expiration (si badge temporaire)"
    )
    
    # Métadonnées optionnelles
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Données supplémentaires (ex: nombre de ventes pour top_seller)"
    )
    
    class Meta:
        unique_together = ['user', 'badge_type']
        ordering = ['-awarded_at']
        verbose_name = 'Badge Utilisateur'
        verbose_name_plural = 'Badges Utilisateurs'
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['badge_type', 'is_active'])
        ]
    
    @property
    def is_valid(self):
        """Vérifie si le badge est toujours valide"""
        if not self.is_active:
            return False
        
        if self.expires_at and self.expires_at < timezone.now():
            return False
        
        return True
    
    @property
    def display_name(self):
        """Retourne le nom d'affichage du badge"""
        return dict(self.BADGE_TYPES).get(self.badge_type, self.badge_type)
    
    @property
    def icon(self):
        """Extrait l'emoji du nom d'affichage"""
        display = self.display_name
        return display.split()[0] if display else ''
    
    def __str__(self):
        status = '✓' if self.is_valid else '✗'
        return f"{self.user.email} - {self.display_name} ({status})"

