from abc import ABC, abstractmethod

from channels.generic.websocket import AsyncJsonWebsocketConsumer


class BaseAuctionConsumer(AsyncJsonWebsocketConsumer, ABC):
    async def connect(self):
        user = self.scope["user"]
        if user.is_anonymous:
            await self.close()
            return

        await self.accept()
        await self.add_to_group()
        await self.on_connect_success()

    @abstractmethod
    async def add_to_group(self):
        pass

    @abstractmethod
    async def on_connect_success(self):
        pass

    async def new_auction_notification(self, event, additional_data=None):
        """
        Handles a new auction notification event.

        Args:
            event (dict): The event data.
            additional_data (dict, optional): Additional data to include in the notification.
        """
        data = event.get("data")
        destination = self.get_destination()
        message = "New auction was successfully created"
        data = {**data}
        if additional_data:
            data.update(additional_data)

        await self.send_json(
            {
                "type": "new_auction_notification",
                "message": message,
                "destination": destination,
                "data": data,
            }
        )

    @abstractmethod
    def get_destination(self):
        """
        Returns the destination for the notification.

        Returns:
            str: The destination.
        """
        pass

    async def disconnect(self, code):
        await self.remove_from_group()
        await self.close()

    @abstractmethod
    async def remove_from_group(self):
        pass


class SellerAuctionConsumer(BaseAuctionConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.new_auction_count = 0

    async def add_to_group(self):
        await self.channel_layer.group_add("auctions_for_bidders", self.channel_name)

    async def on_connect_success(self):
        self.new_auction_count = 0
        await self.send_json(
            {
                "type": "initial_auction_count",
                "new_auction_count": self.new_auction_count,
            }
        )

    def get_destination(self):
        return "Dashboard for Sellers."

    async def new_auction_notification(self, event):
        # Calculate the new auction count
        self.new_auction_count += 1

        # Create additional data
        additional_data = {"new_auction_count": self.new_auction_count}

        # Call the base method with additional data
        await super().new_auction_notification(event, additional_data)

    async def remove_from_group(self):
        await self.channel_layer.group_discard("auctions_for_bidders", self.channel_name)

    async def reset_user_counter(self):
        self.new_auction_count = 0
        data = {"new_auction_count": self.new_auction_count}
        await self.send_json(
            {
                "type": "reset_auction_count",
                "message": "New auction count has been reset.",
                "destination": "Dashboard for Sellers",
                "data": data,
            }
        )

    async def receive_json(self, content, **kwargs):
        message_type = content.get("type")
        user = self.scope["user"]
        if message_type == "load.new.auctions":
            if user.is_buyer:
                await self.send_json({"error": "Buyers cannot load new auctions."})
            else:
                await self.reset_user_counter()


class BuyerAuctionConsumer(BaseAuctionConsumer):
    async def add_to_group(self):
        user = self.scope["user"]
        await self.channel_layer.group_add(f"buyer_{user.id}", self.channel_name)

    def get_destination(self):
        return "Dashboard for Buyer."

    async def on_connect_success(self):
        await self.send_json(
            {
                "type": "connection_success",
                "message": "Connected to Buyer Dashboard.",
            }
        )

    async def remove_from_group(self):
        user = self.scope["user"]
        await self.channel_layer.group_discard(f"buyer_{user.id}", self.channel_name)
