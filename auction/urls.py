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
    path("auctions/", AuctionListView.as_view(), name="auction-list"),
    path("auction/<uuid:id>/", RetrieveAuctionView.as_view(), name="retrieve-auction"),
    path("auction/delete/<uuid:id>/", DeleteAuctionView.as_view(), name="delete-auction"),
    path("bookmarks/", BookmarkListView.as_view(), name="bookmark-list"),
    path("bookmarks/add/", AddBookmarkView.as_view(), name="add-bookmark"),
    path(
        "bookmarks/delete/<uuid:pk>/",
        DeleteBookmarkView.as_view(),
        name="delete-bookmark",
    ),
]
