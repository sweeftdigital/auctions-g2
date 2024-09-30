from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from auction.filters import AuctionFilterSet
from auction.models import Auction
from auction.serializers import AuctionSerializer


class AuctionListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = Auction.objects.all()
    serializer_class = AuctionSerializer
    filterset_class = AuctionFilterSet
