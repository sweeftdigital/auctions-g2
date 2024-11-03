from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import IntegrityError, transaction
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.generics import DestroyAPIView, ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from auction.models import Auction, AuctionStatistics
from auction.pagination import CustomPageNumberPagination
from auction.permissions import HasCountryInProfile, IsBuyer, IsOwner, IsSeller
from auction.utils import get_currency_symbol
from bid.models import Bid
from bid.models.bid import StatusChoices
from bid.openapi.bid_approve_openapi_examples import approve_bid_examples
from bid.openapi.bid_create_openapi_examples import create_bid_examples
from bid.openapi.bid_delete_openapi_examples import delete_bid_examples
from bid.openapi.bid_list_openapi_examples import list_bid_examples
from bid.openapi.bid_reject_openapi_examples import reject_bid_examples
from bid.openapi.bid_retrive_openapi_examples import retrieve_bid_examples
from bid.openapi.bid_update_openapi_examples import update_bid_examples
from bid.permissions import (
    IsBidAuthorOrAuctionAuthor,
    IsBidOwner,
    OnlyFiveUniqueBidsPerUser,
)
from bid.serializers import (
    BaseBidSerializer,
    BidListSerializer,
    CreateBidSerializer,
    UpdateBidSerializer,
)


@extend_schema(
    tags=["Bids"],
    responses={
        201: CreateBidSerializer,
        400: CreateBidSerializer,
        401: CreateBidSerializer,
        403: CreateBidSerializer,
        404: CreateBidSerializer,
    },
    examples=create_bid_examples(),
)
class CreateBidView(generics.CreateAPIView):
    """
    Create a new bid for an auction.

    This view allows authenticated users to place a bid on an auction, provided the auction is live
    and the user meets the auction's bidder requirements (e.g., individual or company).

    **Permissions:**

    - IsAuthenticated: Requires the user to be authenticated.

    **Response:**

    - 201 (Created): Bid created successfully. The response body contains the serialized bid data.
    - 400 (Bad Request): Invalid request data. The response body contains a list of validation errors.
    - 403 (Forbidden): Non-premium user tries to create more than `five` bids, or tries to upload more
    than `five` images per bid.
    - 404 (Not Found): Auction not found.

    **Examples:**

    Refer to the OpenAPI documentation for examples of valid and invalid request and response bodies.

    **Notes:**

    - Upon successful creation, a WebSocket notification will be sent to the auction’s channel group
    (`auction_<auction_id>`) to notify users of the new bid.
    - Additional validation is performed in the serializer, including checks for auction status and
    user eligibility to bid.
    """

    serializer_class = CreateBidSerializer
    permission_classes = (
        IsAuthenticated,
        IsSeller,
        HasCountryInProfile,
        OnlyFiveUniqueBidsPerUser,
    )

    def get_auction(self):
        """
        Helper method to fetch the auction based on auction_id from the URL.
        """
        auction_id = self.kwargs.get("auction_id")
        try:
            auction = Auction.objects.get(id=auction_id)
            if auction.status == "Draft":
                raise ValidationError(
                    {
                        "message": _(
                            "You can not place bids on auctions with a status of `Draft`."
                        )
                    }
                )
            if auction.end_date < timezone.now():
                raise ValidationError(
                    {
                        "message": _(
                            "Auction has already been completed, you can no longer place bids."
                        )
                    }
                )
            elif auction.start_date > timezone.now():
                raise ValidationError(
                    {"message": _("Auction has not started yet, you can not place bid.")}
                )
            return auction
        except Auction.DoesNotExist:
            return None

    def perform_create(self, serializer):
        """Fetch the auction based on the auction_id from the URL"""
        auction = self.get_auction()

        if not auction:  # pragma: no cover
            raise ValidationError({"detail": "Auction not found."})

        serializer.save(
            auction=auction,
            author=self.request.user.id,
            author_avatar=self.request.user.avatar,
            author_nickname=self.request.user.nickname,
        )
        is_top_bid = serializer.data.get("is_top_bid", False)

        self.notify_auction_group(auction.id, serializer.instance, is_top_bid)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        auction = self.get_auction()
        context.update({"auction": auction})
        return context

    @staticmethod
    def notify_auction_group(auction_id, bid, is_top_bid):  # pragma: no cover
        """
        Notify the WebSocket group when a new bid is created.
        Send the full bid data to the WebSocket group.
        """
        channel_layer = get_channel_layer()
        bid_data = CreateBidSerializer(bid).data

        bid_data["id"] = str(bid_data["id"])
        bid_data["auction"] = str(bid_data["auction"])
        bid_data["is_top_bid"] = is_top_bid
        auction_statistics = AuctionStatistics.objects.filter(auction=auction_id).first()

        additional_information = {}
        if auction_statistics:
            additional_information["total_bids_count"] = (
                auction_statistics.total_bids_count
            )
        else:
            additional_information["total_bids_count"] = 0

        print(
            f"Sending WebSocket notification to auction_{str(auction_id)} "
            f"with data: {bid_data}, additional info: {additional_information}"
        )

        async_to_sync(channel_layer.group_send)(
            f"auction_{str(auction_id)}",
            {
                "type": "new_bid_notification",
                "message": bid_data,
                "additional_information": additional_information,
            },
        )


