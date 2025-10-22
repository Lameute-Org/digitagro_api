# apps/users/views.py
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
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
from django.db.models import Q
from django.db import transaction
from django.utils import timezone
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from datetime import timedelta
from drf_spectacular.utils import extend_schema, OpenApiExample

from .models import (
    CustomUser, PasswordResetRequest, PhoneVerification,
    Producteur, Transporteur, Transformateur, Distributeur, Consommateur
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
    SocialAuthSerializer,
    PhoneVerificationRequestSerializer,  # NOUVEAU
    PhoneVerificationCodeSerializer,      # NOUVEAU
)
from .permissions import IsProfileCompleted, IsOwnerOrReadOnly
from .services import BadgeService, TwilioService  # NOUVEAU
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
    PASSWORD_RESET_CONFIRM_SCHEMA,
    # NOUVEAUX SCHEMAS
    PHONE_VERIFICATION_REQUEST_SCHEMA,
    PHONE_VERIFICATION_CODE_SCHEMA,
)


# ==================== NOUVEAU : VÉRIFICATION SMS ====================

class PhoneVerificationViewSet(viewsets.GenericViewSet):
    """Gestion vérification téléphone par SMS (Twilio)"""
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'request_code':
            return PhoneVerificationRequestSerializer
        return PhoneVerificationCodeSerializer
    
    @PHONE_VERIFICATION_REQUEST_SCHEMA
    @action(detail=False, methods=['post'])
    def request_code(self, request):
        """
        Demande d'envoi de code SMS de vérification.
        
        Rate limit : 3 tentatives par heure
        Code valide : 5 minutes
        """
        user = request.user
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        phone_number = serializer.validated_data['phone_number']
        
        # Validation rate limit
        if not user.can_request_sms():
            next_attempt = user.last_sms_attempt + timedelta(hours=1)
            return Response({
                'error': 'Trop de tentatives. Réessayez dans 1 heure.',
                'retry_after': next_attempt,
                'attempts_remaining': 0
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        # Validation et normalisation numéro
        normalized_phone = TwilioService.validate_cameroon_phone(phone_number)
        if not normalized_phone:
            return Response({
                'error': 'Numéro de téléphone invalide',
                'format_attendu': '+237XXXXXXXXX ou 6XXXXXXXX'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Vérifier si numéro déjà vérifié par un autre utilisateur
        if CustomUser.objects.filter(
            telephone=normalized_phone,
            phone_verified=True
        ).exclude(id=user.id).exists():
            return Response({
                'error': 'Ce numéro est déjà vérifié par un autre compte'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Créer vérification
        verification = PhoneVerification.objects.create(
            user=user,
            phone_number=normalized_phone,
            ip_address=self._get_client_ip(request)
        )
        
        # Envoyer SMS via Twilio
        twilio_service = TwilioService()
        success, result = twilio_service.send_verification_sms(
            normalized_phone,
            verification.code
        )
        
        if success:
            # Mise à jour rate limit
            user.sms_attempts_count += 1
            user.last_sms_attempt = timezone.now()
            user.save(update_fields=['sms_attempts_count', 'last_sms_attempt'])
            
            verification.twilio_sid = result
            verification.save(update_fields=['twilio_sid'])
            
            return Response({
                'message': 'Code envoyé avec succès',
                'phone_number': normalized_phone,
                'expires_in': 300,  # 5 minutes
                'can_resend_at': user.last_sms_attempt + timedelta(minutes=2)
            }, status=status.HTTP_200_OK)
        
        # Échec envoi SMS
        verification.delete()
        return Response({
            'error': f'Erreur envoi SMS : {result}',
            'details': 'Vérifiez votre numéro ou contactez le support'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @PHONE_VERIFICATION_CODE_SCHEMA
    @action(detail=False, methods=['post'])
    def verify_code(self, request):
        """Vérification du code SMS avec attribution automatique du badge"""
        user = request.user
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        code = serializer.validated_data['code']
        
        try:
            verification = PhoneVerification.objects.filter(
                user=user,
                verified=False
            ).latest('created_at')
        except PhoneVerification.DoesNotExist:
            return Response({
                'error': 'Aucune vérification en cours',
                'action': 'Demandez un nouveau code'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not verification.is_valid:
            if verification.is_expired:
                return Response({
                    'error': 'Code expiré',
                    'action': 'Demandez un nouveau code'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if verification.attempts >= 3:
                return Response({
                    'error': 'Trop de tentatives',
                    'action': 'Demandez un nouveau code'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        verification.attempts += 1
        verification.save(update_fields=['attempts'])
        
        if verification.code != code:
            return Response({
                'error': 'Code incorrect',
                'attempts_remaining': 3 - verification.attempts
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # ✅ CODE VALIDE - Activer vérification + Badge
        with transaction.atomic():
            verification.verified = True
            verification.verified_at = timezone.now()
            verification.save(update_fields=['verified', 'verified_at'])
            
            user.telephone = verification.phone_number
            user.phone_verified = True
            user.phone_verified_at = timezone.now()
            user.save(update_fields=[
                'telephone',
                'phone_verified',
                'phone_verified_at'
            ])
            
            # ========== ATTRIBUTION BADGE AUTOMATIQUE ==========
            BadgeService.check_and_award_automatic_badges(user)
        
        # Recharger l'utilisateur avec les badges
        user.refresh_from_db()
        
        return Response({
            'message': 'Téléphone vérifié avec succès',
            'phone_verified': True,
            'can_become_producer': user.check_producer_requirements()[0],
            'verified_at': user.phone_verified_at,
            'badges': BadgeService.get_user_badges_summary(user)  # NOUVEAU
        }, status=status.HTTP_200_OK)
    
    
    def _get_client_ip(self, request):
        """Récupère l'IP du client pour logs"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        return x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')

# APRÈS PhoneVerificationViewSet

class DevPhoneVerificationViewSet(viewsets.GenericViewSet):
    """MODE DEV UNIQUEMENT - Bypass SMS"""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(exclude=True)  # Caché dans Swagger
    @action(detail=False, methods=['post'])
    def dev_verify(self, request):
        """DEV: Auto-vérifie sans SMS"""
        if not settings.DEBUG:
            return Response({'error': 'Mode DEV uniquement'}, status=403)
        
        user = request.user
        phone = request.data.get('phone_number')
        
        normalized = TwilioService.validate_cameroon_phone(phone)
        if not normalized:
            return Response({'error': 'Numéro invalide'}, status=400)
        
        with transaction.atomic():
            user.telephone = normalized
            user.phone_verified = True
            user.phone_verified_at = timezone.now()
            user.save(update_fields=['telephone', 'phone_verified', 'phone_verified_at'])
            
            BadgeService.check_and_award_automatic_badges(user)
        
        return Response({
            'message': 'Téléphone vérifié (MODE DEV)',
            'phone_verified': True,
            'badges': BadgeService.get_user_badges_summary(user)
        }, status=200)
# ==================== VIEWS EXISTANTES (Inchangées) ====================

@USER_REGISTRATION_SCHEMA
class UserRegistrationView(CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        instance, token = AuthToken.objects.create(user)
        
        return Response({
            'user': UserProfileSerializer(user).data,
            'token': token,
            'expiry': instance.expiry
        }, status=status.HTTP_201_CREATED)


@LOGIN_SCHEMA
class CustomLoginView(KnoxLoginView):
    permission_classes = [AllowAny]

    def post(self, request, format=None):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        login(request, user)
        
        return super(CustomLoginView, self).post(request, format=None)

    def get_post_response_data(self, request, token, instance):
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
    permission_classes = [IsAuthenticated]


@LOGOUT_ALL_SCHEMA
class CustomLogoutAllView(KnoxLogoutAllView):
    permission_classes = [IsAuthenticated]


class UserProfileView(RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def get_object(self):
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
    serializer_class = ProfileCompletionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user


@ROLE_ACTIVATION_SCHEMA
class RoleActivationView(CreateAPIView):
    serializer_class = RoleActivationSerializer
    permission_classes = [IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        can_activate, error_msg = request.user.check_producer_requirements()
        
        if not can_activate:
            return Response(
                {'error': error_msg},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # ========== ATTRIBUTION BADGES AUTOMATIQUES ==========
        BadgeService.check_and_award_automatic_badges(user)
        
        user_with_roles = CustomUser.objects.select_related(
            'producteur', 'transporteur', 'transformateur',
            'distributeur', 'consommateur'
        ).prefetch_related('badges').get(pk=user.pk)
        
        return Response({
            'message': f'Rôle {request.data.get("role")} activé avec succès',
            'user': UserProfileSerializer(user_with_roles).data
        }, status=status.HTTP_200_OK)
@ROLES_STATUS_SCHEMA
class UserRolesStatusView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        roles_status = {
            'active_roles': user.get_active_roles(),
            'available_roles': {
                role: {
                    'active': getattr(user, f'is_{role}'),
                    'verified': getattr(user, f'is_{role}_verified'),
                    'activated_at': getattr(user, f'{role}_activated_at')
                }
                for role in ['producteur', 'transporteur', 'transformateur', 'distributeur']
            },
            'profile_completed': user.profile_completed,
            'phone_verified': user.phone_verified  # NOUVEAU
        }
        
        return Response(roles_status, status=status.HTTP_200_OK)


# ==================== PASSWORD RESET (Inchangé) ====================

@PASSWORD_RESET_REQUEST_SCHEMA
class PasswordResetRequestView(CreateAPIView):
    serializer_class = PasswordResetRequestSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        identifier = serializer.validated_data['identifier']
        
        try:
            user = CustomUser.objects.only('id', 'email', 'nom', 'prenom').get(
                Q(email=identifier) | Q(telephone=identifier)
            )
        except CustomUser.DoesNotExist:
            return Response(
                {'message': 'Si cet utilisateur existe, un email a été envoyé'},
                status=status.HTTP_200_OK
            )
        
        PasswordResetRequest.objects.filter(
            user=user,
            expires_at__lt=timezone.now()
        ).delete()
        
        reset_request = PasswordResetRequest.objects.create(user=user)
        
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
    serializer_class = OTPVerificationSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        otp_code = serializer.validated_data['otp_code']
        
        try:
            reset_request = PasswordResetRequest.objects.select_for_update().get(
                user__email=email,
                otp_code=otp_code,
                is_validated=False,
                expires_at__gt=timezone.now()
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
    serializer_class = TokenValidationSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        reset_token = serializer.validated_data['reset_token']
        
        valid = PasswordResetRequest.objects.filter(
            reset_token=reset_token,
            expires_at__gt=timezone.now()
        ).exists()
        
        return Response(
            {'message': 'Token valide'} if valid else {'error': 'Token invalide ou expiré'},
            status=status.HTTP_200_OK if valid else status.HTTP_400_BAD_REQUEST
        )


@PASSWORD_RESET_CONFIRM_SCHEMA
class PasswordResetConfirmView(GenericAPIView):
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
            
            user = reset_request.user
            user.set_password(new_password)
            user.save(update_fields=['password'])
            
            reset_request.delete()
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
    serializer_class = SocialAuthSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        return Response(
            {'message': 'Google Auth à implémenter'},
            status=status.HTTP_501_NOT_IMPLEMENTED
        )
    
class UserBadgesView(APIView):
    """Consultation des badges de l'utilisateur connecté"""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        operation_id="get_user_badges",
        summary="Mes badges",
        description="Liste des badges actifs de l'utilisateur connecté avec leurs conditions d'obtention",
        responses={
            200: {
                'description': 'Badges de l\'utilisateur',
                'content': {
                    'application/json': {
                        'example': {
                            'badges': [
                                {
                                    'type': 'phone_verified',
                                    'name': '📱 Téléphone Vérifié',
                                    'icon': '📱',
                                    'awarded_at': '2024-01-15T10:30:00Z',
                                    'metadata': {'verified_at': '2024-01-15T10:30:00Z'}
                                },
                                {
                                    'type': 'organization_member',
                                    'name': '🏢 Membre GIC/Coopérative',
                                    'icon': '🏢',
                                    'awarded_at': '2024-01-15T10:35:00Z',
                                    'metadata': {
                                        'organization_type': 'GIC',
                                        'organization_name': 'GIC ESPOIR AGRICOLE'
                                    }
                                }
                            ],
                            'total_badges': 2
                        }
                    }
                }
            }
        },
        tags=['Badges']
    )
    def get(self, request):
        """Récupère les badges de l'utilisateur"""
        badges = BadgeService.get_user_badges_summary(request.user)
        
        return Response({
            'badges': badges,
            'total_badges': len(badges)
        }, status=status.HTTP_200_OK)