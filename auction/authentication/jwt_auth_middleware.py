import jwt
from channels.auth import AuthMiddlewareStack
from channels.db import close_old_connections, database_sync_to_async
from django.contrib.auth.models import AnonymousUser

from auction.authentication.base_jwt_auth import BaseJWTAuth
from auction.authentication.user_proxy import UserProxy


class CustomJWTAuthMiddleware(BaseJWTAuth):
    """Middleware to authenticate users in Django Channels using JWT."""

    def __init__(self, app):
        super().__init__()
        self.app = app

    async def __call__(self, scope, receive, send):
        close_old_connections()

        try:
            query_string = scope["query_string"].decode("utf-8")
            params = dict(qc.split("=") for qc in query_string.split("&") if "=" in qc)
            auth_token = params.get("token")

            if auth_token:
                self.check_blacklist(auth_token)
                payload = self.decode_token(auth_token)
                scope["user"] = await self.get_user_proxy(payload)
            else:
                scope["user"] = AnonymousUser()

        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, KeyError, IndexError):
            scope["user"] = AnonymousUser()

        return await self.app(scope, receive, send)

    @database_sync_to_async
    def get_user_proxy(self, payload):
        user_id = payload.get("user_id")
        if not user_id:
            return AnonymousUser()

        return UserProxy(payload)


def JWTAuthMiddlewareStack(app):
    return CustomJWTAuthMiddleware(AuthMiddlewareStack(app))
