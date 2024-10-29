import logging
import os

from django.core.management.base import BaseCommand

from auctions.rabbitmq.handlers import BuyerDeletedHandler, SellerDeletedHandler
from auctions.rabbitmq.subscriber import EventSubscriber

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Command(BaseCommand):
    help = "Starts the RabbitMQ event subscriber to listen for events."

    def __init__(self):
        super().__init__()
        self.event_mappings = {
            "Buyer_deletion": {
                "queue": "auctions.buyer.deletion",
                "handler": BuyerDeletedHandler(),
            },
            "Seller_deletion": {
                "queue": "auctions.seller.deletion",
                "handler": SellerDeletedHandler(),
            },
        }

    def handle(self, *args, **options):
        try:
            logger.info("Initializing RabbitMQ event subscriber")
            event_subscriber = EventSubscriber(
                exchange_name="event_bus",
                host=os.environ.get("RABBITMQ_HOST", "localhost"),
                port=int(os.environ.get("RABBITMQ_PORT", 5672)),
                username=os.environ.get("RABBITMQ_DEFAULT_USER", "guest"),
                password=os.environ.get("RABBITMQ_DEFAULT_PASS", "guest"),
            )

            for event_type, config in self.event_mappings.items():
                logger.info(
                    f"Registering handler for {event_type}. Django rabbit_command"
                )
                event_subscriber.register_handler(event_type, config["handler"])

                logger.info(
                    f"Subscribing to queue '{config['queue']}' with routing key '{event_type}'. Django rabbit_command"
                )
                event_subscriber.subscribe_events(
                    queue_name=config["queue"], routing_key=event_type
                )

            logger.info("Starting RabbitMQ event subscriber...")
            self.stdout.write(self.style.SUCCESS("Starting RabbitMQ event subscriber..."))
            event_subscriber.start()

        except KeyboardInterrupt:
            logger.warning("KeyboardInterrupt: Stopping RabbitMQ event subscriber")
            self.stdout.write(self.style.WARNING("Stopping subscriber..."))
        except Exception as e:
            logger.error(f"Failed to start RabbitMQ event subscriber: {e}", exc_info=True)
            self.stdout.write(
                self.style.ERROR(f"Failed to start RabbitMQ event subscriber: {e}")
            )
            raise
