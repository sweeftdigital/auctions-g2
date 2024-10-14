from django.urls import path

from .views import CreateBidView, RejectBidView, RetrieveBidView, UpdateBidView

urlpatterns = [
    path(
        "auction/<uuid:auction_id>/bid/create/",
        CreateBidView.as_view(),
        name="create-bid",
    ),
    path(
        "auction/<uuid:auction_id>/bid/<uuid:bid_id>/update/",
        UpdateBidView.as_view(),
        name="update-bid",
    ),
    path("auction/bid/<uuid:bid_id>/", RetrieveBidView.as_view(), name="retrieve-bid"),
    path("bids/<uuid:bid_id>/reject/", RejectBidView.as_view(), name="reject-bid"),
]
