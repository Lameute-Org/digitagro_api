from django.urls import path, include
from knox import views as knox_views
from .views import (
    UserRegistrationView,
    CustomLoginView,
    UserProfileView,
    CompleteProfileView,
    PasswordResetRequestView,
    OTPVerificationView,
    TokenValidationView,
    PasswordResetConfirmView,
    GoogleAuthView
)

urlpatterns = [
    # Authentification Knox
    path('register/', UserRegistrationView.as_view(), name='user-register'),
    path('login/', CustomLoginView.as_view(), name='knox-login'),
    path('logout/', knox_views.LogoutView.as_view(), name='knox-logout'),
    path('logoutall/', knox_views.LogoutAllView.as_view(), name='knox-logoutall'),
    
    # Profil utilisateur
    path('me/', UserProfileView.as_view(), name='user-profile'),
    path('me/complete-profile/', CompleteProfileView.as_view(), name='complete-profile'),
    
    # Reset password
    path('password/request-reset/', PasswordResetRequestView.as_view(), name='password-request-reset'),
    path('password/verify-otp/', OTPVerificationView.as_view(), name='password-verify-otp'),
    path('password/validate-token/', TokenValidationView.as_view(), name='password-validate-token'),
    path('password/reset-confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    
    # Social Auth
    path('google/', GoogleAuthView.as_view(), name='google-auth'),
]