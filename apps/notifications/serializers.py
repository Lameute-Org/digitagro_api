from rest_framework import serializers
from .models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    icon = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = [
            'id', 'type', 'icon', 'title', 'message', 
            'data', 'is_read', 'read_at', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_icon(self, obj):
        return dict(obj.TYPE_CHOICES).get(obj.type, '🔔')
