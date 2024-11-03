from django.urls import path

from .views import (
    ApproveBidView,
    BuyerBidListView,
    CreateBidView,
    DeleteBidView,
    RejectBidView,
    RetrieveBidView,
    SellerBidListView,
    UpdateBidView,
)

urlpatterns = [
    path(
        "create/bid/<uuid:auction_id>/",
        CreateBidView.as_view(),
        name="create-bid",
    ),
    path(
        "update/bid/<uuid:bid_id>/",
        UpdateBidView.as_view(),
        name="update-bid",
    ),
    path("retrieve/bid/<uuid:bid_id>/", RetrieveBidView.as_view(), name="retrieve-bid"),
    path("delete/bid/<uuid:bid_id>/", DeleteBidView.as_view(), name="delete-bid"),
    path("reject/bid/<uuid:bid_id>/", RejectBidView.as_view(), name="reject-bid"),
    path("approve/bid/<uuid:bid_id>/", ApproveBidView.as_view(), name="approve-bid"),
    path(
        "bids/list/buyer/",
        BuyerBidListView.as_view(),
        name="list-all-bids-buyer",
    ),
    path(
        "bids/list/seller/",
        SellerBidListView.as_view(),
        name="list-all-bids-seller",
    ),
    path(
        "bids/list/buyer/<uuid:auction_id>/",
        BuyerBidListView.as_view(),
        name="list-bids-by-auction-buyer",
    ),
    path(
        "bids/list/seller/<uuid:auction_id>/",
        SellerBidListView.as_view(),
        name="list-bids-by-auction-seller",
    ),
]
