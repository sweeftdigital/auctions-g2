from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from auction.serializers import AuctionPublishSerializer


class AuctionConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        if user.is_anonymous:
            await self.close()
        else:
            await self.accept()

            # Initialize user-specific auction counter
            self.new_auction_count = 0

            # Add user to a group for broadcasting new auctions
            await self.channel_layer.group_add("auctions_for_bidders", self.channel_name)

            # Send the initial count (which should be 0) to the user
            await self.send_json(
                {
                    "type": "initial_auction_count",
                    "new_auction_count": self.new_auction_count,
                }
            )

    @database_sync_to_async
    def _create_auction(self, data, user_id):
        serializer = AuctionPublishSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        return serializer.save(author=user_id)

    async def create_auction(self, message):
        data = message.get("data")
        user = self.scope["user"]

        if user.is_anonymous:
            await self.send_json({"error": "User not authenticated."})
            return

        auction = await self._create_auction(data, user.id)

        # Broadcast to all connected users that a new auction has been created
        await self.channel_layer.group_send(
            "auctions_for_bidders",
            {
                "type": "new_auction_notification",
                "new_auction_id": str(auction.id),
            },
        )

    async def new_auction_notification(self, event):
        # Increment the new auction count for this user
        self.new_auction_count += 1

        # Send the new auction ID and updated count to all connected users
        await self.send_json(
            {
                "type": "new_auction_notification",
                "new_auction_id": event["new_auction_id"],
                "new_auction_count": self.new_auction_count,
            }
        )

    async def reset_user_counter(self):
        # Reset the user's new auction count to 0
        self.new_auction_count = 0

        # Send a message to the user confirming the reset
        await self.send_json(
            {
                "type": "reset_auction_count",
                "new_auction_count": self.new_auction_count,
            }
        )

    async def disconnect(self, code):
        # Remove user from the group when disconnected
        await self.channel_layer.group_discard("auctions_for_bidders", self.channel_name)

        await self.close()

    async def receive_json(self, content, **kwargs):
        message_type = content.get("type")
        user = self.scope["user"]
        if message_type == "create.auction":
            if not user.is_buyer:
                await self.send_json({"error": "Only buyers can create auctions."})
                return
            elif not user.country:
                await self.send_json(
                    {
                        "error": "User must set a country in their profile before proceeding."
                    }
                )
                return

            # Proceed with auction creation if both checks pass
            await self.create_auction(content)
        elif message_type == "load.new.auctions":
            if user.is_buyer:
                await self.send_json({"error": "Buyers cannot load new auctions."})
            else:
                await self.reset_user_counter()


class BuyerAuctionConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        if user.is_anonymous:
            await self.close(code=1001)
        elif user.is_seller:
            await self.close(code=1003)
            return
        else:
            await self.accept()

            # Add user to a group for broadcasting new auctions
            await self.channel_layer.group_add(f"buyer_{user.id}", self.channel_name)

            # Optionally send an initial message or just skip
            await self.send_json(
                {"type": "connection_success", "message": "Connected to Buyer Dashboard."}
            )

    @database_sync_to_async
    def _create_auction(self, data, user_id):
        serializer = AuctionPublishSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        return serializer.save(author=user_id)

    async def create_auction(self, message):
        data = message.get("data")
        user = self.scope["user"]

        if user.is_anonymous:
            await self.send_json({"error": "User not authenticated."})
            return

        auction = await self._create_auction(data, user.id)

        # Broadcast to the user's specific group that a new auction has been created
        await self.channel_layer.group_send(
            f"buyer_{user.id}",
            {
                "type": "new_auction_notification",
                "new_auction_data": AuctionPublishSerializer(auction).data,
            },
        )

    async def new_auction_notification(self, event):
        # Send the new auction ID to the user
        await self.send_json(
            {
                "type": "new_auction_notification",
                "new_auction_data": event["new_auction_data"],
            }
        )

    async def disconnect(self, code):
        user = self.scope["user"]
        await self.channel_layer.group_discard(f"buyer_{user.id}", self.channel_name)
        await self.close(code=1000)

    async def receive_json(self, content, **kwargs):
        message_type = content.get("type")

        if message_type == "create.auction":
            await self.create_auction(content)
