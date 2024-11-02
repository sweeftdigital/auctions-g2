from django.urls import path

from .views import (
    ApproveBidView,
    BuyerBidListView,
    CreateBidView,
    RejectBidView,
    RetrieveBidView,
    SellerBidListView,
    UpdateBidView,
)

urlpatterns = [
    path(
        "auction/<uuid:auction_id>/bid/create/",
        CreateBidView.as_view(),
        name="create-bid",
    ),
    path(
        "update/<uuid:bid_id>/",
        UpdateBidView.as_view(),
        name="update-bid",
    ),
    path("auction/bid/<uuid:bid_id>/", RetrieveBidView.as_view(), name="retrieve-bid"),
    path("bids/<uuid:bid_id>/reject/", RejectBidView.as_view(), name="reject-bid"),
    path("bids/<uuid:bid_id>/approve/", ApproveBidView.as_view(), name="approve-bid"),
    path(
        "bids/list/buyer/",
        BuyerBidListView.as_view(),
        name="list-all-bids-buyer",
    ),
    path(
        "bids/list/buyer/<uuid:auction_id>/",
        BuyerBidListView.as_view(),
        name="list-bids-by-auction-buyer",
    ),
    path(
        "bids/list/seller/",
        SellerBidListView.as_view(),
        name="list-all-bids-seller",
    ),
    path(
        "bids/list/seller/<uuid:auction_id>/",
        SellerBidListView.as_view(),
        name="list-bids-by-auction-seller",
    ),
]
