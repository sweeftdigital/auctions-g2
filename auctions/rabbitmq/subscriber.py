import json
import logging
import time
from typing import Dict, Optional

import pika

from auctions.rabbitmq.handlers import EventHandler

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EventSubscriber:
    def __init__(
        self, exchange_name: str, host: str, port: int, username: str, password: str
    ):
        self._exchange_name = exchange_name
        self._channel: Optional[pika.channel.Channel] = None
        self._connection: Optional[pika.connection.Connection] = None
        self._event_handlers: Dict[str, EventHandler] = {}
        self._should_reconnect = False
        self._reconnect_delay = 5  # Initial delay in seconds
        self._connect(host, port, username, password)

    def _connect(self, host: str, port: int, username: str, password: str) -> None:
        """Establish connection to RabbitMQ with retry mechanism"""
        try:
            connection_params = pika.ConnectionParameters(
                host=host,
                port=port,
                credentials=pika.PlainCredentials(username, password),
                heartbeat=600,
                blocked_connection_timeout=600,
                connection_attempts=5,
                retry_delay=5,
            )

            self._connection = pika.BlockingConnection(connection_params)
            self._channel = self._connection.channel()

            # Declare exchange
            self._channel.exchange_declare(
                exchange=self._exchange_name,
                exchange_type="direct",
                durable=True,
                auto_delete=False,
            )

            logger.info(f"Successfully connected to RabbitMQ at {host}:{port}")
            self._should_reconnect = True  # Enable reconnection for future disconnects
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise

    def register_handler(self, event_type: str, handler: EventHandler) -> None:
        """Register an event handler for a specific event type"""
        self._event_handlers[event_type] = handler
        logger.info(f"Registered handler for event type: {event_type}. EventSubscriber")

    def subscribe_events(self, queue_name: str, routing_key: str) -> None:
        """Subscribe to events with a specific routing key"""
        try:
            # Declare the main queue
            self._channel.queue_declare(
                queue=queue_name,
                durable=True,
                auto_delete=False,
                arguments={
                    "x-message-ttl": 86400000,  # 24 hour TTL
                    "x-dead-letter-exchange": f"{self._exchange_name}-dlx",
                    "x-dead-letter-routing-key": f"{routing_key}-dlq",
                },
            )

            # Declare DLQ exchange and queue
            self._channel.exchange_declare(
                exchange=f"{self._exchange_name}-dlx",
                exchange_type="direct",
                durable=True,
            )

            self._channel.queue_declare(queue=f"{queue_name}-dlq", durable=True)

            self._channel.queue_bind(
                exchange=f"{self._exchange_name}-dlx",
                queue=f"{queue_name}-dlq",
                routing_key=f"{routing_key}-dlq",
            )

            # Bind the main queue
            self._channel.queue_bind(
                exchange=self._exchange_name, queue=queue_name, routing_key=routing_key
            )

            # Set QoS
            self._channel.basic_qos(prefetch_count=1)

            # Start consuming
            self._channel.basic_consume(
                queue=queue_name, on_message_callback=self._on_message, auto_ack=False
            )

            logger.info(
                f"Subscribed to queue: {queue_name} with routing key: {routing_key}. EventSubscriber"
            )
        except Exception as e:
            logger.error(f"Failed to subscribe to events: {e}")
            raise

    def _on_message(self, channel, method, properties, body):
        """Handle incoming messages with proper acknowledgment"""
        try:
            # Try to get event type from different possible locations
            event_type = (
                properties.headers.get("event_type")  # Check headers first
                or method.routing_key  # Fall back to routing key
            )

            event_body = json.loads(body)
            logger.info(f"Received event: {event_type} with body: {event_body}")

            if event_type in self._event_handlers:
                try:
                    # Handle the event
                    self._event_handlers[event_type].handle(event_body)

                    # Acknowledge only after successful handling
                    channel.basic_ack(delivery_tag=method.delivery_tag)
                    logger.info(
                        f"Successfully processed and acknowledged message: {event_type}"
                    )
                except Exception as handle_error:
                    logger.error(f"Error handling event {event_type}: {handle_error}")
                    # Reject and requeue on handler error
                    channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
            else:
                logger.warning(f"No handler registered for event type: {event_type}")
                # Reject without requeue for unknown event types
                channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode message body: {body}, Error: {e}")
            # Reject invalid messages without requeue
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            # Reject and requeue on unexpected errors
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    def start(self) -> None:
        """Start consuming messages with connection recovery"""
        while self._should_reconnect:
            try:
                logger.info("Starting to consume messages...")
                self._channel.start_consuming()
            except pika.exceptions.ConnectionClosedByBroker:
                logger.warning("Connection was closed by broker, retrying...")
                self._handle_disconnect()
            except pika.exceptions.AMQPConnectionError:
                logger.warning("Lost connection to RabbitMQ, retrying...")
                self._handle_disconnect()
            except KeyboardInterrupt:
                self._should_reconnect = False
                logger.info("Subscriber stopped by user")
            except Exception as e:
                logger.error(f"Error during message consumption: {e}")
                self._handle_disconnect()

        self.cleanup()

    def _handle_disconnect(self):
        """Handle disconnection and reconnection logic"""
        if not self._should_reconnect:
            return

        self.cleanup()

        # Wait before attempting to reconnect
        time.sleep(self._reconnect_delay)

        try:
            self._connect(self._host, self._port, self._username, self._password)
        except Exception as e:
            logger.error(f"Failed to reconnect: {e}")
            # Implement exponential backoff if needed
            self._reconnect_delay = min(self._reconnect_delay * 2, 60)

    def cleanup(self) -> None:
        """Clean up connections"""
        try:
            if self._channel and not self._channel.is_closed:
                self._channel.stop_consuming()
            if self._connection and not self._connection.is_closed:
                self._connection.close()
            logger.info("Cleaned up connections")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
