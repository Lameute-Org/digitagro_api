# apps/production/permissions.py
from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsProducteurOrReadOnly(BasePermission):
    """Permet la lecture à tous, mais seuls les producteurs peuvent créer"""
    
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


class IsProducteurOwner(BasePermission):
    """Vérifie que l'utilisateur est le propriétaire de la production"""
    
    def has_object_permission(self, request, view, obj):
        # L'utilisateur doit être producteur et propriétaire de la production
        return (
            request.user.is_authenticated and 
            hasattr(request.user, 'producteur') and 
            obj.producteur.user == request.user
        )


class IsCommandeOwner(BasePermission):
    """Vérifie que l'utilisateur est le client ou le producteur de la commande"""
    
    def has_object_permission(self, request, view, obj):
        return (
            obj.client == request.user or 
            obj.production.producteur.user == request.user
        )


class CanBecomeProducteur(BasePermission):
    """
    Vérifie que l'utilisateur peut devenir producteur.
    Nécessite un profil complété.
    """
    message = "Complétez votre profil (nom, prénom, téléphone, adresse) avant de devenir producteur."
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Si déjà producteur, autoriser
        if request.user.is_producteur:
            return True
        
        # Si création de production (POST), vérifier profil complété
        if request.method == 'POST':
            return request.user.profile_completed
        
        # Pour les autres méthodes (GET, etc.), autoriser
        return True