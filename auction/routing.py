from django.urls import path, re_path

from bid.consumers import BidConsumer

from .consumers import BuyerAuctionConsumer, SellerAuctionConsumer

websocket_urlpatterns = [
    path("ws/auctions/seller/dashboard/", SellerAuctionConsumer.as_asgi()),
    path("ws/auctions/buyer/dashboard/", BuyerAuctionConsumer.as_asgi()),
    re_path(r"ws/auctions/(?P<auction_id>[0-9a-f-]+)/bids/$", BidConsumer.as_asgi()),
]
