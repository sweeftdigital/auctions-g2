from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.openapi import OpenApiParameter
from drf_spectacular.utils import extend_schema
from rest_framework import filters, generics, status
from rest_framework.generics import CreateAPIView, DestroyAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from auction.filters import AuctionFilterSet
from auction.models import Auction, Bookmark
from auction.permissions import IsOwner
from auction.serializers import (
    AuctionListSerializer,
    AuctionRetrieveSerializer,
    BookmarkCreateSerializer,
    BookmarkListSerializer,
)


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
        OpenApiParameter(
            name="page",
            description='The page number or "last" for the last page.',
            required=False,
            type={"oneOf": [{"type": "integer"}, {"type": "string"}]},
        ),
    ],
)
class AuctionListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = Auction.objects.all()
    serializer_class = AuctionListSerializer
    filterset_class = AuctionFilterSet
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ("auction_name", "description", "tags__name")
    ordering_fields = ("start_date", "end_date", "max_price", "quantity")


class BookmarkListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = Bookmark.objects.all()
    serializer_class = BookmarkListSerializer


class RetrieveAuctionView(generics.RetrieveAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = Auction.objects.all()
    serializer_class = AuctionRetrieveSerializer
    lookup_field = "id"


class DeleteAuctionView(generics.DestroyAPIView):
    queryset = Auction.objects.all()
    lookup_field = "id"
    permission_classes = [IsAuthenticated]


class AddBookmarkView(CreateAPIView):
    """
    View to handle the creation of bookmarks for auctions.
    """

    serializer_class = BookmarkCreateSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):

        serializer = self.get_serializer(
            data=request.data, context={"user_id": request.user.id}
        )
        serializer.is_valid(raise_exception=True)
        bookmark = serializer.save()

        response_data = {
            "bookmark_id": bookmark.id,
            "user_id": bookmark.user_id,
            "auction_id": bookmark.auction.id,
        }

        return Response(response_data, status=status.HTTP_201_CREATED)


class DeleteBookmarkView(DestroyAPIView):
    queryset = Bookmark.objects.all()
    permission_classes = (IsAuthenticated, IsOwner)
