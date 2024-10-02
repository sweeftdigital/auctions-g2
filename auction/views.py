from rest_framework import generics, status
from rest_framework.generics import CreateAPIView, DestroyAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from auction.filters import AuctionFilterSet
from auction.models import Auction, Bookmark
from auction.permissions import IsOwner
from auction.serializers import (
    AuctionRetrieveSerializer,
    AuctionSerializer,
    BookmarkCreateSerializer,
)


class AuctionListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = Auction.objects.all()
    serializer_class = AuctionSerializer
    filterset_class = AuctionFilterSet


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
