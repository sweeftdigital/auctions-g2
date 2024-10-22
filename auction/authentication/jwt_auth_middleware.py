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
            headers = dict(scope["headers"])
            subprotocols = scope.get("subprotocols", None)
            auth_header = headers.get(b"sec-websocket-protocol", None)

            if auth_header:
                auth_token = auth_header.decode("utf-8")

                if auth_token:
                    self.check_blacklist(auth_token)
                    payload = self.decode_token(auth_token)
                    scope["user"] = await self.get_user_proxy(payload)
                else:
                    scope["user"] = AnonymousUser()
            else:
                scope["user"] = AnonymousUser()

            # Custom send function to include subprotocol during WebSocket handshake
            async def new_send(message):
                if message["type"] == "websocket.accept":
                    # Include the subprotocol if provided by the client
                    message["subprotocol"] = subprotocols[0] if subprotocols else None
                await send(message)

            # Proceed with the inner application, passing the new send function
            return await self.app(scope, receive, new_send)

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
