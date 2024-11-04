from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import DatabaseError, transaction
from django.db.models import (
    BooleanField,
    Case,
    Count,
    Exists,
    F,
    OuterRef,
    Subquery,
    When,
    Window,
)
from django.db.models.functions import Greatest, RowNumber
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.openapi import OpenApiParameter
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import filters, generics, serializers, status
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.generics import CreateAPIView, DestroyAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from auction.filters import (
    BookmarkFilterSet,
    BuyerAuctionFilterSet,
    SellerAuctionFilterSet,
)
from auction.models import Auction, AuctionStatistics, Bookmark
from auction.models.auction import StatusChoices
from auction.openapi import (
    auction_cancel_openapi_examples,
    auction_create_openapi_examples,
    auction_declare_winner_openapi_examples,
    auction_delete_openapi_examples,
    auction_leave_openapi_examples,
    auction_retrieve_openapi_examples,
    auction_update_patch_openapi_examples,
    auction_update_put_openapi_examples,
    bookmark_create_openapi_examples,
    bookmark_delete_openapi_examples,
    bookmark_list_openapi_examples,
    buyer_dashboard_list_openapi_examples,
    seller_dashboard_list_openapi_examples,
)
from auction.permissions import (
    HasCountryInProfile,
    IsAuctionOwner,
    IsBookmarkOwner,
    IsBuyer,
    IsNotSellerAndIsOwner,
    IsSeller,
)
from auction.serializers import (
    AuctionListSerializer,
    AuctionRetrieveSerializer,
    AuctionSaveSerializer,
    AuctionUpdateSerializer,
    BookmarkCreateSerializer,
    BookmarkListSerializer,
    BulkDeleteAuctionSerializer,
    SellerLiveAuctionListSerializer,
)
from auction.tasks import revoke_auction_bids
from auction.utils import get_currency_symbol
from bid.models import Bid
from bid.models.bid import StatusChoices as BidStatusChoices


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
    responses={
        200: AuctionListSerializer,
        401: AuctionListSerializer,
        403: AuctionListSerializer,
        404: AuctionListSerializer,
    },
    examples=buyer_dashboard_list_openapi_examples.examples(),
)
class BuyerAuctionListView(ListAPIView):
    """
    Retrieves a list of auctions that belong to the user, this includes
    auctions with statuses: `Live`, `Draft`, `Completed`, `Canceled`, `Upcoming`.
    **Auctions with Deleted status will not be included**.

    **Permissions**:

    - IsAuthenticated: Requires the user to be authenticated.
    - IsBuyer: Requires the user to have the 'Buyer' role.

    **Query Parameters**:

    - `search` (optional, str): Search term to filter auctions by auction name, description, or tags.
    - `ordering` (optional, str): Comma-separated list of fields to order the results by.
        Prepend with **“-“** for descending order. Valid fields are: **start_date**, **end_date**,
        **max_price**, **quantity**, **category**, **status**.
    - ` status` (optional, str): The status of the auctions. possible values are: **Live**,
    **Draft**, **Completed**, **Canceled**, **Upcoming**.
    - `page` (optional, int or str): The page number to retrieve (integer). If 'last', retrieves the last page.

    **Returns**:
    - 200 (OK): A paginated list of auctions.
    - 401 (Unauthorized): If the user is not authenticated.
    - 403 (Forbidden): If the user does not have the 'Buyer' role.
    - 404 (Not Found): If invalid value is passed to page query parameter.
    """

    permission_classes = (IsAuthenticated, IsBuyer)
    serializer_class = AuctionListSerializer
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
        queryset = (
            Auction.objects.select_related("statistics", "category").prefetch_related(
                "tags"
            )
        ).filter(author=user)

        # Override ordering if 'category' is in the query params
        ordering = self.request.query_params.get("ordering", None)
        if ordering:
            if "category" in ordering:
                # Map 'category' to 'category__name'
                ordering = ordering.replace("category", "category__name")
            queryset = queryset.order_by(ordering)

        return queryset


