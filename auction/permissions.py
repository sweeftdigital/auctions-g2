from rest_framework.permissions import BasePermission


class IsOwner(BasePermission):
    """
    Custom permission to only allow owners of an object to delete it.
    """

    def has_object_permission(self, request, view, obj):
        result = str(obj.user_id) == str(request.user.id)
        return result


class IsNotSellerAndIsOwner(BasePermission):
    """
    Custom permission to only allow auction owners to delete their auctions,
    but prevent sellers from deleting any auctions.
    """

    def has_object_permission(self, request, view, obj):
        if request.user.is_seller:
            return False

        return obj.author == request.user


class IsBuyer(BasePermission):
    """
    Custom permission to only allow buyers to access certain views.
    """

    def has_permission(self, request, view):
        # Check if the user is a Buyer
        return not request.user.is_seller
