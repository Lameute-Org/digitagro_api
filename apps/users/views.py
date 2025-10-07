from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.generics import (
    CreateAPIView, 
    RetrieveUpdateAPIView, 
    UpdateAPIView,
    GenericAPIView
)
from rest_framework.views import APIView
from knox.views import (
    LoginView as KnoxLoginView,
    LogoutView as KnoxLogoutView,
    LogoutAllView as KnoxLogoutAllView
)
from knox.models import AuthToken
from django.contrib.auth import authenticate, login
from django.db.models import Q, Prefetch
from django.utils import timezone
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from drf_spectacular.utils import extend_schema, OpenApiExample
from .models import (
    CustomUser, PasswordResetRequest, Producteur,
    Transporteur, Transformateur, Distributeur, Consommateur
)
from .serializers import (
    UserRegistrationSerializer,
    UserProfileSerializer,
    ProfileCompletionSerializer,
    LoginSerializer,
    RoleActivationSerializer,
    PasswordResetRequestSerializer,
    OTPVerificationSerializer,
    TokenValidationSerializer,
    PasswordResetConfirmSerializer,
    SocialAuthSerializer
)
from .permissions import IsProfileCompleted, IsOwnerOrReadOnly
from .docs.users_swagger import (
    USER_REGISTRATION_SCHEMA,
    LOGIN_SCHEMA,
    LOGOUT_SCHEMA,
    LOGOUT_ALL_SCHEMA,
    USER_PROFILE_GET_SCHEMA,
    USER_PROFILE_UPDATE_SCHEMA,
    COMPLETE_PROFILE_SCHEMA,
    ROLE_ACTIVATION_SCHEMA,
    ROLES_STATUS_SCHEMA,
    PASSWORD_RESET_REQUEST_SCHEMA,
    OTP_VERIFICATION_SCHEMA,
    TOKEN_VALIDATION_SCHEMA,
    PASSWORD_RESET_CONFIRM_SCHEMA
)

# ==================== VIEWS ====================

@USER_REGISTRATION_SCHEMA
class UserRegistrationView(CreateAPIView):
    """Inscription - Tout le monde est consommateur par défaut"""
    queryset = CustomUser.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Auto-génération du token Knox
        instance, token = AuthToken.objects.create(user)
        
        return Response({
            'user': UserProfileSerializer(user).data,
            'token': token,
            'expiry': instance.expiry
        }, status=status.HTTP_201_CREATED)


@LOGIN_SCHEMA
class CustomLoginView(KnoxLoginView):
    """Connexion avec email ou téléphone"""
    permission_classes = [AllowAny]

    def post(self, request, format=None):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        login(request, user)
        
        return super(CustomLoginView, self).post(request, format=None)

    def get_post_response_data(self, request, token, instance):
        # Optimisation: select_related pour éviter les requêtes multiples
        user = CustomUser.objects.select_related(
            'producteur', 'transporteur', 'transformateur', 
            'distributeur', 'consommateur'
        ).get(pk=request.user.pk)
        
        return {
            'token': token,
            'expiry': instance.expiry,
            'user': UserProfileSerializer(user).data
        }


@LOGOUT_SCHEMA
class CustomLogoutView(KnoxLogoutView):
    """Déconnexion - Révoque le token actuel"""
    permission_classes = [IsAuthenticated]


@LOGOUT_ALL_SCHEMA
class CustomLogoutAllView(KnoxLogoutAllView):
    """Déconnexion de tous les appareils"""
    permission_classes = [IsAuthenticated]


class UserProfileView(RetrieveUpdateAPIView):
    """Consultation et mise à jour du profil"""
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def get_object(self):
        # Optimisation avec select_related
        return CustomUser.objects.select_related(
            'producteur', 'transporteur', 'transformateur',
            'distributeur', 'consommateur'
        ).get(pk=self.request.user.pk)
    
    @USER_PROFILE_GET_SCHEMA
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @USER_PROFILE_UPDATE_SCHEMA
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)


@COMPLETE_PROFILE_SCHEMA
class CompleteProfileView(UpdateAPIView):
    """Compléter les informations manquantes du profil"""
    serializer_class = ProfileCompletionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user


