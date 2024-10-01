from rest_framework import status
from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from auction.filters import AuctionFilterSet
from auction.models import Auction
from auction.serializers import AuctionSerializer, BookmarkCreateSerializer


class AuctionListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = Auction.objects.all()
    serializer_class = AuctionSerializer
    filterset_class = AuctionFilterSet


class AddBookmarkView(CreateAPIView):
    """
    View to handle the creation of bookmarks for auctions.
    """

    serializer_class = BookmarkCreateSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):

        data = request.data
        data["user_id"] = request.user.id

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        bookmark = serializer.save()

        response_data = {"user_id": bookmark.user_id, "auction_id": bookmark.auction.id}

        return Response(response_data, status=status.HTTP_201_CREATED)
