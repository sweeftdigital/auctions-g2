from django.urls import path

from auction.views import (
    AddBookmarkView,
    AuctionListView,
    DeleteBookmarkView,
    RetrieveAuctionView,
)

urlpatterns = [
    path("auctions/", AuctionListView.as_view(), name="auction-list"),
    path("auction/<uuid:id>/", RetrieveAuctionView.as_view(), name="retrieve-auction"),
    path("bookmarks/add/", AddBookmarkView.as_view(), name="add-bookmark"),
    path(
        "bookmarks/delete/<uuid:pk>/",
        DeleteBookmarkView.as_view(),
        name="delete-bookmark",
    ),
]