@ROLE_ACTIVATION_SCHEMA
class RoleActivationView(CreateAPIView):
    """Activation dynamique d'un rôle"""
    serializer_class = RoleActivationSerializer
    permission_classes = [IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        # Vérification profil complété avant activation rôle pro
        if not request.user.profile_completed:
            return Response(
                {'error': 'Veuillez compléter votre profil avant d\'activer un rôle professionnel'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Retour du profil mis à jour
        user_with_roles = CustomUser.objects.select_related(
            'producteur', 'transporteur', 'transformateur',
            'distributeur', 'consommateur'
        ).get(pk=user.pk)
        
        return Response({
            'message': f'Rôle {request.data.get("role")} activé avec succès',
            'user': UserProfileSerializer(user_with_roles).data
        }, status=status.HTTP_200_OK)


@ROLES_STATUS_SCHEMA
class UserRolesStatusView(APIView):
    """Statut des rôles de l'utilisateur"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        roles_status = {
            'active_roles': user.get_active_roles(),
            'available_roles': {
                'producteur': {
                    'active': user.is_producteur,
                    'verified': user.is_producteur_verified,
                    'activated_at': user.producteur_activated_at
                },
                'transporteur': {
                    'active': user.is_transporteur,
                    'verified': user.is_transporteur_verified,
                    'activated_at': user.transporteur_activated_at
                },
                'transformateur': {
                    'active': user.is_transformateur,
                    'verified': user.is_transformateur_verified,
                    'activated_at': user.transformateur_activated_at
                },
                'distributeur': {
                    'active': user.is_distributeur,
                    'verified': user.is_distributeur_verified,
                    'activated_at': user.distributeur_activated_at
                }
            },
            'profile_completed': user.profile_completed
        }
        
        return Response(roles_status, status=status.HTTP_200_OK)


@PASSWORD_RESET_REQUEST_SCHEMA
class PasswordResetRequestView(CreateAPIView):
    """Demande de réinitialisation mot de passe"""
    serializer_class = PasswordResetRequestSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        identifier = serializer.validated_data['identifier']
        
        try:
            # Requête optimisée
            user = CustomUser.objects.only('id', 'email', 'nom', 'prenom').get(
                Q(email=identifier) | Q(telephone=identifier)
            )
        except CustomUser.DoesNotExist:
            # Message générique pour sécurité
            return Response(
                {'message': 'Si cet utilisateur existe, un email a été envoyé'}, 
                status=status.HTTP_200_OK
            )
        
        # Suppression anciennes demandes expirées (nettoyage)
        PasswordResetRequest.objects.filter(
            user=user,
            expires_at__lt=timezone.now()
        ).delete()
        
        # Création nouvelle demande
        reset_request = PasswordResetRequest.objects.create(user=user)
        
        # Envoi email optimisé
        context = {
            'user_name': user.get_full_name(),
            'otp_code': reset_request.otp_code,
            'reset_link': f"{settings.FRONTEND_URL}/reset-password?token={reset_request.reset_token}"
        }
        
        html_content = render_to_string('emails/password_reset_otp.html', context)
        
        email = EmailMultiAlternatives(
            subject='Code de réinitialisation DIGITAGRO',
            body=f'Votre code: {reset_request.otp_code}',
            from_email=settings.EMAIL_HOST_USER,
            to=[user.email]
        )
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=True)
        
        return Response(
            {'message': 'Code de réinitialisation envoyé'}, 
            status=status.HTTP_200_OK
        )


@OTP_VERIFICATION_SCHEMA
class OTPVerificationView(GenericAPIView):
    """Validation du code OTP"""
    serializer_class = OTPVerificationSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        otp_code = serializer.validated_data['otp_code']
        
        try:
            # Requête optimisée avec select_for_update pour éviter race conditions
            reset_request = PasswordResetRequest.objects.select_for_update().get(
                user__email=email,
                otp_code=otp_code,
                is_validated=False,
                expires_at__gt=timezone.now()  # Vérification directe expiration
            )
            
            reset_request.is_validated = True
            reset_request.save(update_fields=['is_validated'])
            
            return Response({
                'message': 'Code validé',
                'reset_token': reset_request.reset_token
            }, status=status.HTTP_200_OK)
            
        except PasswordResetRequest.DoesNotExist:
            return Response(
                {'error': 'Code invalide ou expiré'}, 
                status=status.HTTP_400_BAD_REQUEST
            )


@TOKEN_VALIDATION_SCHEMA
class TokenValidationView(GenericAPIView):
    """Validation du token de reset"""
    serializer_class = TokenValidationSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        reset_token = serializer.validated_data['reset_token']
        
        # Vérification existence et expiration en une requête
        valid = PasswordResetRequest.objects.filter(
            reset_token=reset_token,
            expires_at__gt=timezone.now()
        ).exists()
        
        if valid:
            return Response(
                {'message': 'Token valide'}, 
                status=status.HTTP_200_OK
            )
        
        return Response(
            {'error': 'Token invalide ou expiré'}, 
            status=status.HTTP_400_BAD_REQUEST
        )


@PASSWORD_RESET_CONFIRM_SCHEMA
class PasswordResetConfirmView(GenericAPIView):
    """Confirmation finale du reset"""
    serializer_class = PasswordResetConfirmSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        reset_token = serializer.validated_data['reset_token']
        new_password = serializer.validated_data['new_password']
        
        try:
            reset_request = PasswordResetRequest.objects.select_related('user').get(
                reset_token=reset_token,
                expires_at__gt=timezone.now()
            )
            
            # Réinitialisation mot de passe
            user = reset_request.user
            user.set_password(new_password)
            user.save(update_fields=['password'])
            
            # Suppression demande
            reset_request.delete()
            
            # Optionnel: Révoquer tous les tokens Knox
            AuthToken.objects.filter(user=user).delete()
            
            return Response(
                {'message': 'Mot de passe réinitialisé avec succès'}, 
                status=status.HTTP_200_OK
            )
            
        except PasswordResetRequest.DoesNotExist:
            return Response(
                {'error': 'Token invalide ou expiré'}, 
                status=status.HTTP_400_BAD_REQUEST
            )


class GoogleAuthView(GenericAPIView):
    """Authentification Google OAuth2 - À implémenter"""
    serializer_class = SocialAuthSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        return Response(
            {'message': 'Google Auth à implémenter'}, 
            status=status.HTTP_501_NOT_IMPLEMENTED
        )