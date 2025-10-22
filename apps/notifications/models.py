# ==================== apps/notifications/models.py ====================
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from apps.users.models import CustomUser
from rest_framework.decorators import action

class Notification(models.Model):
    TYPE_CHOICES = [
        # Production
        ('new_order', '📋 Nouvelle commande'),
        ('payment_received', '💰 Paiement reçu'),
        ('order_confirmed', '✅ Commande confirmée'),
        ('product_shipped', '📦 Produit expédié'),
        ('delivery_completed', '✅ Livraison effectuée'),
        ('new_review', '⭐ Nouvelle évaluation'),
        
        # Transport
        ('transport_request', '🚚 Demande de transport'),
        ('transport_confirmed', '✅ Transport confirmé'),
        ('transport_started', '📍 Transport démarré'),
        ('transport_arrived', '🎯 Transport arrivé'),
        
        # Transformation
        ('transformation_request', '🏭 Demande transformation'),
        ('transformation_completed', '✅ Transformation terminée'),
        ('products_ready', '📦 Produits prêts'),
        
        # Distribution
        ('stock_updated', '📦 Stock mis à jour'),
        ('bulk_order', '💼 Commande en gros'),
        
        # Messages
        ('new_message', '💬 Nouveau message'),
        
        # Système
        ('new_device', '🔒 Nouvelle connexion'),
        ('password_changed', '🔑 Mot de passe modifié'),
        ('profile_incomplete', '⚠️ Profil incomplet'),
        
        # Alertes
        ('delivery_delayed', '⚠️ Retard livraison'),
        ('order_cancelled', '❌ Commande annulée'),
        ('refund_requested', '💰 Remboursement demandé'),
    ]
    
    recipient = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='notifications',
        db_index=True
    )
    type = models.CharField(max_length=30, choices=TYPE_CHOICES, db_index=True)
    title = models.CharField(max_length=200)
    message = models.TextField()
    
    # Lien générique vers l'objet concerné (Commande, Transport, etc.)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True)
    object_id = models.PositiveIntegerField(null=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Métadonnées
    data = models.JSONField(default=dict, blank=True)  # Données supplémentaires
    is_read = models.BooleanField(default=False, db_index=True)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', '-created_at']),
            models.Index(fields=['recipient', 'is_read', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_type_display()} - {self.recipient.email}"

    @action(detail=True, methods=['post'])
    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            from django.utils import timezone
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])