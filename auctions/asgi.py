"""
ASGI config for auctions project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""

import os

import django

django.setup()  # Ensures that Django's app


from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

from auction.authentication.jwt_auth_middleware import JWTAuthMiddlewareStack
from auction.routing import websocket_urlpatterns as auction_websocket_urlpatterns
from bid.routing import websocket_urlpatterns as bid_websocket_urlpatterns

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "auctions.settings")

# Combine the WebSocket routes from both auction and bid apps
combined_websocket_urlpatterns = auction_websocket_urlpatterns + bid_websocket_urlpatterns

application = ProtocolTypeRouter(
    {
        # HTTP handling
        "http": get_asgi_application(),
        # WebSocket handling with JWT authentication
        "websocket": JWTAuthMiddlewareStack(URLRouter(combined_websocket_urlpatterns)),
    }
)
