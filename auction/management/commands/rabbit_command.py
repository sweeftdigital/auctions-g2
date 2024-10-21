import os

from django.core.management.base import BaseCommand

from auctions.rabbitmq.handlers import UserDeletedHandler
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

        event_subscriber.register_handler("buyer_deletion", UserDeletedHandler())
        event_subscriber.subscribe_events("buyer_deletion")

        # Start consuming events
        self.stdout.write(self.style.SUCCESS("Starting RabbitMQ event subscriber..."))
        event_subscriber.start()
