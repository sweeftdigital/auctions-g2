from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter

from auction.routing import websocket_urlpatterns as auction_websocket_urlpatterns
from bid.routing import websocket_urlpatterns as bid_websocket_urlpatterns

application = ProtocolTypeRouter(
    {
        "websocket": AuthMiddlewareStack(
            URLRouter(auction_websocket_urlpatterns + bid_websocket_urlpatterns)
        ),
    }
)
