from django.urls import path

from auction.views import (
    BookmarkListView,
    BulkDeleteAuctionView,
    BuyerAuctionListView,
    BuyerDashboardListView,
    CancelAuctionView,
    CreateBookmarkView,
    CreateDraftAuctionView,
    CreateLiveAuctionView,
    DeclareWinnerView,
    DeleteAuctionView,
    DeleteBookmarkView,
    LeaveAuctionView,
    RetrieveAuctionView,
    SellerAuctionListView,
    SellerDashboardListView,
    UpdateAuctionView,
)

urlpatterns = [
    path(
        "buyer/list/",
        BuyerAuctionListView.as_view(),
        name="auction-list-buyer",
    ),
    path("buyer/dashboard/", BuyerDashboardListView.as_view(), name="buyer-dashboard"),
    path(
        "seller/list/",
        SellerAuctionListView.as_view(),
        name="auction-list-seller",
    ),
    path("seller/dashboard/", SellerDashboardListView.as_view(), name="seller-dashboard"),
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
    path("bulk-delete/", BulkDeleteAuctionView.as_view(), name="bulk-delete-auction"),
    path("update/<uuid:id>/", UpdateAuctionView.as_view(), name="update-auction"),
    path("bookmarks/list/", BookmarkListView.as_view(), name="list-bookmark"),
    path("bookmark/create/", CreateBookmarkView.as_view(), name="create-bookmark"),
    path(
        "bookmark/delete/<uuid:pk>/",
        DeleteBookmarkView.as_view(),
        name="delete-bookmark",
    ),
    path(
        "declare-winner/<uuid:auction_id>/<uuid:bid_id>/",
        DeclareWinnerView.as_view(),
        name="declare-winner",
    ),
    path("cancel/<uuid:auction_id>/", CancelAuctionView.as_view(), name="cancel-auction"),
    path("leave/<uuid:auction_id>/", LeaveAuctionView.as_view(), name="leave-auction"),
]
