import os

import jwt
from django.core.cache import caches
from rest_framework import authentication, exceptions


class CustomJWTAuthentication(authentication.BaseAuthentication):
    ACCOUNTS_SERVICE_CACHE = caches["accounts_redis"]

    def __init__(self):
        self.public_key = os.environ.get("RSA_PUBLIC_KEY")
        if not self.public_key:
            raise ValueError("RSA_PUBLIC_KEY environment variable is not set")

    def authenticate(self, request):
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return None

        try:
            token_type, token = auth_header.split()
            if token_type.lower() != "bearer":
                raise exceptions.AuthenticationFailed(
                    "Authorization type must be Bearer."
                )
        except ValueError:
            raise exceptions.AuthenticationFailed("Invalid authorization header format.")

        if self.ACCOUNTS_SERVICE_CACHE.get(token):
            raise exceptions.AuthenticationFailed("This token has been blacklisted.")

        try:
            payload = self.decode_token(token)
        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed("Token has expired.")
        except jwt.InvalidTokenError:
            raise exceptions.AuthenticationFailed("Invalid token.")

        user = self.get_user_proxy(payload)
        return user, None

    def decode_token(self, token):
        options = {
            "verify_exp": True,
        }
        return jwt.decode(token, self.public_key, algorithms=["RS256"], options=options)

    def get_user_proxy(self, payload):
        user_id = payload.get("user_id")
        if not user_id:
            raise exceptions.AuthenticationFailed(
                "Token does not contain a valid user_id."
            )

        return UserProxy(payload)

    def authenticate_header(self, request):
        return "Bearer"


class UserProxy:
    USER_TYPE_BUYER = "Buyer"
    USER_TYPE_SELLER = "Seller"
    PROFILE_TYPE_INDIVIDUAL = "Individual"
    PROFILE_TYPE_COMPANY = "Company"

    def __init__(self, payload: dict):
        self.payload = payload
        self.id = payload.get("user_id", "")
        self.is_authenticated = True
        self.token_type = payload.get("token_type", "")
        self.exp = payload.get("exp")
        self.iat = payload.get("iat")
        self.jti = payload.get("jti")
        self.is_verified = payload.get("is_verified", False)
        self._user_type = payload.get("user_type", "")
        self._user_profile_type = payload.get("user_profile_type", "")
        self.email = payload.get("email", "")
        self.phone_number = payload.get("phone_number", "")
        self.two_factor_authentication_activated = payload.get(
            "two_factor_authentication_activated", False
        )
        self.is_social_account = payload.get("is_social_account", False)
        self.first_name = payload.get("first_name", "")
        self.last_name = payload.get("last_name", "")
        self.theme = payload.get("theme", "")  # Added theme
        self.language = payload.get("language", "")  # Added language

    @property
    def full_name(self) -> str:
        """Return the full name of the user."""
        return f"{self.first_name} {self.last_name}".strip()

    def is_buyer(self) -> bool:
        """Check if the user is a buyer."""
        return self._user_type == self.USER_TYPE_BUYER

    def is_seller(self) -> bool:
        """Check if the user is a seller."""
        return self._user_type == self.USER_TYPE_SELLER

    def is_individual(self) -> bool:
        """Check if the user has an individual profile."""
        return self._user_profile_type == self.PROFILE_TYPE_INDIVIDUAL

    def is_company(self) -> bool:
        """Check if the user has a company profile."""
        return self._user_profile_type == self.PROFILE_TYPE_COMPANY

    def has_verified_account(self) -> bool:
        """Check if the user account is verified."""
        return self.is_verified

    def requires_two_factor_auth(self) -> bool:
        """Check if the user has two-factor authentication enabled."""
        return self.two_factor_authentication_activated

    def get_contact_info(self) -> dict:
        """Return a dictionary containing the user's contact information."""
        return {"email": self.email, "phone_number": self.phone_number}

    def has_email(self) -> bool:
        """Check if the user has an email address."""
        return bool(self.email)

    def has_phone_number(self) -> bool:
        """Check if the user has a phone number."""
        return bool(self.phone_number)

    def get_settings(self) -> dict:
        """Return a dictionary containing the user's settings."""
        return {"theme": self.theme, "language": self.language}

    def __str__(self) -> str:
        return (
            f"UserProxy (ID: {self.id}, Email: {self.email}, "
            f"Type: {self._user_type}, Profile: {self._user_profile_type}, "
            f"Verified: {self.is_verified})"
        )

    def __repr__(self) -> str:
        return (
            f"<UserProxy id={self.id} email={self.email} type={self._user_type} "
            f"profile={self._user_profile_type} verified={self.is_verified}>"
        )
