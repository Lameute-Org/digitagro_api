# apps/users/urls.py
from django.urls import path
from .views import (
    CustomLogoutAllView,
    CustomLogoutView,
    DevPhoneVerificationViewSet,
    UserRegistrationView,
    CustomLoginView,
    UserProfileView,
    CompleteProfileView,
    RoleActivationView,
    UserRolesStatusView,
    PasswordResetRequestView,
    OTPVerificationView,
    TokenValidationView,
    PasswordResetConfirmView,
    GoogleAuthView,
    PhoneVerificationViewSet,
    UserBadgesView  # NOUVEAU
)

urlpatterns = [
    # Authentification
    path('register/', UserRegistrationView.as_view(), name='user-register'),
    path('login/', CustomLoginView.as_view(), name='knox-login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('logoutall/', CustomLogoutAllView.as_view(), name='logoutall'),
    
    # Profil utilisateur
    path('me/', UserProfileView.as_view(), name='user-profile'),
    path('me/complete-profile/', CompleteProfileView.as_view(), name='complete-profile'),
    
    # Vérification SMS
    path('phone/request-code/', 
         PhoneVerificationViewSet.as_view({'post': 'request_code'}),
         name='phone-request-code'),
    path('phone/verify-code/',
         PhoneVerificationViewSet.as_view({'post': 'verify_code'}),
         name='phone-verify-code'),
    
    # ========== NOUVEAU : BADGES ==========
    path('me/badges/', UserBadgesView.as_view(), name='user-badges'),
    
    # Gestion des rôles
    path('activate-role/', RoleActivationView.as_view(), name='activate-role'),
    path('roles-status/', UserRolesStatusView.as_view(), name='roles-status'),
    path('phone/dev-verify/', DevPhoneVerificationViewSet.as_view({'post': 'dev_verify'}),
         name='phone-dev-verify'),

    
    # Reset password
    path('password/request-reset/', PasswordResetRequestView.as_view(), name='password-request-reset'),
    path('password/verify-otp/', OTPVerificationView.as_view(), name='password-verify-otp'),
    path('password/validate-token/', TokenValidationView.as_view(), name='password-validate-token'),
    path('password/reset-confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    
    # Social Auth
    path('google/', GoogleAuthView.as_view(), name='google-auth'),
]