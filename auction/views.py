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
from auction.models.auction import StatusChoices
from auction.permissions import (
    HasCountryInProfile,
    IsBuyer,
    IsNotSellerAndIsOwner,
    IsOwner,
    IsSeller,
)
from auction.serializers import (
    AuctionRetrieveSerializer,
    AuctionSaveSerializer,
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
        status = self.request.query_params.get("status")
        queryset = (
            Auction.objects.all() if status else Auction.objects.filter(status="Live")
        )
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


class BaseAuctionView(CreateAPIView):
    queryset = Auction.objects.all()
    serializer_class = AuctionSaveSerializer
    permission_classes = [IsAuthenticated, IsBuyer, HasCountryInProfile]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user.id, status=self.get_auction_status())
        try:
            self.notify_auction(serializer.data)
        except Exception as e:
            self.warning_message = f"Auction created successfully, but failed to send notifications: {str(e)}"

    def get_auction_status(self):
        raise NotImplementedError("Subclasses must implement get_auction_status()")

    def notify_auction(self, auction_data):
        channel_layer = get_channel_layer()
        notifications = self.get_notifications()

        for group, should_notify in notifications.items():
            if should_notify:
                group_name = self.get_group_name(group)
                async_to_sync(channel_layer.group_send)(
                    group_name,
                    {
                        "type": "new_auction_notification",
                        "data": self.get_notification_data(auction_data, group),
                    },
                )

    def get_group_name(self, group):
        """Get the group name based on the recipient type."""
        if group == "buyer":
            return f"buyer_{self.request.user.id}"
        return "auctions_for_bidders"

    def get_notifications(self):
        """Define which groups should be notified."""
        return {
            "buyer": True,  # Always notify the buyer who created the auction
            "sellers": False,  # By default, don't notify sellers
        }

    def get_notification_data(self, auction_data, group):
        """Customize notification data based on the recipient group."""
        return (
            auction_data if group == "buyer" else {"auction_id": auction_data.get("id")}
        )

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        # If there's a warning message, add it to the response data
        if hasattr(self, "warning_message"):
            if not isinstance(response.data, dict):
                response.data = {"data": response.data}  # pragma: no cover
            response.data["warning"] = self.warning_message
        return response


@extend_schema(
    tags=["Auctions"],
)
class CreateLiveAuctionView(BaseAuctionView):
    def get_auction_status(self):
        return StatusChoices.LIVE

    def get_notifications(self):
        return {
            "buyer": True,  # Notify the buyer who created the auction
            "sellers": True,  # Notify all sellers
        }


@extend_schema(
    tags=["Auctions"],
)
class CreateDraftAuctionView(BaseAuctionView):
    def get_auction_status(self):
        return StatusChoices.DRAFT
