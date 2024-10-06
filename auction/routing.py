from django.urls import path

from .consumers import AuctionConsumer, BuyerAuctionConsumer

websocket_urlpatterns = [
    path("ws/auctions/seller/dashboard/", AuctionConsumer.as_asgi()),
    path("ws/auctions/buyer/dashboard/", BuyerAuctionConsumer.as_asgi()),
]
