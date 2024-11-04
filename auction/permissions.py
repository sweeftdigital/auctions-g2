from rest_framework.permissions import BasePermission


class IsOwner(BasePermission):
    """
    Custom permission to only allow owners of an object to delete it.
    """

    def has_object_permission(self, request, view, obj):
        result = str(obj.author) == str(request.user.id)
        return result


class IsNotSellerAndIsOwner(BasePermission):
    """
    Custom permission to only allow auction owners to delete their auctions,
    but prevent sellers from deleting any auctions.
    """

    def has_object_permission(self, request, view, obj):
        if request.user.is_seller:
            return False

        return str(obj.author) == str(request.user.id)


class IsBuyer(BasePermission):
    """
    Custom permission to only allow buyers to access certain views.
    """

    def has_permission(self, request, view):
        # Check if the user is a Buyer
        return not request.user.is_seller


class IsSeller(BasePermission):
    """
    Custom permission to only allow sellers to access certain views.
    """

    def has_permission(self, request, view):
        # Check if the user is a seller
        return not request.user.is_buyer


class HasCountryInProfile(BasePermission):
    message = "User must set a country in their profile before proceeding."

    def has_permission(self, request, view):
        return bool(request.user.country)


class IsAuctionOwner(BasePermission):
    """
    Custom permission to only allow owners of an auction to declare winners.
    """

    def has_permission(self, request, view):
        return True

    def has_object_permission(self, request, view, obj):
        return str(obj.auction.author) == str(request.user.id)
