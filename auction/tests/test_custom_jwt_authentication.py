import os
import uuid
from unittest import mock

import jwt
from django.test import TestCase
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.test import APIRequestFactory

from auction.authentication.custom_jwt_auth import CustomJWTAuthentication
from auction.authentication.jwt_auth_scheme import CustomJWTAuthenticationScheme
from auction.authentication.user_proxy import UserProxy


class CustomJWTAuthenticationTest(TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.patcher = mock.patch.dict(os.environ, {"RSA_PUBLIC_KEY": "test_public_key"})
        self.patcher.start()

        with mock.patch(
            "auction.authentication.custom_jwt_auth.CustomJWTAuthentication.__init__",
            return_value=None,
        ):
            self.auth = CustomJWTAuthentication()
            self.auth.public_key = os.environ["RSA_PUBLIC_KEY"]
            self.auth.ACCOUNTS_SERVICE_CACHE = mock.Mock()

    def tearDown(self):
        self.patcher.stop()

    @mock.patch("jwt.decode")
    def test_successful_authentication(self, mock_decode):
        """Test that a valid JWT token authenticates successfully."""
        mock_payload = {
            "user_id": str(uuid.uuid4()),
            "token_type": "access",
            "exp": 1700000000,
            "user_type": UserProxy.USER_TYPE_BUYER,
            "user_profile_type": UserProxy.PROFILE_TYPE_INDIVIDUAL,
            "first_name": "John",
            "last_name": "Doe",
            "is_verified": True,
            "two_factor_authentication_activated": True,
            "email": "john.doe@example.com",
            "phone_number": "1234567890",
            "theme": "dark",
            "language": "en",
        }
        mock_decode.return_value = mock_payload
        self.auth.ACCOUNTS_SERVICE_CACHE.get.return_value = None

        request = self.factory.get("/")
        request.headers = {"Authorization": "Bearer valid_token"}

        user, _ = self.auth.authenticate(request)

        self.assertIsInstance(user, UserProxy)
        self.assertEqual(user.id, mock_payload["user_id"])
        self.assertTrue(user.is_buyer)
        self.assertTrue(user.is_individual())
        self.assertFalse(user.is_seller)
        self.assertFalse(user.is_company())
        self.assertEqual(user.full_name, "John Doe")
        self.assertTrue(user.has_verified_account())
        self.assertTrue(user.requires_two_factor_auth())
        self.assertTrue(user.has_email())
        self.assertTrue(user.has_phone_number())
        self.assertEqual(
            user.get_contact_info(),
            {"email": "john.doe@example.com", "phone_number": "1234567890"},
        )
        self.assertEqual(user.get_settings(), {"theme": "dark", "language": "en"})
        self.assertEqual(
            str(user),
            f"UserProxy (ID: {user.id},"
            f" Email: john.doe@example.com, Type: Buyer, Profile: Individual, Verified: True)",
        )
        self.assertEqual(
            repr(user),
            f"<UserProxy id={user.id}"
            f" email=john.doe@example.com type=Buyer profile=Individual verified=True>",
        )

    def test_no_authorization_header(self):
        """Test that no authorization header returns None."""
        self.auth.ACCOUNTS_SERVICE_CACHE.get.return_value = None
        request = self.factory.get("/")
        request.headers = {}

        result = self.auth.authenticate(request)
        self.assertIsNone(result)

    def test_invalid_authorization_header_format(self):
        """Test that an invalid authorization header raises AuthenticationFailed."""
        self.auth.ACCOUNTS_SERVICE_CACHE.get.return_value = None
        request = self.factory.get("/")
        request.headers = {"Authorization": "InvalidFormat"}

        with self.assertRaises(AuthenticationFailed) as context:
            self.auth.authenticate(request)
        self.assertEqual(str(context.exception), "Invalid authorization header format.")

    def test_wrong_token_type(self):
        """Test that a non-bearer token raises AuthenticationFailed."""
        self.auth.ACCOUNTS_SERVICE_CACHE.get.return_value = None
        request = self.factory.get("/")
        request.headers = {"Authorization": "Basic token"}

        with self.assertRaises(AuthenticationFailed) as context:
            self.auth.authenticate(request)
        self.assertEqual(str(context.exception), "Authorization type must be Bearer.")

    def test_blacklisted_token(self):
        """Test that a blacklisted token raises AuthenticationFailed."""
        self.auth.ACCOUNTS_SERVICE_CACHE.get.return_value = "blacklisted"
        request = self.factory.get("/")
        request.headers = {"Authorization": "Bearer blacklisted_token"}

        with self.assertRaises(AuthenticationFailed) as context:
            self.auth.authenticate(request)
        self.assertEqual(str(context.exception), "This token has been blacklisted.")

    @mock.patch("jwt.decode")
    def test_expired_token(self, mock_decode):
        """Test that an expired token raises AuthenticationFailed."""
        self.auth.ACCOUNTS_SERVICE_CACHE.get.return_value = None
        mock_decode.side_effect = jwt.ExpiredSignatureError

        request = self.factory.get("/")
        request.headers = {"Authorization": "Bearer expired_token"}

        with self.assertRaises(AuthenticationFailed) as context:
            self.auth.authenticate(request)
        self.assertEqual(str(context.exception), "Token has expired.")

    @mock.patch("jwt.decode")
    def test_invalid_token(self, mock_decode):
        """Test that an invalid token raises AuthenticationFailed."""
        self.auth.ACCOUNTS_SERVICE_CACHE.get.return_value = None
        mock_decode.side_effect = jwt.InvalidTokenError

        request = self.factory.get("/")
        request.headers = {"Authorization": "Bearer invalid_token"}

        with self.assertRaises(AuthenticationFailed) as context:
            self.auth.authenticate(request)
        self.assertEqual(
            str(context.exception), "Invalid token type. Expected access token."
        )

    @mock.patch("jwt.decode")
    def test_missing_user_id_in_token(self, mock_decode):
        """Test that a token without user_id raises AuthenticationFailed."""
        self.auth.ACCOUNTS_SERVICE_CACHE.get.return_value = None
        mock_payload = {"token_type": "access"}
        mock_decode.return_value = mock_payload

        request = self.factory.get("/")
        request.headers = {"Authorization": "Bearer token_without_user_id"}

        with self.assertRaises(AuthenticationFailed) as context:
            self.auth.authenticate(request)
        self.assertEqual(
            str(context.exception), "Token does not contain a valid user_id."
        )

    def test_public_key_not_set(self):
        """Test that not setting the RSA_PUBLIC_KEY raises a ValueError."""
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError) as context:
                CustomJWTAuthentication()
            self.assertEqual(
                str(context.exception), "RSA_PUBLIC_KEY environment variable is not set"
            )

    def test_authenticate_header(self):
        """Test that authenticate_header returns 'Bearer'."""
        request = self.factory.get("/")
        auth_header = self.auth.authenticate_header(request)
        self.assertEqual(auth_header, "Bearer")


class CustomJWTAuthenticationSchemeTest(TestCase):
    def test_get_security_definition(self):
        """Test that get_security_definition returns the correct security definition."""

        auth_scheme = CustomJWTAuthenticationScheme(target="dummy_target")
        security_definition = auth_scheme.get_security_definition(None)

        expected_definition = {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }

        self.assertEqual(security_definition, expected_definition)
