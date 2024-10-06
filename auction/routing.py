from django.urls import path

from .consumers import BuyerAuctionConsumer, SellerAuctionConsumer

websocket_urlpatterns = [
    path("ws/auctions/seller/dashboard/", SellerAuctionConsumer.as_asgi()),
    path("ws/auctions/buyer/dashboard/", BuyerAuctionConsumer.as_asgi()),
]
