from django.contrib.auth.backends import ModelBackend
from django.db.models import Q
from .models import CustomUser


class CustomAuthenticationBackend(ModelBackend):
    """Permet connexion via email OU téléphone"""
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None
            
        try:
            user = CustomUser.objects.get(
                Q(email=username) | Q(telephone=username)
            )
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
        except CustomUser.DoesNotExist:
            return None
        return None

    def get_user(self, user_id):
        try:
            return CustomUser.objects.get(pk=user_id)
        except CustomUser.DoesNotExist:
            return None