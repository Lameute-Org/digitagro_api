from rest_framework import serializers
from django.contrib.auth import authenticate
from django.utils import timezone
from django.db import models
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
    role_choisi = serializers.ChoiceField(choices=CustomUser.ROLE_CHOICES)
    
    # Champs spécifiques selon le rôle
    type_production = serializers.CharField(required=False, write_only=True)
    superficie = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, write_only=True)
    type_vehicule = serializers.CharField(required=False, write_only=True)
    capacite = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, write_only=True)
    type_transformation = serializers.CharField(required=False, write_only=True)
    type_distribution = serializers.CharField(required=False, write_only=True)
    
    class Meta:
        model = CustomUser
        fields = [
            'email', 'telephone', 'nom', 'prenom', 'adresse', 'avatar',
            'role_choisi', 'password', 'password_confirm',
            # Champs rôles spécifiques
            'type_production', 'superficie', 'type_vehicule', 'capacite',
            'type_transformation', 'type_distribution'
        ]
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Les mots de passe ne correspondent pas")
        return attrs
    
    def create_role_instance_recursif(self, user, role, extra_data, roles_mapping=None, index=0):
        """Crée l'instance de rôle avec algorithme récursif"""
        if roles_mapping is None:
            roles_mapping = {
                'producteur': (Producteur, ['type_production', 'superficie']),
                'transporteur': (Transporteur, ['type_vehicule', 'capacite']),
                'transformateur': (Transformateur, ['type_transformation']),
                'distributeur': (Distributeur, ['type_distribution']),
                'consommateur': (Consommateur, [])
            }
        
        if role not in roles_mapping:
            return Consommateur.objects.create(
                user=user,
                adresse_livraison=user.adresse
            )
        
        model_class, required_fields = roles_mapping[role]
        role_data = {'user': user}
        
        # Extraction récursive des données
        def extraire_donnees_recursif(fields, field_index=0):
            if field_index >= len(fields):
                return role_data
            
            field = fields[field_index]
            if field in extra_data:
                role_data[field] = extra_data[field]
            
            return extraire_donnees_recursif(fields, field_index + 1)
        
        extraire_donnees_recursif(required_fields)
        
        # Ajout de champs par défaut selon le rôle
        if role == 'consommateur':
            role_data['adresse_livraison'] = user.adresse
        elif role == 'distributeur':
            role_data['zones_service'] = user.adresse
        
        return model_class.objects.create(**role_data)
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        role_choisi = validated_data.pop('role_choisi')
        
        # Extraction des données spécifiques au rôle
        role_fields = ['type_production', 'superficie', 'type_vehicule', 'capacite', 
                      'type_transformation', 'type_distribution']
        role_data = {}
        for field in role_fields:
            if field in validated_data:
                role_data[field] = validated_data.pop(field)
        
        # Création de l'utilisateur
        user = CustomUser.objects.create_user(
            password=password, 
            role_choisi=role_choisi,
            **validated_data
        )
        
        # Création de l'instance de rôle spécifique
        self.create_role_instance_recursif(user, role_choisi, role_data)
        
        # Marquer le profil comme complété
        user.profile_completed = True
        user.save()
        
        return user


class ProducteurSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = Producteur
        fields = ['user', 'type_production', 'superficie', 'certification']


class TransporteurSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = Transporteur
        fields = ['user', 'type_vehicule', 'capacite', 'permis_transport', 'conditions_conservation']


class UserProfileSerializer(serializers.ModelSerializer):
    user_role = serializers.SerializerMethodField()
    role_details = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'telephone', 'nom', 'prenom', 'adresse', 
                 'avatar', 'role_choisi', 'profile_completed', 'date_creation', 
                 'user_role', 'role_details']
        read_only_fields = ['id', 'email', 'date_creation', 'profile_completed']
    
    def get_user_role(self, obj):
        return obj.get_role()
    
    def get_role_details_recursif(self, obj, roles_mapping=None, index=0):
        """Récupère les détails du rôle avec algorithme récursif"""
        if roles_mapping is None:
            roles_mapping = [
                ('producteur', ProducteurSerializer),
                ('transporteur', TransporteurSerializer),
                ('transformateur', None),  # Ajoutera les autres sérialiseurs plus tard
                ('distributeur', None),
                ('consommateur', None)
            ]
        
        if index >= len(roles_mapping):
            return None
        
        role_name, serializer_class = roles_mapping[index]
        
        if hasattr(obj, role_name) and serializer_class:
            role_instance = getattr(obj, role_name)
            return serializer_class(role_instance).data
        
        return self.get_role_details_recursif(obj, roles_mapping, index + 1)
    
    def get_role_details(self, obj):
        return self.get_role_details_recursif(obj)


class ProfileCompletionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['telephone', 'nom', 'prenom', 'adresse', 'avatar']
    
    def update(self, instance, validated_data):
        def update_fields_recursif(fields_list, field_index=0):
            if field_index >= len(fields_list):
                return
            
            field = fields_list[field_index]
            if field in validated_data:
                setattr(instance, field, validated_data[field])
            
            update_fields_recursif(fields_list, field_index + 1)
        
        fields = list(validated_data.keys())
        update_fields_recursif(fields)
        
        # Vérifier si le profil est maintenant complet
        required_fields = ['telephone', 'adresse', 'nom', 'prenom']
        if all(getattr(instance, field) for field in required_fields):
            instance.profile_completed = True
        
        instance.save()
        return instance


class PasswordResetRequestSerializer(serializers.Serializer):
    identifier = serializers.CharField()
    
    def validate_identifier(self, value):
        if not CustomUser.objects.filter(
            models.Q(email=value) | models.Q(telephone=value)
        ).exists():
            raise serializers.ValidationError("Utilisateur non trouvé")
        return value


class OTPVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp_code = serializers.CharField(max_length=6)


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