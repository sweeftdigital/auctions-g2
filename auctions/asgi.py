"""
ASGI config for auctions project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""

import os

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

from auction.authentication.jwt_auth_middleware import JWTAuthMiddlewareStack
from auction.routing import websocket_urlpatterns

# from bid.routing import websocket_urlpatterns

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "auctions.settings")

application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        "websocket": JWTAuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
    }
)
