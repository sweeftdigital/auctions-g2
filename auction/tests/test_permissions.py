import uuid
from unittest import mock

from django.test import TestCase
from rest_framework.test import APIRequestFactory

from auction.permissions import IsOwner


class IsOwnerPermissionTest(TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.permission = IsOwner()

        self.user_1_id = uuid.uuid4()
        self.user_2_id = uuid.uuid4()

    def test_owner_has_permission(self):
        """Test that the owner of the object has permission."""
        request = self.factory.get("/")
        request.user = mock.Mock()
        request.user.id = self.user_1_id

        obj = mock.Mock()
        obj.user_id = self.user_1_id
        self.assertTrue(self.permission.has_object_permission(request, None, obj))

    def test_non_owner_denied_permission(self):
        """Test that a user who is not the owner is denied permission."""
        request = self.factory.get("/")
        request.user = mock.Mock()
        request.user.id = self.user_2_id

        obj = mock.Mock()
        obj.user_id = self.user_1_id

        self.assertFalse(self.permission.has_object_permission(request, None, obj))

    def test_anonymous_user_denied_permission(self):
        """Test that an anonymous user is denied permission."""
        request = self.factory.get("/")
        request.user = mock.Mock()
        request.user.id = None

        obj = mock.Mock()
        obj.user_id = self.user_1_id

        self.assertFalse(self.permission.has_object_permission(request, None, obj))
