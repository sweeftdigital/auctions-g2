from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from rest_framework import generics, mixins
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from auction.models import Auction
from bid.models import Bid
from bid.serializers import BidSerializer


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
    - 404 (Not Found): Auction not found.

    **Examples:**

    Refer to the OpenAPI documentation for examples of valid and invalid request and response bodies.

    **Notes:**

    - Upon successful creation, a WebSocket notification will be sent to the auction’s channel group
    (`auction_<auction_id>`) to notify users of the new bid.
    - Additional validation is performed in the serializer, including checks for auction status and
    user eligibility to bid.
    """

    serializer_class = BidSerializer
    permission_classes = (IsAuthenticated,)

    def get_auction(self):
        """
        Helper method to fetch the auction based on auction_id from the URL.
        """
        auction_id = self.kwargs.get("auction_id")
        try:
            auction = Auction.objects.get(id=auction_id)
            return auction
        except Auction.DoesNotExist:
            return None

    def perform_create(self, serializer):
        """Fetch the auction based on the auction_id from the URL"""
        auction = self.get_auction()

        if not auction:  # pragma: no cover
            raise ValidationError({"detail": "Auction not found."})

        serializer.save(auction=auction, author=self.request.user.id)

        self.notify_auction_group(auction.id, serializer.instance)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        auction = self.get_auction()
        context.update({"auction": auction})
        return context

    @staticmethod
    def notify_auction_group(auction_id, bid):  # pragma: no cover
        """
        Notify the WebSocket group when a new bid is created.
        Send the full bid data to the WebSocket group.
        """
        channel_layer = get_channel_layer()

        bid_data = BidSerializer(bid).data

        bid_data["id"] = str(bid_data["id"])
        bid_data["auction"] = str(bid_data["auction"])

        print(
            f"Sending WebSocket notification to auction_{str(auction_id)} with data: {bid_data}"
        )

        async_to_sync(channel_layer.group_send)(
            f"auction_{str(auction_id)}",
            {
                "type": "new_bid_notification",
                "message": bid_data,
            },
        )


class UpdateBidView(generics.GenericAPIView, mixins.UpdateModelMixin):
    """
    View for updating a bid in an auction.

    **Permissions:**
    - IsAuthenticated: Requires the user to be authenticated.
    """

    serializer_class = BidSerializer
    permission_classes = [IsAuthenticated]

    def patch(self, request, *args, **kwargs):
        """Allow partial update, specifically for the offer"""
        auction_id = self.kwargs.get("auction_id")
        bid_id = self.kwargs.get("bid_id")

        auction = Auction.objects.filter(id=auction_id).first()
        if auction is None:
            raise ValidationError({"detail": "Auction not found."})

        bid = Bid.objects.filter(
            id=bid_id, auction_id=auction_id, author=self.request.user.id
        ).first()
        if bid is None:
            raise ValidationError({"detail": "Bid not found or you are not the author."})

        serializer = self.get_serializer(
            bid,
            data=request.data,
            context={"auction": auction, "request": request},
            partial=True,
        )
        serializer.is_valid(raise_exception=True)

        self.perform_update(serializer)

        return Response(serializer.data)

    def perform_update(self, serializer):
        """Send WebSocket notification after bid update"""
        bid = serializer.save()
        self.notify_auction_group(bid.auction.id, bid)

    @staticmethod
    def notify_auction_group(auction_id, bid):
        """Notify WebSocket group of updated bid"""
        channel_layer = get_channel_layer()
        bid_data = BidSerializer(bid).data

        bid_data["id"] = str(bid_data["id"])
        bid_data["auction"] = str(bid_data["auction"])

        async_to_sync(channel_layer.group_send)(
            f"auction_{auction_id}",
            {
                "type": "updated_bid_notification",
                "message": bid_data,
            },
        )
