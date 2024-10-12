from django.urls import path

from .views import CreateBidView

urlpatterns = [
    path(
        "auction/<uuid:auction_id>/bid/create/",
        CreateBidView.as_view(),
        name="create-bid",
    ),
]
