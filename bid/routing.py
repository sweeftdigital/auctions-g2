from django.urls import re_path

from .consumers import BidConsumer

websocket_urlpatterns = [
    re_path(r"ws/auctions/(?P<auction_id>[A-Za-z0-9_-]+)/bids/$", BidConsumer.as_asgi()),
]
