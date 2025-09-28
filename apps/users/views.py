from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.generics import (
    CreateAPIView, 
    RetrieveUpdateAPIView, 
    UpdateAPIView,
    GenericAPIView
)
from knox.views import LoginView as KnoxLoginView
from knox.models import AuthToken
from django.contrib.auth import authenticate, login
from django.db.models import Q
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings

from .models import CustomUser, PasswordResetRequest
from .serializers import (
    UserRegistrationSerializer,
    UserProfileSerializer,
    ProfileCompletionSerializer,
    LoginSerializer,
    PasswordResetRequestSerializer,
    OTPVerificationSerializer,
    TokenValidationSerializer,
    PasswordResetConfirmSerializer,
    SocialAuthSerializer
)
from .permissions import IsProfileCompleted, IsOwnerOrReadOnly

# Import de la documentation Swagger
from .docs.users_swagger import (
    USER_REGISTRATION_SCHEMA,
    TOKEN_OBTAIN_SCHEMA,
    USER_PROFILE_GET_SCHEMA,
    USER_PROFILE_UPDATE_SCHEMA,
    COMPLETE_PROFILE_SCHEMA,
    PASSWORD_RESET_REQUEST_SCHEMA,
    OTP_VERIFICATION_SCHEMA,
    TOKEN_VALIDATION_SCHEMA,
    PASSWORD_RESET_CONFIRM_SCHEMA,
    GOOGLE_AUTH_SCHEMA
)


@USER_REGISTRATION_SCHEMA
class UserRegistrationView(CreateAPIView):
    """Enregistrement d'un nouvel utilisateur avec choix de rôle et auto-login"""
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


@TOKEN_OBTAIN_SCHEMA
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
        return {
            'token': token,
            'expiry': instance.expiry,
            'user': UserProfileSerializer(request.user).data
        }


class UserProfileView(RetrieveUpdateAPIView):
    """Consultation et mise à jour du profil utilisateur"""
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def get_object(self):
        return self.request.user

    @USER_PROFILE_GET_SCHEMA
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @USER_PROFILE_UPDATE_SCHEMA
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)


@COMPLETE_PROFILE_SCHEMA
class CompleteProfileView(UpdateAPIView):
    """Achèvement forcé du profil après social auth"""
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
            user = CustomUser.objects.get(
                Q(email=identifier) | Q(telephone=identifier)
            )
        except CustomUser.DoesNotExist:
            return Response(
                {'message': 'Si cet utilisateur existe, un email a été envoyé'}, 
                status=status.HTTP_200_OK
            )
        
        # Créer la demande de reset
        reset_request = PasswordResetRequest.objects.create(user=user)
        
        # Envoyer OTP par email
        send_mail(
            subject='Code de réinitialisation DIGITAGRO',
            message=f'Votre code de réinitialisation: {reset_request.otp_code}',
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user.email],
            fail_silently=True,
        )
        
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
            reset_request = PasswordResetRequest.objects.get(
                user__email=email,
                otp_code=otp_code,
                is_validated=False
            )
            
            if reset_request.is_expired:
                return Response(
                    {'error': 'Code expiré'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            reset_request.is_validated = True
            reset_request.save()
            
            return Response({
                'message': 'Code validé',
                'reset_token': reset_request.reset_token
            }, status=status.HTTP_200_OK)
            
        except PasswordResetRequest.DoesNotExist:
            return Response(
                {'error': 'Code invalide'}, 
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
        
        try:
            reset_request = PasswordResetRequest.objects.get(
                reset_token=reset_token
            )
            
            if reset_request.is_expired:
                return Response(
                    {'error': 'Lien expiré'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            return Response(
                {'message': 'Token valide'}, 
                status=status.HTTP_200_OK
            )
            
        except PasswordResetRequest.DoesNotExist:
            return Response(
                {'error': 'Token invalide'}, 
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
            reset_request = PasswordResetRequest.objects.get(
                reset_token=reset_token
            )
            
            if reset_request.is_expired:
                return Response(
                    {'error': 'Token expiré'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Réinitialiser le mot de passe
            user = reset_request.user
            user.set_password(new_password)
            user.save()
            
            # Supprimer la demande de reset
            reset_request.delete()
            
            return Response(
                {'message': 'Mot de passe réinitialisé avec succès'}, 
                status=status.HTTP_200_OK
            )
            
        except PasswordResetRequest.DoesNotExist:
            return Response(
                {'error': 'Token invalide'}, 
                status=status.HTTP_400_BAD_REQUEST
            )


@GOOGLE_AUTH_SCHEMA
class GoogleAuthView(GenericAPIView):
    """Authentification Google OAuth2"""
    serializer_class = SocialAuthSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        # À implémenter avec social-auth-app-django
        return Response(
            {'message': 'Google Auth à implémenter'}, 
            status=status.HTTP_501_NOT_IMPLEMENTED
        )