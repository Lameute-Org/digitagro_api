# ==================== apps/notifications/signals.py ====================
from django.db.models.signals import post_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Notification
from .serializers import NotificationSerializer

@receiver(post_save, sender=Notification)
def notify_user(sender, instance, created, **kwargs):
    if not created:
        return
    
    channel_layer = get_channel_layer()
    room_group_name = f'notifications_{instance.recipient.id}'
    
    # Sérialiser la notification
    serialized = NotificationSerializer(instance).data
    
    # Envoyer au groupe WebSocket de l'utilisateur
    async_to_sync(channel_layer.group_send)(
        room_group_name,
        {
            'type': 'send_notification',
            'notification': {
                'type': 'new_notification',
                'data': serialized
            }
        }
    )
