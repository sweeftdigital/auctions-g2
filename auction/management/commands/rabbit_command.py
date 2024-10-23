import os

from django.core.management.base import BaseCommand

from auctions.rabbitmq.handlers import BuyerDeletedHandler, SellerDeletedHandler
from auctions.rabbitmq.subscriber import EventSubscriber


class Command(BaseCommand):
    help = "Starts the RabbitMQ event subscriber to listen for events."

    def handle(self, *args, **options):
        # Initialize the event subscriber
        event_subscriber = EventSubscriber(
            exchange_name="event_bus",
            host=os.environ.get("RABBITMQ_HOST", "localhost"),
            port=int(os.environ.get("RABBITMQ_PORT", 5672)),
            username=os.environ.get("RABBITMQ_DEFAULT_USER", "guest"),
            password=os.environ.get("RABBITMQ_DEFAULT_PASS", "guest"),
        )

        event_subscriber.register_handler("Buyer_deletion", BuyerDeletedHandler())
        event_subscriber.register_handler("Seller_deletion", SellerDeletedHandler())
        event_subscriber.subscribe_events("Buyer_deletion")
        event_subscriber.subscribe_events("Seller_deletion")

        # Start consuming events
        self.stdout.write(self.style.SUCCESS("Starting RabbitMQ event subscriber..."))
        event_subscriber.start()
