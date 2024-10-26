import json

from channels.generic.websocket import AsyncJsonWebsocketConsumer


class BidConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        self.auction_id = self.scope["url_route"]["kwargs"]["auction_id"]

        if not user.is_authenticated:
            await self.close()
            return

        await self.channel_layer.group_add(
            f"auction_{self.auction_id}", self.channel_name
        )

        # Accept the WebSocket connection
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(
            f"auction_{self.auction_id}", self.channel_name
        )
        await self.close()

    async def new_bid_notification(self, event):
        """
        Handles real-time notifications of new bids.
        """
        await self.send_json(
            {
                "type": "new_bid_notification",
                "bid": event["message"],
                "additional_information": event["additional_information"],
            }
        )

    async def updated_bid_notification(self, event):
        """
        Handles real-time notifications of updated bids.
        """
        await self.send_json(
            {
                "type": "updated_bid_notification",
                "bid": event["message"],
            }
        )

    async def updated_bid_status_notification(self, event):
        """
        Handles real-time notifications of updated bid status (e.g., when a bid is rejected).
        """
        data = {
            "type": "updated_bid_status_notification",
            "bid": event["message"],
        }
        if event.get("additional_information"):
            data["additional_information"] = event["additional_information"]

        await self.send(text_data=json.dumps(data, ensure_ascii=False))

    async def auction_view_count_notification(self, event):
        """
        Handles real-time notifications about how many times users have
        viewed specified auction.
        """
        await self.send_json(
            {
                "type": "auction_view_count_notification",
                "auction_view_count": event["message"],
            }
        )
