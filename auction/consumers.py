import json
from abc import ABC, abstractmethod

from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.utils.translation import activate
from django.utils.translation import gettext_lazy as _


class CustomAsyncJsonWebsocketConsumer(AsyncJsonWebsocketConsumer):
    async def send_json(self, content, close=False, ensure_ascii=False):
        """
        Encode the given content as JSON and send it to the client,
        with optional ensure_ascii parameter (default is False).
        """
        # Override encode_json to include the ensure_ascii parameter
        await super().send(
            text_data=self.encode_json(content, ensure_ascii=ensure_ascii), close=close
        )

    @classmethod
    def encode_json(cls, content, ensure_ascii=False):
        return json.dumps(content, ensure_ascii=ensure_ascii)


class BaseAuctionConsumer(CustomAsyncJsonWebsocketConsumer, ABC):
    async def connect(self):
        user = self.scope["user"]
        if user.is_anonymous:
            await self.close()
            return

        # Activate language, this is used for translating responses.
        self.language = self.get_language_from_headers()
        activate(self.language)

        await self.accept()
        await self.add_to_group()
        await self.on_connect_success()

    def get_language_from_headers(self):
        """
        Extracts the language from the Accept-Language header.

        Returns:
            str: The language code if found, otherwise None.
        """
        headers = dict(self.scope["headers"])
        accept_language = headers.get(b"accept-language")
        if accept_language:
            # Decode and split languages by quality score, choosing the highest-ranked one
            languages = accept_language.decode().split(",")
            primary_language = languages[0].split(";")[
                0
            ]  # Take the primary language code
            return primary_language
        return None

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
        activate(self.language)
        data = event.get("data")
        destination = self.get_destination()
        message = str(_("New auction was successfully created."))
        data = {**data}
        if additional_data:
            data.update(additional_data)

        await self.send_json(
            {
                "type": "new_auction_notification",
                "message": message,
                "destination": destination,
                "data": data,
            },
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
        activate(self.language)
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
                await self.send_json(
                    {"error": str(_("Buyers cannot load new auctions."))}
                )
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
