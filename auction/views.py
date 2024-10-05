from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.openapi import OpenApiParameter
from drf_spectacular.utils import extend_schema
from rest_framework import filters, generics, status
from rest_framework.generics import CreateAPIView, DestroyAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from auction.filters import (
    BookmarkFilterSet,
    BuyerAuctionFilterSet,
    SellerAuctionFilterSet,
)
from auction.models import Auction, Bookmark
from auction.permissions import IsBuyer, IsNotSellerAndIsOwner, IsOwner, IsSeller
from auction.serializers import (
    AuctionPublishSerializer,
    AuctionRetrieveSerializer,
    BookmarkCreateSerializer,
    BookmarkListSerializer,
    BuyerAuctionListSerializer,
    SellerAuctionListSerializer,
)


@extend_schema(
    tags=["Auctions"],
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
                "`max_price`, `quantity`, `category`, `status`."
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
class BuyerAuctionListView(ListAPIView):
    permission_classes = (IsAuthenticated, IsBuyer)
    serializer_class = BuyerAuctionListSerializer
    filterset_class = BuyerAuctionFilterSet
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ("auction_name", "description", "tags__name")
    ordering_fields = (
        "start_date",
        "end_date",
        "max_price",
        "quantity",
        "category__name",
        "status",
    )

    def get_queryset(self):
        user = self.request.user.id
        queryset = Auction.objects.filter(author=user)

        # Override ordering if 'category' is in the query params
        ordering = self.request.query_params.get("ordering", None)
        if ordering:
            if "category" in ordering:
                # Map 'category' to 'category__name'
                ordering = ordering.replace("category", "category__name")
            queryset = queryset.order_by(ordering)

        return queryset


@extend_schema(
    tags=["Auctions"],
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
                "`max_price`, `quantity`, `category`, `status`, `tags__name`."
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
class SellerAuctionListView(ListAPIView):
    permission_classes = (IsAuthenticated, IsSeller)
    serializer_class = SellerAuctionListSerializer
    filterset_class = SellerAuctionFilterSet
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ("auction_name", "description", "tags__name")
    ordering_fields = (
        "start_date",
        "end_date",
        "max_price",
        "quantity",
        "category__name",
        "status",
        "tags__name",
    )

    def get_queryset(self):
        queryset = Auction.objects.all()

        # Override ordering if 'tags' or 'category' is in the query params
        ordering = self.request.query_params.get("ordering", None)
        if ordering:
            if "category" in ordering:
                ordering = ordering.replace("category", "category__name")
            if "tags" in ordering:
                ordering = ordering.replace("tags", "tags__name")
            queryset = queryset.order_by(ordering)

        return queryset


@extend_schema(
    tags=["Bookmarks"],
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
class BookmarkListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = Bookmark.objects.all()
    serializer_class = BookmarkListSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = BookmarkFilterSet
    search_fields = (
        "auction__auction_name",
        "auction__description",
        "auction__tags__name",
    )
    ordering_fields = (
        "auction__start_date",
        "auction__end_date",
        "auction__max_price",
        "auction__quantity",
    )

    def get_queryset(self):
        return Bookmark.objects.filter(user_id=self.request.user.id)


@extend_schema(
    tags=["Auctions"],
)
class RetrieveAuctionView(generics.RetrieveAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = Auction.objects.all()
    serializer_class = AuctionRetrieveSerializer
    lookup_field = "id"

    def get_object(self):
        auction = super().get_object()

        if auction.status == "Draft":
            # Deny access if the user is a seller or not the author of the draft
            if self.request.user.is_seller or auction.author != self.request.user.id:
                self.permission_denied(self.request)

        return auction


@extend_schema(
    tags=["Auctions"],
)
class DeleteAuctionView(generics.DestroyAPIView):
    queryset = Auction.objects.all()
    lookup_field = "id"
    permission_classes = (IsAuthenticated, IsNotSellerAndIsOwner)


@extend_schema(
    tags=["Bookmarks"],
)
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


@extend_schema(
    tags=["Bookmarks"],
)
class DeleteBookmarkView(DestroyAPIView):
    queryset = Bookmark.objects.all()
    permission_classes = (IsAuthenticated, IsOwner)


@extend_schema(
    tags=["Auctions"],
)
class PublishAuctionView(CreateAPIView):
    queryset = Auction.objects.all()
    serializer_class = AuctionPublishSerializer
    permission_classes = [IsAuthenticated, IsBuyer]

    def perform_create(self, serializer):
        auction = serializer.save(author=self.request.user.id)

        # Notify the WebSocket consumer about the new auction
        self.notify_new_auction(auction.id)

    def notify_new_auction(self, auction_id):
        channel_layer = get_channel_layer()
        # Send a message to the group notifying that a new auction has been created
        async_to_sync(channel_layer.group_send)(
            "auctions_for_bidders",  # This is the group name in your consumer
            {
                "type": "new_auction_notification",  # The type of message to handle
                "new_auction_id": str(auction_id),  # Include the auction ID
            },
        )
