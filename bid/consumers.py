from channels.generic.websocket import AsyncJsonWebsocketConsumer


class BidConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        self.auction_id = self.scope["url_route"]["kwargs"]["auction_id"]

        if not user.is_authenticated or not user.is_seller:
            print("*" * 2000)
            await self.close()
            return

        print(self.auction_id, "*" * 200)

        # Add the user to the auction-specific group
        await self.channel_layer.group_add(
            f"auction_{self.auction_id}", self.channel_name
        )

        # Accept the WebSocket connection
        await self.accept()

    async def disconnect(self, code):
        """self.auction_id is available before discarding the group"""
        await self.channel_layer.group_discard(
            f"auction_{self.auction_id}", self.channel_name
        )
        await self.close()

    async def new_bid_notification(self, event):
        """
        Handles real-time notifications of new bids.
        The `event` contains the full bid data.
        """
        await self.send_json(
            {
                "type": "new_bid_notification",
                "bid": event[
                    "message"
                ],  # Send the full bid data in the WebSocket message
            }
        )
