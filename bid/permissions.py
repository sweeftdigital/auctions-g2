from rest_framework.permissions import BasePermission


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
