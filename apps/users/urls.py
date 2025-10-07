from django.urls import path
from .views import (
    CustomLogoutAllView,
    CustomLogoutView,
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
    GoogleAuthView
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
    
    # Gestion des rôles
    path('activate-role/', RoleActivationView.as_view(), name='activate-role'),
    path('roles-status/', UserRolesStatusView.as_view(), name='roles-status'),
    
    # Reset password
    path('password/request-reset/', PasswordResetRequestView.as_view(), name='password-request-reset'),
    path('password/verify-otp/', OTPVerificationView.as_view(), name='password-verify-otp'),
    path('password/validate-token/', TokenValidationView.as_view(), name='password-validate-token'),
    path('password/reset-confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    
    # Social Auth
    path('google/', GoogleAuthView.as_view(), name='google-auth'),
]