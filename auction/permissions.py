# permissions.py

from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    """
    Custom permission to only allow owners of a bookmark to delete it.
    """

    def has_object_permission(self, request, view, obj):
        result = str(obj.user_id) == str(request.user.id)
        return result