@extend_schema(
    tags=["Dashboards"],
    responses={
        200: AuctionListSerializer,
        401: AuctionListSerializer,
        403: AuctionListSerializer,
        404: AuctionListSerializer,
    },
    examples=buyer_dashboard_list_openapi_examples.examples(),
)
class BuyerDashboardListView(ListAPIView):
    """
    Retrieves a list of auctions that belong to the user, this includes
    auctions with status: `Live` only. This view is intended to be
    used for buyer's dashboard.

    **Permissions**:

    - IsAuthenticated: Requires the user to be authenticated.
    - IsBuyer: Requires the user to have the `Buyer` role.

    **Returns**:
    - 200 (OK): A paginated list of auctions.
    - 401 (Unauthorized): If the user is not authenticated.
    - 403 (Forbidden): If the user does not have the 'Buyer' role.
    - 404 (Not Found): If invalid value is passed to page query parameter.
    """

    permission_classes = (IsAuthenticated, IsBuyer)
    serializer_class = AuctionListSerializer

    def get_queryset(self):
        queryset = (
            Auction.objects.select_related("statistics", "category")
            .prefetch_related("tags")
            .filter(
                status="Live", start_date__lte=timezone.now(), author=self.request.user.id
            )
        )
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
    responses={
        200: SellerLiveAuctionListSerializer,
        401: SellerLiveAuctionListSerializer,
        403: SellerLiveAuctionListSerializer,
        404: SellerLiveAuctionListSerializer,
    },
    examples=seller_dashboard_list_openapi_examples.examples(include_description=True),
)
class SellerAuctionListView(ListAPIView):
    """
    Retrieves a list of auctions created by buyers, this auctions will have
    `Live` or `Upcoming` statuses.

    **Permissions**:
    - IsAuthenticated: Requires the user to be authenticated.
    - IsSeller: Requires the user to have the 'Seller' role.

    **Query Parameters**:
    - `search` (optional, str): Search term to filter auctions by auction name, description, or tags.
    - `ordering` (optional, str): Comma-separated list of fields to order the results by. Prepend with **"-"**
        for descending order. Valid fields are: **start_date**, **end_date**, **max_price**, **quantity**,
        **category**, **status**, **tags__name**.
    - `start_date` (optional, str): Filter auctions by start date.
    - `end_date` (optional, str): Filter auctions by end date.
    - `max_price` (optional, float): Filter auctions by maximum price.
    - `min_price` (optional, float): Filter auctions by minimum price.
    - `status` (optional, str): Filter auctions by status. Possible values are: **Live**, **Upcoming**.
    - `category` (optional, str): Filter auctions by category.
    - `page` (optional, int or str): The page number to retrieve (integer). If 'last', retrieves the last page.

    **Returns**:
    - 200 (OK): A paginated list of auctions created by the seller, including their status, category, tags,
    and other details.
    - 401 (Unauthorized): If the user is not authenticated.
    - 403 (Forbidden): If the user does not have the 'Seller' role.
    - 404 (Not Found): If invalid value is passed to page query parameter.
    """

    permission_classes = (IsAuthenticated,)
    serializer_class = SellerLiveAuctionListSerializer
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
        base_queryset = (
            Auction.objects.select_related("statistics", "category")
            .prefetch_related("tags")
            .exclude(status=StatusChoices.DRAFT)
        )

        if status == "Upcoming":
            queryset = base_queryset.filter(start_date__gt=timezone.now())
        else:
            queryset = base_queryset.filter(status="Live")

        ordering = self.request.query_params.get("ordering", None)

        bookmarked_subquery = Bookmark.objects.filter(
            user_id=self.request.user.id, auction_id=OuterRef("pk")
        ).values("pk")

        queryset = queryset.annotate(bookmarked=Exists(bookmarked_subquery))

        if ordering:
            if "category" in ordering:
                ordering = ordering.replace("category", "category__name")
            if "tags" in ordering:
                ordering = ordering.replace("tags", "tags__name")
            queryset = queryset.order_by(ordering)

        return queryset


