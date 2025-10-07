from rest_framework import serializers
from django.contrib.auth import authenticate
from django.utils import timezone
from django.db import models, transaction
from knox.models import AuthToken
from .models import (
    CustomUser, PasswordResetRequest, Producteur, 
    Transporteur, Transformateur, Distributeur, Consommateur
)


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
            # Création utilisateur (consommateur par défaut)
            user = CustomUser.objects.create_user(
                password=password,
                is_consommateur=True,
                **validated_data
            )
            
            # Création profil consommateur
            Consommateur.objects.create(
                user=user,
                adresse_livraison=validated_data.get('adresse', '')
            )
            
            # Vérification profil complété
            user.profile_completed = user.check_profile_requirements()
            user.save(update_fields=['profile_completed'])
            
        return user


class RoleActivationSerializer(serializers.Serializer):
    role = serializers.ChoiceField(
        choices=['producteur', 'transporteur', 'transformateur', 'distributeur']
    )
    # Champs optionnels selon le rôle
    type_production = serializers.CharField(required=False)
    superficie = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    type_vehicule = serializers.CharField(required=False)
    capacite = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    permis_transport = serializers.CharField(required=False)
    type_transformation = serializers.CharField(required=False)
    type_distribution = serializers.CharField(required=False)
    zones_service = serializers.CharField(required=False)
    
    def validate(self, attrs):
        role = attrs.get('role')
        
        # Validation des champs requis par rôle (optimisé avec dict)
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
        
        return attrs
    
    def create(self, validated_data):
        user = self.context['request'].user
        role = validated_data.pop('role')
        
        with transaction.atomic():
            # Activation du rôle
            user.activate_role(role)
            
            # Création du profil associé
            role_models = {
                'producteur': (Producteur, ['type_production', 'superficie']),
                'transporteur': (Transporteur, ['type_vehicule', 'capacite', 'permis_transport']),
                'transformateur': (Transformateur, ['type_transformation']),
                'distributeur': (Distributeur, ['type_distribution', 'zones_service'])
            }
            
            if role in role_models:
                model_class, fields = role_models[role]
                profile_data = {f: validated_data.get(f) for f in fields if f in validated_data}
                model_class.objects.get_or_create(user=user, defaults=profile_data)
        
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    active_roles = serializers.SerializerMethodField()
    role_profiles = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'email', 'telephone', 'nom', 'prenom', 'adresse', 'avatar',
            'is_consommateur', 'is_producteur', 'is_transporteur', 
            'is_transformateur', 'is_distributeur',
            'is_producteur_verified', 'is_transporteur_verified',
            'is_transformateur_verified', 'is_distributeur_verified',
            'profile_completed', 'date_creation', 'active_roles', 'role_profiles'
        ]
        read_only_fields = [
            'id', 'email', 'date_creation', 'is_consommateur',
            'is_producteur', 'is_transporteur', 'is_transformateur', 'is_distributeur',
            'is_producteur_verified', 'is_transporteur_verified',
            'is_transformateur_verified', 'is_distributeur_verified'
        ]
    
    def get_active_roles(self, obj):
        return obj.get_active_roles()
    
    def get_role_profiles(self, obj):
        """Récupère les profils actifs (optimisé)"""
        profiles = {}
        
        # Liste des rôles à vérifier avec leurs serializers
        role_checks = [
            ('producteur', obj.is_producteur, ProducteurMiniSerializer),
            ('transporteur', obj.is_transporteur, TransporteurMiniSerializer),
            ('transformateur', obj.is_transformateur, TransformateurMiniSerializer),
            ('distributeur', obj.is_distributeur, DistributeurMiniSerializer),
        ]
        
        # Utilisation de list comprehension pour filtrer et serializer
        for role_name, is_active, serializer_class in role_checks:
            if is_active and hasattr(obj, role_name):
                profiles[role_name] = serializer_class(getattr(obj, role_name)).data
        
        return profiles


# Mini serializers pour les profils de rôle (éviter les requêtes N+1)
class ProducteurMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Producteur
        fields = ['type_production', 'superficie', 'certification', 'total_productions']


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


class ProfileCompletionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['telephone', 'nom', 'prenom', 'adresse', 'avatar']
    
    def update(self, instance, validated_data):
        # Update avec list comprehension
        update_fields = [field for field in validated_data.keys() 
                        if hasattr(instance, field)]
        
        for field in update_fields:
            setattr(instance, field, validated_data[field])
        
        # Vérification profil complété
        instance.profile_completed = instance.check_profile_requirements()
        instance.save(update_fields=update_fields + ['profile_completed'])
        
        return instance


class PasswordResetRequestSerializer(serializers.Serializer):
    identifier = serializers.CharField()
    
    def validate_identifier(self, value):
        # Vérification existence optimisée
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