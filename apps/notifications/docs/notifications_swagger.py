# apps/notifications/docs/notifications_swagger.py
from drf_spectacular.utils import extend_schema, OpenApiExample
from rest_framework import status

CONTENT_TYPE_JSON = 'application/json'
TAG_NOTIFICATIONS = 'Notifications'

# ==================== LIST NOTIFICATIONS ====================
NOTIFICATIONS_LIST_SCHEMA = extend_schema(
    operation_id="list_notifications",
    summary="Liste des notifications",
    description="Récupère toutes les notifications de l'utilisateur connecté (paginé)",
    responses={
        200: {
            'description': 'Liste des notifications',
            'content': {
                CONTENT_TYPE_JSON: {
                    'example': {
                        'count': 42,
                        'next': 'http://api/notifications/?page=2',
                        'previous': None,
                        'results': [
                            {
                                'id': 1,
                                'type': 'new_order',
                                'icon': '📋',
                                'title': 'Nouvelle commande reçue',
                                'message': 'Jean Dupont - 50 Tomates',
                                'data': {'order_id': 1, 'amount': 25000},
                                'is_read': False,
                                'read_at': None,
                                'created_at': '2025-01-15T10:30:00Z'
                            },
                            {
                                'id': 2,
                                'type': 'payment_received',
                                'icon': '💰',
                                'title': 'Paiement reçu',
                                'message': '25000 FCFA reçu',
                                'data': {'amount': 25000},
                                'is_read': True,
                                'read_at': '2025-01-15T11:00:00Z',
                                'created_at': '2025-01-15T10:45:00Z'
                            }
                        ]
                    }
                }
            }
        },
        401: {'description': 'Non authentifié'}
    },
    tags=[TAG_NOTIFICATIONS]
)

# ==================== UNREAD NOTIFICATIONS ====================
UNREAD_NOTIFICATIONS_SCHEMA = extend_schema(
    operation_id="unread_notifications",
    summary="Notifications non lues",
    description="Liste des 50 dernières notifications non lues",
    responses={
        200: {
            'description': 'Notifications non lues',
            'content': {
                CONTENT_TYPE_JSON: {
                    'example': {
                        'count': 5,
                        'results': [
                            {
                                'id': 1,
                                'type': 'new_order',
                                'icon': '📋',
                                'title': 'Nouvelle commande reçue',
                                'message': 'Jean Dupont - 50 Tomates',
                                'data': {'order_id': 1, 'amount': 25000},
                                'is_read': False,
                                'read_at': None,
                                'created_at': '2025-01-15T10:30:00Z'
                            }
                        ]
                    }
                }
            }
        },
        401: {'description': 'Non authentifié'}
    },
    tags=[TAG_NOTIFICATIONS]
)

# ==================== MARK AS READ ====================
MARK_READ_SCHEMA = extend_schema(
    operation_id="mark_notification_read",
    summary="Marquer comme lue",
    description="Marque une notification spécifique comme lue",
    request=None,
    responses={
        200: {
            'description': 'Notification marquée comme lue',
            'content': {
                CONTENT_TYPE_JSON: {
                    'example': {'status': 'marked_as_read'}
                }
            }
        },
        404: {'description': 'Notification non trouvée'}
    },
    tags=[TAG_NOTIFICATIONS]
)

# ==================== MARK ALL READ ====================
MARK_ALL_READ_SCHEMA = extend_schema(
    operation_id="mark_all_notifications_read",
    summary="Tout marquer comme lu",
    description="Marque toutes les notifications comme lues",
    request=None,
    responses={
        200: {
            'description': 'Toutes marquées comme lues',
            'content': {
                CONTENT_TYPE_JSON: {
                    'example': {'marked_count': 5}
                }
            }
        }
    },
    tags=[TAG_NOTIFICATIONS]
)

# ==================== CLEAR ALL ====================
CLEAR_ALL_SCHEMA = extend_schema(
    operation_id="clear_all_notifications",
    summary="Supprimer toutes les notifications",
    description="Supprime définitivement toutes les notifications",
    request=None,
    responses={
        200: {
            'description': 'Notifications supprimées',
            'content': {
                CONTENT_TYPE_JSON: {
                    'example': {'deleted_count': 42}
                }
            }
        }
    },
    tags=[TAG_NOTIFICATIONS]
)

# ==================== WEBSOCKET INFO ====================
WEBSOCKET_INFO_SCHEMA = """
## 🔌 WebSocket Temps Réel

### Connexion
```javascript
const token = 'votre_token_knox';
const ws = new WebSocket(
    `ws://185.217.125.37:8001/ws/notifications/?token=${token}`
);

ws.onopen = () => {
    console.log('✅ Connecté aux notifications');
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    if (data.type === 'unread_list') {
        // Liste initiale des non lues
        console.log('📋 Non lues:', data.notifications);
        console.log('🔢 Total:', data.count);
    } 
    else if (data.type === 'new_notification') {
        // Nouvelle notification en temps réel
        console.log('🔔 Nouvelle:', data.data);
        showNotification(data.data);
    }
};

ws.onerror = (error) => {
    console.error('❌ Erreur WebSocket:', error);
};

ws.onclose = () => {
    console.log('🔌 Déconnecté');
};
```

### Actions WebSocket

**Marquer comme lue:**
```javascript
ws.send(JSON.stringify({
    action: 'mark_read',
    notification_id: 123
}));
```

**Tout marquer comme lu:**
```javascript
ws.send(JSON.stringify({
    action: 'mark_all_read'
}));
```

### Événements Reçus

**1. Liste initiale (connexion):**
```json
{
    "type": "unread_list",
    "notifications": [...],
    "count": 5
}
```

**2. Nouvelle notification:**
```json
{
    "type": "new_notification",
    "data": {
        "id": 1,
        "type": "new_order",
        "icon": "📋",
        "title": "Nouvelle commande",
        "message": "Jean Dupont - 50 Tomates",
        "data": {"order_id": 1, "amount": 25000},
        "is_read": false,
        "created_at": "2025-01-15T10:30:00Z"
    }
}
```

### React Hook Exemple

```javascript
import { useState, useEffect } from 'react';

const useNotifications = (token) => {
    const [notifications, setNotifications] = useState([]);
    const [unreadCount, setUnreadCount] = useState(0);
    const [ws, setWs] = useState(null);
    
    useEffect(() => {
        const websocket = new WebSocket(
            `ws://185.217.125.37:8001/ws/notifications/?token=${token}`
        );
        
        websocket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            
            if (data.type === 'unread_list') {
                setNotifications(data.notifications);
                setUnreadCount(data.count);
            } else if (data.type === 'new_notification') {
                setNotifications(prev => [data.data, ...prev]);
                setUnreadCount(prev => prev + 1);
            }
        };
        
        setWs(websocket);
        
        return () => websocket.close();
    }, [token]);
    
    const markAsRead = (notifId) => {
        ws?.send(JSON.stringify({
            action: 'mark_read',
            notification_id: notifId
        }));
    };
    
    const markAllAsRead = () => {
        ws?.send(JSON.stringify({action: 'mark_all_read'}));
    };
    
    return { notifications, unreadCount, markAsRead, markAllAsRead };
};

export default useNotifications;
```
"""