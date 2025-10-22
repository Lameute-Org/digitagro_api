# apps/users/services.py

from twilio.rest import Client
from django.conf import settings
from django.db import models
from django.utils import timezone
from .models import UserBadge
import logging

logger = logging.getLogger(__name__)

class TwilioService:
    """Service d'envoi SMS via Twilio"""
    
    def __init__(self):
        self.client = Client(
            settings.TWILIO_ACCOUNT_SID,
            settings.TWILIO_AUTH_TOKEN
        )
        self.from_number = settings.TWILIO_PHONE_NUMBER
    
    def send_verification_sms(self, phone_number, code):
        """
        Envoie un code de vérification par SMS.
        
        Args:
            phone_number (str): Numéro au format international (+237...)
            code (str): Code 5 chiffres
        
        Returns:
            tuple: (success, message_sid_or_error)
        """
        try:
            message = self.client.messages.create(
                body=f"🌾 DIGITAGRO\n\nVotre code de vérification : {code}\n\nValide 5 minutes.",
                from_=self.from_number,
                to=phone_number
            )
            
            logger.info(f"SMS envoyé avec succès à {phone_number} - SID: {message.sid}")
            return True, message.sid
            
        except Exception as e:
            logger.error(f"Erreur envoi SMS à {phone_number}: {str(e)}")
            return False, str(e)
    
    @staticmethod
    def validate_cameroon_phone(phone_number):
        """
        Valide format numéro camerounais.
        
        Formats acceptés :
        - +237XXXXXXXXX (international)
        - 237XXXXXXXXX
        - 6XXXXXXXX ou 2XXXXXXXX (local)
        
        Returns:
            str: Numéro normalisé au format international ou None
        """
        import re
        
        # Nettoyer
        phone = re.sub(r'[^\d+]', '', phone_number)
        
        # Déjà au format international
        if phone.startswith('+237') and len(phone) == 13:
            return phone
        
        # Format avec 237 sans +
        if phone.startswith('237') and len(phone) == 12:
            return f'+{phone}'
        
        # Format local (6XX ou 2XX)
        if len(phone) == 9 and phone[0] in ['6', '2']:
            return f'+237{phone}'
        
        return None
    


class BadgeService:
    """Gestion automatique et manuelle des badges utilisateur"""
    
    @staticmethod
    def award_badge(user, badge_type, awarded_by=None, metadata=None):
        """
        Attribue un badge à un utilisateur.
        
        Args:
            user: Instance CustomUser
            badge_type: Type de badge (voir UserBadge.BADGE_TYPES)
            awarded_by: Utilisateur qui attribue (admin) - None si automatique
            metadata: Données supplémentaires (dict)
        
        Returns:
            tuple: (badge: UserBadge, created: bool)
        """
        from .models import UserBadge
        
        badge, created = UserBadge.objects.get_or_create(
            user=user,
            badge_type=badge_type,
            defaults={
                'is_active': True,
                'awarded_by': awarded_by,
                'metadata': metadata or {}
            }
        )
        
        # Si badge existait mais était inactif, le réactiver
        if not created and not badge.is_active:
            badge.is_active = True
            badge.awarded_at = timezone.now()
            badge.awarded_by = awarded_by
            badge.metadata = metadata or badge.metadata
            badge.save(update_fields=['is_active', 'awarded_at', 'awarded_by', 'metadata'])
        
        if created:
            logger.info(f"Badge '{badge_type}' attribué à {user.email}")
        
        return badge, created
    
    @staticmethod
    def revoke_badge(user, badge_type):
        """
        Révoque un badge (le désactive).
        
        Args:
            user: Instance CustomUser
            badge_type: Type de badge à révoquer
        
        Returns:
            bool: True si révoqué, False si badge inexistant
        """
        from .models import UserBadge
        
        updated = UserBadge.objects.filter(
            user=user,
            badge_type=badge_type,
            is_active=True
        ).update(is_active=False)
        
        if updated:
            logger.info(f"Badge '{badge_type}' révoqué pour {user.email}")
        
        return updated > 0
    
    @staticmethod
    def check_and_award_automatic_badges(user):
        """
        Vérifie et attribue tous les badges automatiques selon les conditions.
        
        Badges automatiques :
        - phone_verified : Si téléphone vérifié
        - organization_member : Si membre GIC ou Coopérative
        
        Args:
            user: Instance CustomUser
        
        Returns:
            list: Liste des badges attribués (instances UserBadge)
        """
        badges_awarded = []
        
        # Badge téléphone vérifié
        if user.phone_verified and not user.has_badge('phone_verified'):
            badge, created = BadgeService.award_badge(
                user,
                'phone_verified',
                metadata={'verified_at': user.phone_verified_at.isoformat() if user.phone_verified_at else None}
            )
            if created:
                badges_awarded.append(badge)
        
        # Badge organisation (GIC/Coopérative)
        if hasattr(user, 'producteur') and user.producteur.has_organization_badge:
            if not user.has_badge('organization_member'):
                org_info = user.producteur.organization_info
                badge, created = BadgeService.award_badge(
                    user,
                    'organization_member',
                    metadata={
                        'organization_type': org_info.get('type') if org_info else None,
                        'organization_name': org_info.get('name') if org_info else None
                    }
                )
                if created:
                    badges_awarded.append(badge)
        
        return badges_awarded
    
    @staticmethod
    def remove_organization_badge_if_needed(user):
        """
        Révoque le badge organisation si l'utilisateur n'est plus membre.
        Appelé lors de la modification du profil producteur.
        """
        if hasattr(user, 'producteur'):
            if not user.producteur.has_organization_badge and user.has_badge('organization_member'):
                BadgeService.revoke_badge(user, 'organization_member')
    
    @staticmethod
    def get_user_badges_summary(user):
        """
        Retourne un résumé des badges de l'utilisateur.
        Optimisé avec list comprehension.
        
        Returns:
            list: Liste de dicts avec infos badges
        """
        badges = user.get_active_badges()
        
        return [
            {
                'type': badge.badge_type,
                'name': badge.display_name,
                'icon': badge.icon,
                'awarded_at': badge.awarded_at,
                'metadata': badge.metadata
            }
            for badge in badges
        ]
    
    @staticmethod
    def check_eligibility_for_badge(user, badge_type):
        """
        Vérifie si un utilisateur est éligible pour un badge donné.
        
        Args:
            user: Instance CustomUser
            badge_type: Type de badge à vérifier
        
        Returns:
            tuple: (eligible: bool, reason: str)
        """
        # Règles d'éligibilité
        eligibility_rules = {
            'phone_verified': lambda u: (
                u.phone_verified,
                "Téléphone vérifié" if u.phone_verified else "Téléphone non vérifié"
            ),
            'organization_member': lambda u: (
                hasattr(u, 'producteur') and u.producteur.has_organization_badge,
                "Membre GIC/Coopérative" if hasattr(u, 'producteur') and u.producteur.has_organization_badge else "Non membre d'une organisation"
            ),
        }
        
        rule = eligibility_rules.get(badge_type)
        if rule:
            return rule(user)
        
        return False, "Badge non automatique ou inexistant"