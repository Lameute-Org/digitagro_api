# apps/production/permissions.py
from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsProducteurOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        # Lecture : authentification requise
        if request.method in SAFE_METHODS:
            return request.user and request.user.is_authenticated
        # Création : producteur uniquement
        return hasattr(request.user, 'producteur')
    
    def has_object_permission(self, request, view, obj):
        # Lecture : utilisateur authentifié
        if request.method in SAFE_METHODS:
            return request.user and request.user.is_authenticated
        # Modification/Suppression : propriétaire uniquement
        return obj.producteur.user == request.user


class IsCommandeOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.client == request.user or obj.production.producteur.user == request.user