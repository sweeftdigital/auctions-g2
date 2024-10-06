from django.urls import path

from auction.views import (
    AddBookmarkView,
    BookmarkListView,
    BuyerAuctionListView,
    CreateDraftAuctionView,
    CreateLiveAuctionView,
    DeleteAuctionView,
    DeleteBookmarkView,
    RetrieveAuctionView,
    SellerAuctionListView,
)

urlpatterns = [
    path(
        "buyer/auctions/list/",
        BuyerAuctionListView.as_view(),
        name="auction-list-buyer",
    ),
    path(
        "seller/auctions/list/",
        SellerAuctionListView.as_view(),
        name="auction-list-seller",
    ),
    path(
        "auction/retrieve/<uuid:id>/",
        RetrieveAuctionView.as_view(),
        name="retrieve-auction",
    ),
    path(
        "auction/create/live/",
        CreateLiveAuctionView.as_view(),
        name="create-live-auction",
    ),
    path(
        "auction/create/draft/",
        CreateDraftAuctionView.as_view(),
        name="create-draft-auction",
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
