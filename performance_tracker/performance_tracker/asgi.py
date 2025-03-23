"""
ASGI config for performance_tracker project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import message.routing  # Import the app-level routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'performance_tracker.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),  # Handle HTTP requests
    "websocket": AuthMiddlewareStack(
        URLRouter(
            message.routing.websocket_urlpatterns  # Connect WebSocket routing
        )
    ),
})

