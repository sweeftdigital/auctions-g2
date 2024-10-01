from django.urls import path

from auction.views import AddBookmarkView, AuctionListView

urlpatterns = [
    path("auctions/", AuctionListView.as_view(), name="auction-list"),
    path("bookmarks/add/", AddBookmarkView.as_view(), name="add-bookmark"),
]
