from django.urls import path

from auction.views import (
    BookmarkListView,
    BuyerAuctionListView,
    CreateBookmarkView,
    CreateDraftAuctionView,
    CreateLiveAuctionView,
    DeleteAuctionView,
    DeleteBookmarkView,
    RetrieveAuctionView,
    SellerAuctionListView,
)

urlpatterns = [
    path(
        "buyer/list/",
        BuyerAuctionListView.as_view(),
        name="auction-list-buyer",
    ),
    path(
        "seller/list/",
        SellerAuctionListView.as_view(),
        name="auction-list-seller",
    ),
    path(
        "retrieve/<uuid:id>/",
        RetrieveAuctionView.as_view(),
        name="retrieve-auction",
    ),
    path(
        "create/auction/",
        CreateLiveAuctionView.as_view(),
        name="create-live-auction",
    ),
    path(
        "create/draft/",
        CreateDraftAuctionView.as_view(),
        name="create-draft-auction",
    ),
    path("delete/<uuid:id>/", DeleteAuctionView.as_view(), name="delete-auction"),
    path("bookmarks/list/", BookmarkListView.as_view(), name="list-bookmark"),
    path("bookmark/create/", CreateBookmarkView.as_view(), name="create-bookmark"),
    path(
        "bookmark/delete/<uuid:pk>/",
        DeleteBookmarkView.as_view(),
        name="delete-bookmark",
    ),
]