@extend_schema(
    tags=["Dashboards"],
    responses={
        200: AuctionListSerializer,
        401: AuctionListSerializer,
        403: AuctionListSerializer,
        404: AuctionListSerializer,
    },
    examples=seller_dashboard_list_openapi_examples.examples(),
)
class SellerDashboardListView(ListAPIView):
    """
    Retrieves a list of auctions that user is taking part in(user has
    created bid on that auction), this includes auctions with status:
    `Live` only. This view is intended to be used for seller's dashboard.

    **Permissions**:

    - IsAuthenticated: Requires the user to be authenticated.
    - IsSeller: Requires the user to have the `Seller` role.

    **Returns**:
    - 200 (OK): A paginated list of auctions.
    - 401 (Unauthorized): If the user is not authenticated.
    - 403 (Forbidden): If the user does not have the 'Seller' role.
    - 404 (Not Found): If invalid value is passed to page query parameter.
    """

    permission_classes = (IsAuthenticated, IsSeller)
    serializer_class = AuctionListSerializer

    def get_queryset(self):
        user = self.request.user

        # Get auctions where the user has placed bids
        queryset = (
            Auction.objects.select_related("statistics", "category")
            .prefetch_related("tags")
            .filter(
                bids__author=user.id,
                start_date__lte=timezone.now(),
                status=StatusChoices.LIVE,
            )
            .distinct()
        )

        # Add bookmarked status
        bookmarked_subquery = Bookmark.objects.filter(
            user_id=user.id, auction_id=OuterRef("pk")
        ).values("pk")

        # Annotate auctions with bookmarked status
        queryset = queryset.annotate(bookmarked=Exists(bookmarked_subquery))

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
    responses={
        200: BookmarkListSerializer,
        401: BookmarkListSerializer,
        404: BookmarkListSerializer,
    },
    examples=bookmark_list_openapi_examples.examples(),
)
class BookmarkListView(ListAPIView):
    """
    Retrieves a list of auctions bookmarked by the authenticated user.

    **Permissions**:
    - IsAuthenticated: Requires the user to be authenticated.

    **Query Parameters**:
    - `search` (optional, str): Search term to filter bookmarks by **auction name**,
        **description**, or **tags**.
    - `ordering` (optional, str): Comma-separated list of fields to order the results by. Prepend with
        "-" for descending order. Valid fields are: **start_date**, **end_date**, **max_price**, **quantity**.
    - `status` (optional, str): Filter bookmarks by auction status. Possible values are: **Live**,
        **Draft**, **Completed**, **Canceled**, **Upcoming**.
    - `condition` (optional, str): Filter bookmarks by auction condition. Possible values are:
        **New**, **Used - Like New**, **Used - Very Good**, **Used - Like New**, **Used - Good**,
        **Used - Acceptable**.
    - `accepted_bidders` (optional, str): Filter bookmarks by auction accepted bidders. Possible
        values are: **Both**, **Company**, **Individual**.
    - `accepted_locations` (optional, str): Filter bookmarks by auction accepted locations.
    - `currency` (optional, str): Filter bookmarks by auction currency. Possible values are:
        **USD**, **GEL**, **EUR**.
    - `max_price` (optional, decimal): Filter bookmarks by maximum auction price.
    - `min_price` (optional, decimal): Filter bookmarks by minimum auction price.
    - `start_date` (optional, date-time): Filter bookmarks by auction start date.
    - `end_date` (optional, date-time): Filter bookmarks by auction end date.
    - `category` (optional, str): Filter bookmarks by auction category.

    **Returns**:
    - 200 (OK): A paginated list of bookmarked auctions, including their details.
    - 401 (Unauthorized): If the user is not authenticated.
    - 404 (Not Found): If invalid value is passed to page query parameter.
    """

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
    responses={
        200: AuctionRetrieveSerializer,
        401: AuctionRetrieveSerializer,
        403: AuctionRetrieveSerializer,
        404: AuctionRetrieveSerializer,
    },
    examples=auction_retrieve_openapi_examples.examples(),
)
class RetrieveAuctionView(generics.RetrieveAPIView):
    """
    Retrieve details of a specific auction by its ID.

    This view allows authorized users to retrieve information about an existing auction.
    Permissions are checked to ensure only the following users can access an auction:
    - **Authenticated** user (for published auctions)
    - **Author** of the auction (for draft auctions)

    **Response:**

    - 200 (OK): Successful retrieval of the auction details.
    - 401 (Unauthorized): Authentication credentials are missing or invalid.
    - 403 (Forbidden): User does not have permission to access the auction (draft or seller attempting access).
    - 404 (Not Found): The requested auction does not exist.
    """

    permission_classes = (IsAuthenticated,)
    serializer_class = AuctionRetrieveSerializer
    lookup_field = "id"

    def get_object(self):
        user_id = self.request.user.id
        user_is_seller = self.request.user.is_seller

        try:
            # Base query with all necessary relations and annotations
            base_query = (
                Auction.objects.select_related(
                    "statistics",
                    "category",
                )
                .prefetch_related(
                    "tags",
                )
                .annotate(
                    bookmark_id=Subquery(
                        Bookmark.objects.filter(
                            user_id=user_id, auction_id=OuterRef("pk")
                        ).values("id")[:1]
                    ),
                    bookmarked=Case(
                        When(bookmark_id__isnull=False, then=True),
                        default=False,
                        output_field=BooleanField(),
                    ),
                )
            )

            # bid-related annotations only for sellers
            if user_is_seller:
                base_query = base_query.annotate(
                    has_bid=Exists(
                        Bid.objects.filter(author=user_id, auction_id=OuterRef("pk"))
                    ),
                )

            # Get the auction with a single query
            auction = base_query.get(id=self.kwargs["id"])

            # Increment views count for the auction
            auction.statistics.views_count = F("views_count") + 1
            auction.statistics.save(update_fields=["views_count"])
            auction.statistics.refresh_from_db()

            # Handle draft auction access based on user permissions
            if auction.status == StatusChoices.DRAFT:
                if user_is_seller or str(auction.author) != str(user_id):
                    self.permission_denied(self.request)
            else:
                self.notify_auction_group(auction)

            return auction

        except Auction.DoesNotExist:
            raise NotFound("Not found.")

    def notify_auction_group(self, auction):
        channel_layer = get_channel_layer()

        async_to_sync(channel_layer.group_send)(
            f"auction_{auction.id}",
            {
                "type": "auction_view_count_notification",
                "message": auction.statistics.views_count,
            },
        )


@extend_schema(
    tags=["Auctions"],
    responses={
        204: AuctionRetrieveSerializer,
        401: AuctionRetrieveSerializer,
        403: AuctionRetrieveSerializer,
        404: AuctionRetrieveSerializer,
    },
    examples=auction_delete_openapi_examples.examples(),
)
class DeleteAuctionView(generics.DestroyAPIView):
    """
    Delete a specific auction by its ID.

    This view allows authenticated users to delete an auction they own, with
    permission checks to ensure that only authorized users can perform this action.

    **Deletion Behavior:**
    - If the auction is in "DRAFT" status, it is permanently deleted from the database.
    - For other statuses, the auction is marked as "DELETED" but remains in the database.

    **Permissions:**
    - The user must be authenticated.
    - Only users who are not sellers or who own the auction are permitted to delete it.

    **Response:**
    - 204 (No Content): The auction was successfully deleted or marked as deleted.
    - 401 (Unauthorized): Authentication credentials are missing or invalid.
    - 403 (Forbidden): User does not have permission to delete the auction.
    - 404 (Not Found): The auction does not exist or is inaccessible.
    """

    queryset = Auction.objects.all()
    lookup_field = "id"
    permission_classes = (IsAuthenticated, IsNotSellerAndIsOwner)

    def delete(self, request, *args, **kwargs):
        auction = self.get_object()

        if auction.status == StatusChoices.DRAFT:
            auction.delete()
        else:
            auction.status = StatusChoices.DELETED
            auction.save()

        return Response(
            {"detail": _("Auction deleted successfully.")},
            status=status.HTTP_204_NO_CONTENT,
        )


