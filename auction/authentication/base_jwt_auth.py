import os

import jwt
from django.core.cache import caches
from rest_framework import exceptions

from auction.authentication.user_proxy import UserProxy


class BaseJWTAuth:
    ACCOUNTS_SERVICE_CACHE = caches["accounts_redis"]

    def __init__(self):
        self.public_key = os.environ.get("RSA_PUBLIC_KEY").replace("\\n", "\n")
        if not self.public_key:
            raise ValueError("RSA_PUBLIC_KEY environment variable is not set")

    def decode_token(self, token):
        options = {
            "verify_exp": True,
        }
        token = jwt.decode(token, self.public_key, algorithms=["RS256"], options=options)
        if token.get("token_type") != "access":
            raise jwt.InvalidTokenError()
        return token

    def check_blacklist(self, token):
        if self.ACCOUNTS_SERVICE_CACHE.get(token):
            raise exceptions.AuthenticationFailed("This token has been blacklisted.")

    def get_user_proxy(self, payload):
        user_id = payload.get("user_id")
        if not user_id:
            raise exceptions.AuthenticationFailed(
                "Token does not contain a valid user_id."
            )

        return UserProxy(payload)
