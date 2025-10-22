# apps/users/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Producteur
from .services import BadgeService


@receiver(post_save, sender=Producteur)
def check_organization_badge(sender, instance, created, **kwargs):
    """
    Vérifie et attribue/révoque le badge organisation lors de la modification
    du profil producteur.
    """
    if not created:  # Uniquement lors des modifications
        if instance.has_organization_badge:
            # Attribuer badge si membre GIC/Coop
            BadgeService.check_and_award_automatic_badges(instance.user)
        else:
            # Révoquer badge si plus membre
            BadgeService.remove_organization_badge_if_needed(instance.user)