@extend_schema(
    tags=["Bids"],
    responses={
        200: UpdateBidSerializer,
        400: UpdateBidSerializer,
        401: UpdateBidSerializer,
        403: UpdateBidSerializer,
        404: UpdateBidSerializer,
    },
    examples=update_bid_examples(),
)
class UpdateBidView(generics.UpdateAPIView):
    """
    View for partially updating a bid in an auction.

    **Functionality**:
    - Allows authenticated users to update their own bids in a specific auction.
    - Validates that the bid belongs to the user.
    - Sends a WebSocket notification to inform other users about the updated bid.
    - **Note**: Only the `offer` field can be updated.

    **Permissions**:
    - The user must be authenticated (IsAuthenticated).
    - Only the bid's author is allowed to make updates.

    **Request Parameters**:
    - `bid_id`: UUID of the bid to be updated.

    **Response**:
    - Returns the updated bid data if successful.
    - Raises validation errors if the auction or bid is not found, or if the user is unauthorized.
    """

    serializer_class = UpdateBidSerializer
    permission_classes = [IsAuthenticated, IsBidOwner]
    lookup_url_kwarg = "bid_id"
    http_method_names = ["patch"]

    def get_queryset(self):
        """
        Get base queryset with all necessary related fields.
        """
        return Bid.objects.select_related("auction").prefetch_related("images")

    def perform_update(self, serializer):
        """Send WebSocket notification after bid update"""
        bid = serializer.save()
        is_top_bid = serializer.data.get("is_top_bid", False)
        self.notify_auction_group(bid.auction.id, serializer.data, is_top_bid)

    @staticmethod
    def notify_auction_group(auction_id, bid, is_top_bid):
        """Notify WebSocket group of updated bid with full fields"""
        channel_layer = get_channel_layer()
        bid_data = bid

        bid_data["id"] = str(bid.get("id"))
        bid_data["auction"] = str(auction_id)
        bid_data["is_top_bid"] = is_top_bid

        async_to_sync(channel_layer.group_send)(
            f"auction_{auction_id}",
            {
                "type": "updated_bid_notification",
                "message": bid_data,
            },
        )


@extend_schema(
    tags=["Bids"],
    responses={
        200: BaseBidSerializer,
        401: BaseBidSerializer,
        403: BaseBidSerializer,
        404: BaseBidSerializer,
    },
    examples=retrieve_bid_examples(),
)
class RetrieveBidView(RetrieveAPIView):
    """
    View for retrieving a bid by its ID.

    **Permissions**:
    - IsAuthenticated: Requires the user to be authenticated.

    **Response**:
    - Returns the bid data if found.
    - Raises a validation error if the bid is not found.
    """

    serializer_class = BaseBidSerializer
    permission_classes = (IsAuthenticated, IsBidAuthorOrAuctionAuthor)
    lookup_url_kwarg = "bid_id"
    queryset = Bid.objects.all()


