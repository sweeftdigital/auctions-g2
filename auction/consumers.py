from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from auction.serializers import AuctionCreateSerializer, AuctionRetrieveSerializer


class AuctionConsumer(AsyncJsonWebsocketConsumer):

    @database_sync_to_async
    def _create_auction(self, data, user_id):
        data["author"] = user_id

        serializer = AuctionCreateSerializer(data=data)
        serializer.is_valid(raise_exception=True)

        return serializer.save()

    @database_sync_to_async
    def _get_auction_data(self, auction):
        return AuctionRetrieveSerializer(auction).data

    async def connect(self):
        user = self.scope["user"]
        if user.is_anonymous:
            await self.close()
        else:
            await self.accept()

    async def create_auction(self, message):
        data = message.get("data")
        user = self.scope["user"]

        if user.is_anonymous:
            await self.send_json({"error": "User not authenticated."})
            return

        auction = await self._create_auction(data, user.id)
        auction_data = await self._get_auction_data(auction)

        await self.send_json(
            {
                "type": "auction.created",
                "data": auction_data,
            }
        )

    async def disconnect(self, code):
        await self.close()

    async def receive_json(self, content, **kwargs):
        message_type = content.get("type")
        if message_type == "create.auction":
            await self.create_auction(content)
