from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import DatabaseError, transaction
from django.db.models import BooleanField, Case, Exists, F, OuterRef, Subquery, When
from django.db.models.functions import Greatest
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.openapi import OpenApiParameter
from drf_spectacular.utils import extend_schema
from rest_framework import filters, generics, status
from rest_framework.exceptions import NotFound
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
    auction_create_openapi_examples,
    auction_delete_openapi_examples,
    auction_retrieve_openapi_examples,
    bookmark_create_openapi_examples,
    bookmark_delete_openapi_examples,
    bookmark_list_openapi_examples,
    buyer_dashboard_list_openapi_examples,
    seller_dashboard_list_openapi_examples,
)
from auction.permissions import (
    HasCountryInProfile,
    IsBuyer,
    IsNotSellerAndIsOwner,
    IsOwner,
    IsSeller,
)
from auction.serializers import (
    AuctionListSerializer,
    AuctionRetrieveSerializer,
    AuctionSaveSerializer,
    BookmarkCreateSerializer,
    BookmarkListSerializer,
    BulkDeleteAuctionSerializer,
    SellerLiveAuctionListSerializer,
)
from bid.models import Bid


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
        queryset = Auction.objects.filter(
            status="Live", start_date__lte=timezone.now(), author=self.request.user.id
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
        queryset = (
            Auction.objects.all() if status else Auction.objects.filter(status="Live")
        )

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
        queryset = Auction.objects.filter(
            bids__author=user.id, start_date__lte=timezone.now()
        ).distinct()

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
            # Base query with bookmark annotation
            base_query = Auction.objects.annotate(
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

            # bid-related annotations only for users with user_type of Seller
            if user_is_seller:
                base_query = base_query.annotate(
                    has_bid=Exists(
                        Bid.objects.filter(author=user_id, auction_id=OuterRef("pk"))
                    ),
                )

            # Getting the auction with appropriate/combined annotations
            auction = base_query.get(id=self.kwargs["id"])

            # Increment views count for the auction
            AuctionStatistics.objects.filter(auction=auction.id).update(
                views_count=F("views_count") + 1
            )

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
    permission_classes = (IsAuthenticated, IsOwner)

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