@extend_schema(
    tags=["Bids"],
    responses={
        204: BaseBidSerializer,
        401: BaseBidSerializer,
        403: BaseBidSerializer,
        404: BaseBidSerializer,
    },
    examples=delete_bid_examples(),
)
class DeleteBidView(DestroyAPIView):
    queryset = Bid.objects.all()
    lookup_url_kwarg = "bid_id"
    permission_classes = (IsAuthenticated, IsBidOwner)


@extend_schema(
    tags=["Bids_Status"],
    examples=reject_bid_examples(),
    responses={
        200: "Bid has been successfully rejected.",
        400: "Validation error (bid already rejected)",
        401: "Unauthorized",
        403: "Permission denied (not auction owner)",
        404: "Bid not found",
    },
)
class RejectBidView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsOwner, IsBuyer]

    def post(self, request, *args, **kwargs):
        bid_id = self.kwargs.get("bid_id")

        try:
            bid = Bid.objects.get(id=bid_id)
        except Bid.DoesNotExist:
            raise NotFound("Bid not found.")

        if bid.status == "Rejected":
            raise ValidationError({"detail": "This bid has already been rejected."})

        auction = Auction.objects.get(id=bid.auction_id)

        if str(auction.author) != str(request.user.id):
            raise PermissionDenied("You are not the owner of this auction.")

        bid.status = "Rejected"
        bid.save()

        self.notify_bid_status_change(bid)

        return Response({"detail": "Bid has been rejected.", "bid_id": str(bid.id)})

    @staticmethod
    def notify_bid_status_change(bid):
        """Notify WebSocket group of updated bid status with full bid data"""
        from bid.serializers import BaseBidSerializer

        channel_layer = get_channel_layer()

        bid_data = BaseBidSerializer(bid).data

        bid_data["id"] = str(bid_data["id"])
        bid_data["auction"] = str(bid_data["auction"])
        bid_data["author"] = str(bid_data["author"])

        async_to_sync(channel_layer.group_send)(
            f"auction_{bid.auction.id}",
            {
                "type": "updated_bid_status_notification",
                "message": bid_data,
            },
        )


@extend_schema(
    tags=["Bids_Status"],
    examples=approve_bid_examples(),
    responses={
        200: "Bid has been successfully approved.",
        400: "Validation error (bid already approved or other issues)",
        401: "Unauthorized",
        403: "Permission denied (not auction owner)",
        404: "Bid not found",
    },
)
class ApproveBidView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsOwner, IsBuyer]

    def post(self, request, *args, **kwargs):
        bid_id = self.kwargs.get("bid_id")

        try:
            with transaction.atomic():
                bid = get_object_or_404(Bid, id=bid_id)

                # Check if bid is already approved
                if bid.status == "Approved":
                    raise ValidationError(
                        {"detail": "This bid has already been approved."}
                    )

                # Fetch auction with related statistics
                auction = Auction.objects.select_related("statistics").get(
                    id=bid.auction_id
                )

                # Ensure the user owns the auction
                if str(auction.author) != str(request.user.id):
                    raise PermissionDenied("You are not the owner of this auction.")

                # Approve the bid
                bid.status = "Approved"
                bid.save()

                # Update the top bid in auction statistics if necessary
                new_top_bid = self.update_top_bid(auction, bid.offer)

                # Notify about the bid status change
                self.notify_bid_status_change(bid, new_top_bid)

            return Response({"detail": "Bid has been approved.", "bid_id": str(bid.id)})

        except IntegrityError:
            raise ValidationError("A database error occurred. Please try again.")
        except Http404:
            raise NotFound("Bid not found.")

    def update_top_bid(self, auction, bid_offer):
        statistics = auction.statistics
        top_bid = statistics.top_bid
        new_top_bid = None

        # If there's no top bid or the new offer is lower, update the top bid
        if top_bid is None or bid_offer < top_bid:
            statistics.top_bid = bid_offer
            new_top_bid = statistics.top_bid
            statistics.save()

        return new_top_bid

    @staticmethod
    def notify_bid_status_change(bid, new_top_bid):
        """Notify WebSocket group of updated bid status with full bid data"""

        from bid.serializers import BaseBidSerializer

        channel_layer = get_channel_layer()
        bid_data = BaseBidSerializer(bid).data

        bid_data["id"] = str(bid_data["id"])
        bid_data["auction"] = str(bid_data["auction"])
        bid_data["author"] = str(bid_data["author"])

        # Include top_bid field in response if user approved bid with the
        # cheapest offer among other approved bids.
        top_bid = f"{get_currency_symbol(bid.auction.currency)}{new_top_bid}"
        additional_information = {"top_bid": str(top_bid)} if new_top_bid else None
        print(
            f"Sending WebSocket notification to auction_{str(bid.auction.id)} "
            f"with data: {bid_data}, additional info: {additional_information}"
        )

        async_to_sync(channel_layer.group_send)(
            f"auction_{str(bid.auction.id)}",
            {
                "type": "updated_bid_status_notification",
                "message": bid_data,
                "additional_information": additional_information,
            },
        )


