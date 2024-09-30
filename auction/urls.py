from django.urls import path

from auction.views import AuctionListView

urlpatterns = [
    path("auctions/", AuctionListView.as_view(), name="auction-list"),
]
