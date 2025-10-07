# apps/notifications/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from .models import Notification
from .serializers import NotificationSerializer
from .docs.notifications_swagger import (
    NOTIFICATIONS_LIST_SCHEMA,
    UNREAD_NOTIFICATIONS_SCHEMA,
    MARK_READ_SCHEMA,
    MARK_ALL_READ_SCHEMA,
    CLEAR_ALL_SCHEMA
)

class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    
    @NOTIFICATIONS_LIST_SCHEMA
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    def get_queryset(self):
        return self.request.user.notifications.select_related('content_type').all()
    
    @action(detail=False, methods=['get'])
    @UNREAD_NOTIFICATIONS_SCHEMA
    def unread(self, request):
        notifications = self.get_queryset().filter(is_read=False)[:50]
        serializer = self.get_serializer(notifications, many=True)
        return Response({
            'count': self.get_queryset().filter(is_read=False).count(),
            'results': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    @MARK_READ_SCHEMA
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.mark_as_read()
        return Response({'status': 'marked_as_read'})
    
    @action(detail=False, methods=['post'])
    @MARK_ALL_READ_SCHEMA
    def mark_all_read(self, request):
        count = self.get_queryset().filter(is_read=False).update(
            is_read=True,
            read_at=timezone.now()
        )
        return Response({'marked_count': count})
    
    @action(detail=False, methods=['delete'])
    @CLEAR_ALL_SCHEMA
    def clear_all(self, request):
        count, _ = self.get_queryset().delete()
        return Response({'deleted_count': count})