@extend_schema(
    tags=["Bids"],
    examples=list_bid_examples(),
    responses={
        200: BidListSerializer,
        401: BidListSerializer,
        403: BidListSerializer,
        404: BidListSerializer,
    },
)
class BuyerBidListView(ListAPIView):
    serializer_class = BidListSerializer
    permission_classes = [IsAuthenticated, IsBuyer, IsOwner]

    def get_queryset(self):
        auction_id = self.kwargs.get("auction_id")
        user_id = self.request.user.id

        queryset = Bid.objects.exclude(status=StatusChoices.DELETED).prefetch_related(
            "images"
        )

        if auction_id:
            auction = get_object_or_404(Auction, id=auction_id, author=user_id)
            queryset = queryset.filter(auction=auction)

        return queryset


@extend_schema(
    tags=["Bids"],
    examples=list_bid_examples(),
    responses={
        200: BidListSerializer,
        401: BidListSerializer,
        403: BidListSerializer,
        404: BidListSerializer,
    },
)
class SellerBidListView(ListAPIView):
    serializer_class = BidListSerializer
    permission_classes = [IsAuthenticated, IsSeller]
    pagination_class = None  # Disable pagination by default

    def get_top_bids(self, auction_id):
        """
        Get top 3 bids for an auction based on lowest offer and best condition.
        Returns only approved and pending bids.
        """
        return (
            Bid.objects.filter(
                auction_id=auction_id,
                status__in=[StatusChoices.APPROVED, StatusChoices.PENDING],
            )
            .order_by("offer", "-created_at")
            .prefetch_related("images")[:3]
        )

    def get_queryset(self):
        user_id = self.request.user.id
        auction_id = self.kwargs.get("auction_id")

        # Base queryset: filter by user and exclude deleted bids
        queryset = (
            Bid.objects.filter(
                author=user_id,
            )
            .exclude(status=StatusChoices.DELETED)
            .prefetch_related("images")
        )

        # If auction_id is provided, filter by auction
        if auction_id:
            auction = get_object_or_404(Auction, id=auction_id)
            queryset = queryset.filter(auction=auction)

        return queryset

    def list(self, request, *args, **kwargs):
        auction_id = self.kwargs.get("auction_id")
        queryset = self.get_queryset()

        if auction_id:
            # When auction_id is provided, return without pagination
            response_data = {"user_bids": self.serializer_class(queryset, many=True).data}
            top_bids = self.get_top_bids(auction_id)
            response_data["top_bids"] = self.serializer_class(top_bids, many=True).data
            return Response(response_data)
        else:
            # When no auction_id, use pagination
            self.pagination_class = CustomPageNumberPagination
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.serializer_class(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.serializer_class(queryset, many=True)
            return Response(serializer.data)