@extend_schema(
    tags=["Auctions"],
    responses={
        200: AuctionUpdateSerializer,
        400: AuctionUpdateSerializer,
        401: AuctionUpdateSerializer,
        403: AuctionUpdateSerializer,
        404: AuctionUpdateSerializer,
    },
)
@extend_schema(
    examples=auction_update_patch_openapi_examples.examples(), methods=["PATCH"]
)
@extend_schema(examples=auction_update_put_openapi_examples.examples(), methods=["PUT"])
class UpdateAuctionView(generics.UpdateAPIView):
    """
    Update details of a specific auction by its ID.

    This view allows authenticated users to update an auction they own, with
    permission checks to ensure that only authorized users can perform this action.

    **Update Behavior:**
    - Users can update auction fields like `title`, `description`, and `start_date` and etc.
    - If the auction has already started, users won't be able to update the auction.
    - If the auction has already been completed, users won't be able to update the auction.
    - If an update violates validation rules, an appropriate error response is returned.

    **Permissions:**
    - The user must be authenticated.
    - Only users who are not sellers or who own the auction are permitted to update it.

    **Response:**
    - 200 (OK): The auction was successfully updated.
    - 400 (Bad Request): Validation errors or read-only fields attempted to be updated.
    - 401 (Unauthorized): Authentication credentials are missing or invalid.
    - 403 (Forbidden): User does not have permission to update the auction.
    - 404 (Not Found): The auction does not exist or is inaccessible.
    """

    queryset = Auction.objects.all()
    lookup_url_kwarg = "id"
    permission_classes = (IsAuthenticated, IsNotSellerAndIsOwner)
    serializer_class = AuctionUpdateSerializer


