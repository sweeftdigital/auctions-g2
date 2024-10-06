import jwt
from rest_framework import authentication, exceptions

from auction.authentication.base_jwt_auth import BaseJWTAuth


class CustomJWTAuthentication(BaseJWTAuth, authentication.BaseAuthentication):
    """Custom JWT Authentication for DRF views."""

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

        self.check_blacklist(token)

        try:
            payload = self.decode_token(token)
        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed("Token has expired.")
        except jwt.InvalidTokenError:
            raise exceptions.AuthenticationFailed(
                "Invalid token type. Expected access token."
            )

        user = self.get_user_proxy(payload)
        return user, None

    def authenticate_header(self, request):
        return "Bearer"
