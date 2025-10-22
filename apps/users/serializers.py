# apps/users/serializers.py
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.utils import timezone
from django.db import models, transaction
from knox.models import AuthToken
from .models import (
    CustomUser, PasswordResetRequest, Producteur,
    Transporteur, Transformateur, Distributeur, Consommateur,
    PhoneVerification, UserBadge  # AJOUT

)


# ==================== AUTHENTIFICATION ====================

class LoginSerializer(serializers.Serializer):
    identifier = serializers.CharField()
    password = serializers.CharField()

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
            if not user.is_active:
                raise serializers.ValidationError('Compte désactivé')
            
            attrs['user'] = user
            return attrs
        
        raise serializers.ValidationError('Identifier et password requis')


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = CustomUser
        fields = ['email', 'telephone', 'nom', 'prenom', 'adresse', 'avatar',
                 'password', 'password_confirm']
        extra_kwargs = {
            'telephone': {'required': False},
            'nom': {'required': False},
            'prenom': {'required': False},
            'adresse': {'required': False},
            'avatar': {'required': False},
        }
    
    def validate(self, attrs):
        if attrs.get('password') != attrs.get('password_confirm'):
            raise serializers.ValidationError("Les mots de passe ne correspondent pas")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        with transaction.atomic():
            user = CustomUser.objects.create_user(
                password=password,
                is_consommateur=True,
                **validated_data
            )
            
            Consommateur.objects.create(
                user=user,
                adresse_livraison=validated_data.get('adresse', '')
            )
            
            user.profile_completed = user.check_profile_requirements()
            user.save(update_fields=['profile_completed'])
            
        return user


# ==================== NOUVEAU : VÉRIFICATION SMS ====================

class PhoneVerificationRequestSerializer(serializers.Serializer):
    """Demande d'envoi de code SMS"""
    phone_number = serializers.CharField(
        max_length=20,
        help_text="Numéro au format +237XXXXXXXXX ou 6XXXXXXXX"
    )


class PhoneVerificationCodeSerializer(serializers.Serializer):
    """Vérification du code reçu"""
    code = serializers.CharField(
        min_length=5,
        max_length=5,
        help_text="Code 5 chiffres reçu par SMS"
    )
    
    def validate_code(self, value):
        """Vérifie que le code ne contient que des chiffres"""
        if not value.isdigit():
            raise serializers.ValidationError("Le code doit contenir uniquement des chiffres")
        return value


# ==================== ACTIVATION RÔLES ====================

class RoleActivationSerializer(serializers.Serializer):
    role = serializers.ChoiceField(
        choices=['producteur', 'transporteur', 'transformateur', 'distributeur']
    )
    
    # Champs producteur
    type_production = serializers.CharField(required=False)
    superficie = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    
    # ========== NOUVEAUX CHAMPS GIC/COOPÉRATIVE ==========
    is_in_gic = serializers.BooleanField(required=False, default=False)
    gic_name = serializers.CharField(max_length=200, required=False, allow_blank=True)
    gic_registration_number = serializers.CharField(max_length=50, required=False, allow_blank=True)
    
    is_in_cooperative = serializers.BooleanField(required=False, default=False)
    cooperative_name = serializers.CharField(max_length=200, required=False, allow_blank=True)
    cooperative_registration_number = serializers.CharField(max_length=50, required=False, allow_blank=True)
    
    # Champs transporteur
    type_vehicule = serializers.CharField(required=False)
    capacite = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    permis_transport = serializers.CharField(required=False)
    
    # Champs transformateur
    type_transformation = serializers.CharField(required=False)
    
    # Champs distributeur
    type_distribution = serializers.CharField(required=False)
    zones_service = serializers.CharField(required=False)
    
    def validate(self, attrs):
        role = attrs.get('role')
        
        # Champs requis par rôle
        required_fields = {
            'producteur': ['type_production'],
            'transporteur': ['type_vehicule', 'capacite'],
            'transformateur': ['type_transformation'],
            'distributeur': ['type_distribution']
        }
        
        if role in required_fields:
            missing = [f for f in required_fields[role] if not attrs.get(f)]
            if missing:
                raise serializers.ValidationError(
                    f"Champs requis pour {role}: {', '.join(missing)}"
                )
        
        # Validation GIC
        if attrs.get('is_in_gic') and not attrs.get('gic_name'):
            raise serializers.ValidationError(
                "Le nom du GIC est requis si vous êtes membre d'un GIC"
            )
        
        # Validation Coopérative
        if attrs.get('is_in_cooperative') and not attrs.get('cooperative_name'):
            raise serializers.ValidationError(
                "Le nom de la coopérative est requis si vous êtes membre"
            )
        
        return attrs
    
    def create(self, validated_data):
        user = self.context['request'].user
        role = validated_data.pop('role')
        
        with transaction.atomic():
            user.activate_role(role)
            
            # Création profil selon rôle
            if role == 'producteur':
                Producteur.objects.get_or_create(
                    user=user,
                    defaults={
                        'type_production': validated_data.get('type_production', ''),
                        'superficie': validated_data.get('superficie'),
                        'is_in_gic': validated_data.get('is_in_gic', False),
                        'gic_name': validated_data.get('gic_name', ''),
                        'gic_registration_number': validated_data.get('gic_registration_number', ''),
                        'is_in_cooperative': validated_data.get('is_in_cooperative', False),
                        'cooperative_name': validated_data.get('cooperative_name', ''),
                        'cooperative_registration_number': validated_data.get('cooperative_registration_number', ''),
                    }
                )
            
            elif role == 'transporteur':
                Transporteur.objects.get_or_create(
                    user=user,
                    defaults={
                        'type_vehicule': validated_data.get('type_vehicule', ''),
                        'capacite': validated_data.get('capacite'),
                        'permis_transport': validated_data.get('permis_transport', ''),
                    }
                )
            
            elif role == 'transformateur':
                Transformateur.objects.get_or_create(
                    user=user,
                    defaults={
                        'type_transformation': validated_data.get('type_transformation', ''),
                    }
                )
            
            elif role == 'distributeur':
                Distributeur.objects.get_or_create(
                    user=user,
                    defaults={
                        'type_distribution': validated_data.get('type_distribution', ''),
                        'zones_service': validated_data.get('zones_service', ''),
                    }
                )
        
        return user