@extend_schema(
    tags=["Auctions"],
    responses={
        204: BulkDeleteAuctionSerializer,
        401: BulkDeleteAuctionSerializer,
        403: BulkDeleteAuctionSerializer,
        404: BulkDeleteAuctionSerializer,
    },
    examples=auction_delete_openapi_examples.examples(),
)
class BulkDeleteAuctionView(generics.GenericAPIView):
    """
    Bulk delete multiple auctions by their UUIDs.

    This view allows authenticated users to delete multiple auctions they own.
    Only auctions that the user has permission to delete will be processed.

    **Deletion Behavior:**
    - If an auction is in "DRAFT" status, it is permanently deleted from the database.
    - For other statuses, the auction is marked as "DELETED" but remains in the database.

    **Permissions:**
    - The user must be authenticated.
    - Only users who are not sellers or who own the auction are permitted to delete it.

    **Response:**
    - 204 (No Content): The auctions were successfully deleted or marked as deleted.
    - 401 (Unauthorized): Authentication credentials are missing or invalid.
    - 403 (Forbidden): User does not have permission to delete the auctions.
    - 404 (Not Found): One or more auctions do not exist or are inaccessible.
    """

    serializer_class = BulkDeleteAuctionSerializer
    permission_classes = (IsAuthenticated, IsNotSellerAndIsOwner)

    def post(self, request, *args, **kwargs):
        # Validate request data using the serializer
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        auction_ids = serializer.validated_data["ids"]

        deleted_count = 0
        marked_deleted_count = 0

        for auction_id in auction_ids:
            try:
                auction = Auction.objects.get(id=auction_id)

                if auction.status == StatusChoices.DRAFT:
                    auction.delete()
                    deleted_count += 1
                else:
                    auction.status = StatusChoices.DELETED
                    auction.save()
                    marked_deleted_count += 1

            except Auction.DoesNotExist:
                return Response(
                    {
                        "detail": _("Auction with UUID {id} does not exist.").format(
                            id=auction_id
                        )
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

        response_data = {
            "detail": _(
                "{deleted} auctions deleted and {marked_deleted} auctions marked as deleted."
            ).format(deleted=deleted_count, marked_deleted=marked_deleted_count)
        }
        return Response(response_data, status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    tags=["Bookmarks"],
    responses={
        201: BookmarkCreateSerializer,
        400: BookmarkCreateSerializer,
        401: BookmarkCreateSerializer,
        404: BookmarkCreateSerializer,
    },
    examples=bookmark_create_openapi_examples.examples(),
)
class CreateBookmarkView(CreateAPIView):
    """
    Create a bookmark for an auction.

    This view allows authenticated users to bookmark existing auctions.

    **Permissions:**

    - IsAuthenticated

    **Request Body:**

    - `auction_id` (required): Unique identifier of the auction to bookmark (UUID format).

    **Response:**
    - 201 (Created): Successful creation of the bookmark. Response includes details of the created bookmark.
    - 400 (Bad Request): User has already bookmarked the auction (duplicate entry).
    - 401 (Unauthorized): Authentication credentials are missing or invalid.
    - 404 (Not Found): The requested auction does not exist.

    **Examples:**

    Refer to the `examples` attribute for detailed examples of request and response structures
    for various scenarios.
    """

    serializer_class = BookmarkCreateSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data, context={"user_id": request.user.id}
        )
        serializer.is_valid(raise_exception=True)
        bookmark = serializer.save()

        auction_id = bookmark.auction.id
        current_bookmarks_count = bookmark.auction.statistics.bookmarks_count

        self.notify_auction_group(auction_id, current_bookmarks_count)
        response_data = {
            "bookmark_id": bookmark.id,
            "user_id": bookmark.user_id,
            "auction_id": auction_id,
        }

        return Response(response_data, status=status.HTTP_201_CREATED)

    def notify_auction_group(self, auction_id, bookmarks_count):
        channel_layer = get_channel_layer()

        print(
            f"Sending WebSocket notification to auction_{str(auction_id)} "
            f"with bookmarks count increased, current bookmarks count: "
            f"{bookmarks_count}"
        )

        async_to_sync(channel_layer.group_send)(
            f"auction_{str(auction_id)}",
            {
                "type": "bookmarks_count_notification",
                "message": bookmarks_count,
            },
        )


@extend_schema(
    tags=["Bookmarks"],
    responses={
        204: None,
        401: BookmarkCreateSerializer,
        403: BookmarkCreateSerializer,
        404: BookmarkCreateSerializer,
    },
    examples=bookmark_delete_openapi_examples.examples(),
)
class DeleteBookmarkView(DestroyAPIView):
    """
    Delete an existing bookmark.

    This view allows authorized users to delete their own bookmarks.

    **Permissions:**

    - IsAuthenticated: Requires the user to be authenticated.
    - IsOwner: Requires the user to be the owner of the bookmark.

    **Response:**

    - 204 (No Content): Bookmark deleted successfully.
    - 401 (Unauthorized): Authentication credentials are missing or invalid.
    - 403 (Forbidden): Bookmark does not belong to the user.
    - 404 (Not Found): The requested bookmark does not exist.
    """

    queryset = Bookmark.objects.all()
    permission_classes = (IsAuthenticated, IsBookmarkOwner)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        auction_id = instance.auction.id

        try:
            with transaction.atomic():
                # Decrease bookmarks count statistic field in auction statistics model
                AuctionStatistics.objects.filter(auction_id=auction_id).update(
                    bookmarks_count=Greatest(F("bookmarks_count") - 1, 0)
                )

                # Get the updated count for WebSocket notification
                updated_count = AuctionStatistics.objects.get(
                    auction_id=auction_id
                ).bookmarks_count

                # Delete the bookmark
                instance.delete()
                self.notify_auction_group(auction_id, updated_count)

            return Response(status=status.HTTP_204_NO_CONTENT)
        except DatabaseError as e:
            return Response(
                {"detail": f"Failed to delete bookmark due to database error. {e}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except Exception as e:
            return Response(
                {
                    "detail": f"An unexpected error occurred while deleting the bookmark. {e}"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def notify_auction_group(self, auction_id, bookmarks_count):
        channel_layer = get_channel_layer()

        print(
            f"Sending WebSocket notification to auction_{str(auction_id)} "
            f"with bookmarks count decreased, current bookmarks count: "
            f"{bookmarks_count}"
        )

        async_to_sync(channel_layer.group_send)(
            f"auction_{auction_id}",
            {
                "type": "bookmarks_count_notification",
                "message": bookmarks_count,
            },
        )


@extend_schema(
    tags=["Auctions"],
    responses={
        201: AuctionSaveSerializer,
        400: AuctionSaveSerializer,
        401: AuctionSaveSerializer,
        403: AuctionSaveSerializer,
    },
    examples=auction_create_openapi_examples.examples(),
)
class BaseAuctionView(CreateAPIView):
    """
    Create a new auction.

    This view allows authenticated users with `IsBuyer` and `HasCountryInProfile` permissions to
    create a new auction.

    **Permissions:**

    - IsAuthenticated: Requires the user to be authenticated.
    - IsBuyer: Requires the user to be a buyer.
    - HasCountryInProfile: Requires the user to have a country specified in their profile.

    **Response:**

    - 201 (Created): Auction created successfully. The response body contains the serialized auction
    data (see `AuctionSaveSerializer`).
    - 400 (Bad Request): Invalid request data. The response body contains a list of validation errors.
     (see example in OpenAPI documentation)
    - 401 (Unauthorized): Authentication credentials are missing or invalid.
    - 403 (Forbidden): User does not have permission to create an auction.

    **Examples:**

    Refer to the OpenAPI documentation for examples of valid and invalid request and response bodies.

    **Notes:**

    - Upon successful creation, the auction will be saved with a status of either `LIVE` or `DRAFT`
    depending on if user sent the request to the `create/draft` or `create/auction` endpoints.
    - If an error occurs during notification sending after a successful creation, a warning message will
    be included in the response data.
    """

    queryset = Auction.objects.all()
    serializer_class = AuctionSaveSerializer
    permission_classes = [IsAuthenticated, IsBuyer, HasCountryInProfile]

    def perform_create(self, serializer):

        serializer.save(
            author=self.request.user.id,
            author_avatar=self.request.user.avatar,
            author_nickname=self.request.user.nickname,
            status=self.get_auction_status(),
        )
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


class CreateLiveAuctionView(BaseAuctionView):
    def get_auction_status(self):
        return StatusChoices.LIVE

    def get_notifications(self):
        return {
            "buyer": True,  # Notify the buyer who created the auction
            "sellers": True,  # Notify all sellers
        }


class CreateDraftAuctionView(BaseAuctionView):
    def get_auction_status(self):
        return StatusChoices.DRAFT


@extend_schema(
    tags=["Auctions"],
    responses={
        200: inline_serializer(
            name="DeclareWinnerResponse",
            fields={
                "message": serializers.CharField(),
                "bid_id": serializers.UUIDField(),
                "auction_id": serializers.UUIDField(),
                "winner_offer": serializers.CharField(
                    help_text="Offer amount with currency symbol"
                ),
                "winner_author_id": serializers.UUIDField(),
            },
        ),
        401: inline_serializer(
            name="DeclareWinnerUnauthorized",
            fields={
                "message": serializers.CharField(help_text="Authentication error message")
            },
        ),
        403: inline_serializer(
            name="DeclareWinnerForbidden",
            fields={
                "message": serializers.CharField(help_text="Permission error message")
            },
        ),
    },
    examples=auction_declare_winner_openapi_examples.examples(),
)
class DeclareWinnerView(generics.GenericAPIView):
    """
    Declare the winner of an auction.

    This view allows authenticated users with to declare a winner for
    a specified auction bid, provided that the auction has completed.

    **Permissions:**

    - IsAuthenticated: Requires the user to be authenticated.
    - IsBuyer: Requires the user to be a buyer.
    - IsAuctionOwner: Requires the user to be an owner of the auction.
    - HasCountryInProfile: Requires the user to have a country specified in their profile.

    **Response:**

    - 200 (OK): Winner of the auction has been successfully declared. The response body contains
    the details of the winning bid, including the `bid_id`, `auction_id`, and `winner_offer`.
    - 401 (Unauthorized): Authentication credentials are missing or invalid.
    - 403 (Forbidden): User does not have permission to declare a winner.
    - 500 (Internal Server Error): An unexpected error occurred while processing the request.

    **Notes:**

    - The winner can only be declared after the auction has been completed.
    If the auction is still ongoing or in a draft state, a validation error will be raised.
    - Bids that have been deleted, rejected, or already approved cannot be declared as winners.
    - If a winner is successfully declared, the auction status will be updated to `COMPLETED`
    and the bid status will be set to `APPROVED`.
    """

    permission_classes = [IsAuthenticated, IsBuyer, IsAuctionOwner, HasCountryInProfile]

    def get_bid(self, auction_id, bid_id):
        bid = get_object_or_404(
            Bid.objects.select_related("auction"), id=bid_id, auction_id=auction_id
        )

        self.check_object_permissions(self.request, bid)
        return bid

    def validate_bid_and_auction(self, bid):
        """Validate bid and auction status"""
        if bid.status in [
            BidStatusChoices.REJECTED,
            BidStatusChoices.DELETED,
            BidStatusChoices.APPROVED,
            BidStatusChoices.REVOKED,
        ]:
            raise ValidationError(
                _(
                    "Only the bids with a status of either Pending or Approved can be declared as winner bids."
                )
            )

        auction = bid.auction
        if (
            auction.status
            in [
                StatusChoices.LIVE,
                StatusChoices.DRAFT,
                StatusChoices.CANCELED,
                StatusChoices.DELETED,
            ]
            or auction.end_date > timezone.now()
        ):
            raise ValidationError(
                _("You can only declare a winner after the auction has been completed.")
            )

    def update_auction_winner(self, bid):
        with transaction.atomic():
            statistics, created = AuctionStatistics.objects.get_or_create(
                auction=bid.auction,
                defaults={
                    "winner_bid": bid.offer,
                    "winner_bid_author": bid.author,
                    "winner_bid_object": bid,
                    "top_bid": bid.offer,
                    "top_bid_author": bid.author,
                    "top_bid_object": bid,
                },
            )

            if not created:
                statistics.winner_bid = bid.offer
                statistics.winner_bid_author = bid.author
                statistics.winner_bid_object = bid

                # If this is also the top bid, update top bid information
                if (
                    not statistics.top_bid_object
                    or bid.offer > statistics.top_bid_object.offer
                ):
                    statistics.top_bid = bid.offer
                    statistics.top_bid_author = bid.author
                    statistics.top_bid_object = bid

                statistics.save()

            # Update bid status to approved
            bid.status = BidStatusChoices.APPROVED
            bid.save()

            # Update auction status to indicate winner has been declared
            bid.auction.status = StatusChoices.COMPLETED
            bid.auction.save()

            return {
                "message": _("Winner of this auction has successfully been declared"),
                "bid_id": str(bid.id),
                "auction_id": str(bid.auction.id),
                "winner_offer": f"{get_currency_symbol(bid.auction.currency)}{bid.offer}",
                "winner_author_id": str(bid.author),
            }

    def post(self, request, auction_id, bid_id, *args, **kwargs):
        try:
            bid = self.get_bid(auction_id, bid_id)
            self.validate_bid_and_auction(bid)

            # All state changes happen in this method within a transaction
            result = self.update_auction_winner(bid)

            return Response(result, status=status.HTTP_200_OK)

        except ValidationError as e:
            error_message = (
                str(e.detail[0]) if isinstance(e.detail, list) else str(e.detail)
            )
            return Response(
                {"message": error_message}, status=status.HTTP_400_BAD_REQUEST
            )
        except PermissionDenied as e:
            return Response({"message": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            return Response(
                {"message": f"An error occurred while declaring the winner {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@extend_schema(
    tags=["Auctions"],
    responses={
        200: inline_serializer(
            name="CancelAuction",
            fields={
                "message": serializers.CharField(),
            },
        ),
        401: inline_serializer(
            name="CancelAuctionUnauthorized",
            fields={
                "message": serializers.CharField(help_text="Authentication error message")
            },
        ),
        403: inline_serializer(
            name="CancelAuctionForbidden",
            fields={
                "message": serializers.CharField(help_text="Permission error message")
            },
        ),
        404: inline_serializer(
            name="CancelAuctionNotFound",
            fields={
                "message": serializers.CharField(help_text="Not found error message")
            },
        ),
    },
    examples=auction_cancel_openapi_examples.examples(),
)
class CancelAuctionView(generics.GenericAPIView):
    """
    Cancel an active auction.

    This view allows authenticated users to cancel an active auction, provided they are
    the auction owner and not the seller. The cancellation will invalidate all existing
    bids and set their status to `Revoked`.

    **Permissions:**

    - IsAuthenticated: Requires the user to be authenticated.
    - IsNotSellerAndIsOwner: Requires the user to be the auction owner and not to be a  seller.

    **Response:**

    - 200 (OK): Auction has been successfully canceled. The response contains a success message.
    - 401 (Unauthorized): Authentication credentials are missing or invalid.
    - 403 (Forbidden): User does not have permission to cancel the auction.
    - 404 (Not Found): The specified auction does not exist.

    **Notes:**

    - Only active auctions can be canceled. Auctions in draft, canceled, deleted, or completed
      states cannot be canceled.
    - An auction cannot be canceled after its end date has passed.
    - Upon successful cancellation:
        - The auction status is set to CANCELED
        - All existing bids are revoked(their status gets set to `Revoked`)
    """

    permission_classes = [IsAuthenticated, IsNotSellerAndIsOwner]
    lookup_url_kwarg = "auction_id"
    queryset = Auction.objects.all()

    def validate_auction_status(self, auction):

        auction_status_responses = {
            "Draft": _("You can not cancel draft auctions."),
            "Canceled": _("This auction is already canceled."),
            "Deleted": _("You can not cancel deleted auctions."),
            "Completed": _(
                "You can not cancel auctions that have already been completed."
            ),
        }

        if auction.end_date < timezone.now():
            raise ValidationError(auction_status_responses["Completed"])

        if auction.status in auction_status_responses:
            raise ValidationError(auction_status_responses[auction.status])

        return True

    def post(self, request, auction_id):
        with transaction.atomic():
            auction = self.get_object()
            self.validate_auction_status(auction)
            auction.status = StatusChoices.CANCELED
            auction.save()
            self.notify_auction_group(auction)
            transaction.on_commit(lambda: revoke_auction_bids.delay(auction.id))

        return Response(
            {"message": _("Auction was successfully canceled.")},
            status=status.HTTP_200_OK,
        )

    def notify_auction_group(self, auction):
        channel_layer = get_channel_layer()
        data = {"auction_id": str(auction.id), "auction_status": "Canceled"}

        async_to_sync(channel_layer.group_send)(
            f"auction_{str(auction.id)}",
            {
                "type": "auction_cancelled_notification",
                "message": data,
            },
        )


@extend_schema(
    tags=["Auctions"],
    responses={
        200: inline_serializer(
            name="LeaveAuction",
            fields={
                "message": serializers.CharField(),
                "user_id": serializers.UUIDField(),
                "cancelled_auction_count": serializers.IntegerField(),
            },
        ),
        400: inline_serializer(
            name="LeaveAuctionBadRequest",
            fields={
                "message": serializers.CharField(),
            },
        ),
        401: inline_serializer(
            name="LeaveAuctionBadUnauthorized",
            fields={
                "message": serializers.CharField(help_text="Authentication error message")
            },
        ),
        403: inline_serializer(
            name="LeaveAuctionForbidden",
            fields={
                "message": serializers.CharField(help_text="Permission error message")
            },
        ),
        404: inline_serializer(
            name="LeaveAuctionNotFound",
            fields={
                "message": serializers.CharField(help_text="Not found error message")
            },
        ),
    },
    examples=auction_leave_openapi_examples.examples(),
)
class LeaveAuctionView(generics.GenericAPIView):
    """
    Leave an auction by cancelling all user's bids.

    This view allows authenticated users to leave an auction by cancelling all their active bids.
    Users can leave the auction only if it is in progress and they are not the auction's winner.

    **Permissions:**

    - IsAuthenticated: Requires the user to be authenticated.
    - IsSeller: Requires the user to be a seller to leave the auction.

    **Response:**

    - 200 (OK): Successfully left the auction. The response contains a
    success message and details about the cancelled bids.
    - 401 (Unauthorized): Authentication credentials are missing or invalid.
    - 403 (Forbidden): User does not have permission to make request to this endpoint.
    - 404 (Not Found): The specified auction does not exist or no active bids found for the user.

    **Notes:**

    - Users cannot leave an auction that has already been completed or is in the future.
    - Auctions that have been cancelled, drafted, or have the user as the winner cannot be left.
    - Upon successful execution:
        - All active bids of the user for the auction are cancelled (their status is set to `Cancelled`).
        - If the user's cancelled bid was the top bid, the auction's statistics are updated
        to reflect the next highest bid.
    """

    permission_classes = [IsAuthenticated, IsSeller]
    lookup_url_kwarg = "auction_id"
    queryset = Auction.objects.all()

    def validate_auction_status(self, auction):
        if auction.end_date < timezone.now() or auction.status == StatusChoices.COMPLETED:
            raise ValidationError(
                _("You can not leave an auction that has already been completed."),
            )
        if auction.start_date > timezone.now():
            raise ValidationError(
                _("You can not leave an auction that has not started yet."),
            )
        if auction.status in [StatusChoices.CANCELED, StatusChoices.DRAFT]:
            raise ValidationError(
                _("You can not leave an auction that has been cancelled, drafted."),
            )
        if auction.statistics.winner_bid_object is not None and str(
            auction.statistics.winner_bid_object.author
        ) == str(self.request.user.id):
            raise ValidationError(_("As a winner of an auction, you can not leave it."))

        return True

    def post(self, request, auction_id, *args, **kwargs):
        auction = self.get_object()
        self.validate_auction_status(auction)

        try:
            with transaction.atomic():
                # Get all user's active bids for this auction
                user_bids = Bid.objects.filter(
                    auction=auction,
                    author=request.user.id,
                    status__in=[
                        BidStatusChoices.PENDING,
                        BidStatusChoices.APPROVED,
                        BidStatusChoices.REJECTED,
                    ],
                )
                user_bids_count = user_bids.count()

                if not user_bids.exists():
                    return Response(
                        {"detail": "No active bids found for this auction"},
                        status=status.HTTP_404_NOT_FOUND,
                    )

                # Check if any of user's bids is the top bid
                auction_stats = auction.statistics
                needs_top_bid_update = False

                if str(auction_stats.top_bid_author) == str(request.user.id):
                    needs_top_bid_update = True

                # Cancel all user's bids
                user_bids.update(status=BidStatusChoices.CANCELED)

                # Update top bid if necessary
                if needs_top_bid_update:
                    # Get the next highest bid
                    next_top_bid = (
                        Bid.objects.filter(
                            auction=auction,
                            status__in=[
                                BidStatusChoices.PENDING,
                                BidStatusChoices.APPROVED,
                            ],
                        )
                        .order_by("-offer")
                        .first()
                    )

                    if next_top_bid:
                        # Update auction statistics with new top bid
                        auction_stats.top_bid = next_top_bid.offer
                        auction_stats.top_bid_author = next_top_bid.author
                        auction_stats.top_bid_object = next_top_bid
                        auction_stats.save()
                    else:
                        # No more active bids
                        auction_stats.top_bid = None
                        auction_stats.top_bid_author = None
                        auction_stats.top_bid_object = None
                        auction_stats.save()

                response_data = {
                    "message": "Successfully left the auction",
                    "user_id": str(self.request.user.id),
                    "cancelled_auction_count": user_bids_count,
                }

                return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"detail": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@extend_schema(
    tags=["Statistics"],
)
class BuyerLeaderBoardStatisticsListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsBuyer]

    def get_queryset(self):
        return (
            Auction.objects.filter(
                status=StatusChoices.COMPLETED,
                statistics__winner_bid_object__isnull=False,
            )
            .values(
                "author",
                "author_nickname",
                "author_avatar",
            )
            .annotate(
                completed_auctions_count=Count("id"),
                rank=Window(
                    expression=RowNumber(), order_by=F("completed_auctions_count").desc()
                ),
            )
            .order_by("-completed_auctions_count")
        )

    def format_users(self, users):
        return [
            {
                "rank": user["rank"],
                "author_id": user["author"],
                "author_nickname": user["author_nickname"],
                "author_avatar": user["author_avatar"],
                "completed_auctions_count": user["completed_auctions_count"],
            }
            for user in users
        ]

    def list(self, request, *args, **kwargs):
        requesting_user_id = request.user.id

        # Get the complete ordered queryset and materialize it
        complete_queryset = list(self.get_queryset())

        # Get top 3 users
        top_three = complete_queryset[:3]

        # Get paginated results
        page = self.paginate_queryset(complete_queryset)
        formatted_users = self.format_users(page)

        # Find user's data in the complete queryset
        user_data = None
        for item in complete_queryset:
            if str(item["author"]) == str(
                requesting_user_id
            ):  # Convert both to strings to ensure matching
                user_data = item
                break

        # If user not found in complete_queryset but exists in results, use that data
        if not user_data:
            for item in formatted_users:
                if str(item["author_id"]) == str(requesting_user_id):
                    user_data = {
                        "rank": item["rank"],
                        "author": item["author_id"],
                        "author_nickname": item["author_nickname"],
                        "author_avatar": item["author_avatar"],
                        "completed_auctions_count": item["completed_auctions_count"],
                    }
                    break

        if user_data:
            user_data_response = {
                "rank": user_data["rank"],
                "author_id": user_data["author"],
                "author_nickname": user_data["author_nickname"],
                "author_avatar": user_data["author_avatar"],
                "completed_auctions_count": user_data["completed_auctions_count"],
            }
        else:
            user_data_response = {
                "rank": None,
                "author_id": requesting_user_id,
                "author_nickname": (
                    request.user.nickname if hasattr(request.user, "nickname") else None
                ),
                "author_avatar": (
                    request.user.avatar if hasattr(request.user, "avatar") else None
                ),
                "completed_auctions_count": 0,
            }

        paginated_response = {
            "user_data": user_data_response,
            "top_three_users": self.format_users(top_three),
            "results": formatted_users,
        }

        response = self.get_paginated_response(paginated_response)
        response.data["user_data"] = paginated_response["user_data"]
        response.data["top_three_users"] = paginated_response["top_three_users"]
        response.data["results"] = paginated_response["results"]

        return response
