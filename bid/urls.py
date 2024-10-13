from django.urls import path

from .views import CreateBidView, UpdateBidView

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
]
