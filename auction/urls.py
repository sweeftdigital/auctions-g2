from django.urls import path

from auction.views import (
    AddBookmarkView,
    AuctionListView,
    BookmarkListView,
    DeleteAuctionView,
    DeleteBookmarkView,
    RetrieveAuctionView,
)

urlpatterns = [
    path("auctions/list/", AuctionListView.as_view(), name="auction-list"),
    path(
        "auction/retrieve/<uuid:id>/",
        RetrieveAuctionView.as_view(),
        name="retrieve-auction",
    ),
    path("auction/delete/<uuid:id>/", DeleteAuctionView.as_view(), name="delete-auction"),
    path("bookmarks/list/", BookmarkListView.as_view(), name="bookmark-list"),
    path("bookmarks/create/", AddBookmarkView.as_view(), name="add-bookmark"),
    path(
        "bookmarks/delete/<uuid:pk>/",
        DeleteBookmarkView.as_view(),
        name="delete-bookmark",
    ),
]
