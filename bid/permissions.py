from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission

from bid.models import Bid


class IsBidAuthorOrAuctionAuthor(BasePermission):
    """
    Custom permission to check if the user is the author of the bid
    or the author of the auction associated with the bid.
    """

    def has_object_permission(self, request, view, obj):
        is_bid_author = str(obj.author) == str(request.user.id)
        is_auction_author = str(obj.auction.author) == str(request.user.id)
        print(obj.auction.author, request.user.id)
        return is_bid_author or is_auction_author


class IsBidOwner(BasePermission):
    """
    Custom permission to only allow owners of an object to work with them.
    """

    def has_object_permission(self, request, view, obj):
        is_author = str(obj.author) == str(request.user.id)
        return is_author


class OnlyFiveUniqueBidsPerUser(BasePermission):
    """
    Custom permission to only allow users to place five unique bids on an auction.
    """

    def has_permission(self, request, view):
        auction_id = view.kwargs.get("auction_id")

        if auction_id is None:
            return False

        user_bids_count = Bid.objects.filter(
            auction_id=auction_id, author=request.user.id
        ).count()

        if user_bids_count >= 5:
            raise PermissionDenied(
                _(
                    "As a non-premium user you can not place more than five unique bids on this "
                    "auction. But you can change the offer of a bid as many "
                    "times as you want."
                )
            )

        return True
