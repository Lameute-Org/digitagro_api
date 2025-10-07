import os
import django

# Configurer Django AVANT tout import
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'digitagro_api.settings')
django.setup()

# Maintenant on peut importer
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from apps.notifications.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    )
})