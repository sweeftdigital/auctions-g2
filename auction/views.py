from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.openapi import OpenApiParameter
from drf_spectacular.utils import extend_schema
from rest_framework import filters
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from auction.filters import AuctionFilterSet
from auction.models import Auction
from auction.serializers import AuctionSerializer


@extend_schema(
    parameters=[
        OpenApiParameter(
            name="search",
            description="Fields that will be searched by are: `auction_name`, `description`, `tags`.",
            required=False,
            type=str,
        ),
        OpenApiParameter(
            name="ordering",
            description=(
                "Comma-separated list of fields to order by. Prepend with '-' to "
                "indicate descending order. Valid fields are: `start_date`, `end_date`, "
                "`max_price`, `quantity`"
            ),
            required=False,
            type=str,
        ),
    ],
)
class AuctionListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = Auction.objects.all()
    serializer_class = AuctionSerializer
    filterset_class = AuctionFilterSet
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ("auction_name", "description", "tags__name")
    ordering_fields = ("start_date", "end_date", "max_price", "quantity")