# ==================== PROFIL UTILISATEUR ====================

class ProducteurMiniSerializer(serializers.ModelSerializer):
    organization = serializers.SerializerMethodField()
    
    class Meta:
        model = Producteur
        fields = [
            'type_production', 'superficie', 'certification',
            'total_productions', 'organization'
        ]
    
    def get_organization(self, obj):
        """Retourne infos GIC/Coopérative si membre"""
        return obj.organization_info


class TransporteurMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transporteur
        fields = ['type_vehicule', 'capacite', 'permis_transport', 'total_trajets', 'note_moyenne']


class TransformateurMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transformateur
        fields = ['type_transformation', 'certification', 'capacite_traitement']


class DistributeurMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Distributeur
        fields = ['type_distribution', 'zones_service', 'licence']


class UserProfileSerializer(serializers.ModelSerializer):
    active_roles = serializers.SerializerMethodField()
    role_profiles = serializers.SerializerMethodField()
    badges = serializers.SerializerMethodField()  # NOUVEAU
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'email', 'telephone', 'nom', 'prenom', 'adresse', 'avatar',
            'is_consommateur', 'is_producteur', 'is_transporteur',
            'is_transformateur', 'is_distributeur',
            'is_producteur_verified', 'is_transporteur_verified',
            'is_transformateur_verified', 'is_distributeur_verified',
            'profile_completed',
            'phone_verified',
            'phone_verified_at',
            'date_creation',
            'active_roles',
            'role_profiles',
            'badges'  # NOUVEAU
        ]
        read_only_fields = [
            'id', 'email', 'date_creation', 'is_consommateur',
            'is_producteur', 'is_transporteur', 'is_transformateur', 'is_distributeur',
            'is_producteur_verified', 'is_transporteur_verified',
            'is_transformateur_verified', 'is_distributeur_verified',
            'phone_verified', 'phone_verified_at', 'badges'
        ]
    
    def get_active_roles(self, obj):
        return obj.get_active_roles()
    
    def get_role_profiles(self, obj):
        """Récupère profils actifs (optimisé avec dict comprehension)"""
        role_mapping = {
            'producteur': (obj.is_producteur, ProducteurMiniSerializer),
            'transporteur': (obj.is_transporteur, TransporteurMiniSerializer),
            'transformateur': (obj.is_transformateur, TransformateurMiniSerializer),
            'distributeur': (obj.is_distributeur, DistributeurMiniSerializer),
        }
        
        return {
            role: serializer_class(getattr(obj, role)).data
            for role, (is_active, serializer_class) in role_mapping.items()
            if is_active and hasattr(obj, role)
        }
    
    def get_badges(self, obj):
        """
        Retourne les badges actifs de l'utilisateur.
        Optimisé avec list comprehension.
        """
        from .services import BadgeService
        return BadgeService.get_user_badges_summary(obj)


class ProfileCompletionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['telephone', 'nom', 'prenom', 'adresse', 'avatar']
    
    def update(self, instance, validated_data):
        # Mise à jour avec list comprehension
        update_fields = [
            field for field in validated_data.keys()
            if hasattr(instance, field)
        ]
        
        for field in update_fields:
            setattr(instance, field, validated_data[field])
        
        instance.profile_completed = instance.check_profile_requirements()
        instance.save(update_fields=update_fields + ['profile_completed'])
        
        return instance


# ==================== PASSWORD RESET (Inchangé) ====================

class PasswordResetRequestSerializer(serializers.Serializer):
    identifier = serializers.CharField()
    
    def validate_identifier(self, value):
        exists = CustomUser.objects.filter(
            models.Q(email=value) | models.Q(telephone=value)
        ).exists()
        
        if not exists:
            raise serializers.ValidationError("Utilisateur non trouvé")
        return value


class OTPVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp_code = serializers.CharField(max_length=6, min_length=6)


class TokenValidationSerializer(serializers.Serializer):
    reset_token = serializers.CharField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    reset_token = serializers.CharField()
    new_password = serializers.CharField(min_length=8)
    new_password_confirm = serializers.CharField()
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("Les mots de passe ne correspondent pas")
        return attrs


class SocialAuthSerializer(serializers.Serializer):
    access_token = serializers.CharField()

class UserBadgeSerializer(serializers.ModelSerializer):
    """Serializer pour affichage des badges"""
    name = serializers.CharField(source='display_name', read_only=True)
    icon = serializers.CharField(read_only=True)
    is_valid = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = UserBadge
        fields = ['type', 'name', 'icon', 'awarded_at', 'is_valid', 'metadata']
        read_only_fields = ['type', 'name', 'icon', 'awarded_at', 'is_valid', 'metadata']
    
    def to_representation(self, instance):
        """Représentation simplifiée pour l'API"""
        return {
            'type': instance.badge_type,
            'name': instance.display_name,
            'icon': instance.icon,
            'awarded_at': instance.awarded_at,
            'metadata': instance.metadata
        }