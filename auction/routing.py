from django.urls import path

from .consumers import AuctionConsumer

websocket_urlpatterns = [
    path("ws/auctions/create/", AuctionConsumer.as_asgi()),
    path("ws/auctions/<uuid:auction_id>/", AuctionConsumer.as_asgi()),
]
