from django.urls import path

from .consumers import AuctionConsumer

websocket_urlpatterns = [
    path("ws/auctions/dashboard/", AuctionConsumer.as_asgi()),
]
