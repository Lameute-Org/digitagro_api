import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from knox.models import AuthToken
from apps.users.models import CustomUser

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Authentification via token Knox
        self.user = await self.get_user_from_token()
        
        if not self.user:
            await self.close(code=4001)
            return
        
        # Groupe personnel de l'utilisateur
        self.room_group_name = f'notifications_{self.user.id}'
        
        # Rejoindre le groupe
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Envoyer les notifications non lues
        await self.send_unread_notifications()
    
    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')
        
        if action == 'mark_read':
            notif_id = data.get('notification_id')
            await self.mark_notification_read(notif_id)
        
        elif action == 'mark_all_read':
            await self.mark_all_read()
    
    # Handler pour recevoir les notifications du groupe
    async def send_notification(self, event):
        await self.send(text_data=json.dumps(event['notification']))
    
    @database_sync_to_async
    def get_user_from_token(self):
        token = self.scope['query_string'].decode().split('token=')[-1]
        if not token:
            return None
        
        try:
            auth_token = AuthToken.objects.select_related('user').get(
                token_key=token[:8]
            )
            return auth_token.user if auth_token.user.is_active else None
        except AuthToken.DoesNotExist:
            return None
    
    @database_sync_to_async
    def send_unread_notifications(self):
        from .serializers import NotificationSerializer
        
        notifications = self.user.notifications.filter(is_read=False)[:20]
        serialized = NotificationSerializer(notifications, many=True).data
        
        return self.send(text_data=json.dumps({
            'type': 'unread_list',
            'notifications': serialized,
            'count': self.user.notifications.filter(is_read=False).count()
        }))
    
    @database_sync_to_async
    def mark_notification_read(self, notif_id):
        from .models import Notification
        try:
            notif = Notification.objects.get(id=notif_id, recipient=self.user)
            notif.mark_as_read()
        except Notification.DoesNotExist:
            pass
    
    @database_sync_to_async
    def mark_all_read(self):
        from django.utils import timezone
        self.user.notifications.filter(is_read=False).update(
            is_read=True,
            read_at=timezone.now()
        )