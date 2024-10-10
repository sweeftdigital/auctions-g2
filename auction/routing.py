from django.urls import path

from .consumers import BuyerAuctionConsumer, SellerAuctionConsumer

websocket_urlpatterns = [
    path("ws/seller/dashboard/", SellerAuctionConsumer.as_asgi()),
    path("ws/buyer/dashboard/", BuyerAuctionConsumer.as_asgi()),
]
