from rest_framework.permissions import BasePermission


class IsProfileCompleted(BasePermission):
    """
    Permission pour vérifier si le profil utilisateur est complété
    """
    message = "Vous devez compléter votre profil pour accéder à cette ressource."
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.profile_completed
    
    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)


class IsOwnerOrReadOnly(BasePermission):
    """
    Permission pour autoriser seulement le propriétaire à modifier
    """
    
    def has_object_permission(self, request, view, obj):
        # Permissions de lecture pour tous les utilisateurs authentifiés
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        # Permissions d'écriture seulement pour le propriétaire
        return obj == request.user