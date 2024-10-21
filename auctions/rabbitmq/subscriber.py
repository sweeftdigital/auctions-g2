import json

import pika

from auctions.rabbitmq.handlers import EventHandler


class EventSubscriber:
    def __init__(
        self, exchange_name: str, host: str, port: int, username: str, password: str
    ):
        self._exchange_name = exchange_name
        self._channel = None
        self._connection = None
        self._event_handlers = {}
        self._connect(host, port, username, password)

    def _connect(self, host, port, username, password):
        connection_params = pika.ConnectionParameters(
            host=host,
            port=port,
            credentials=pika.PlainCredentials(username, password),
            heartbeat=600,
            blocked_connection_timeout=600,
        )
        self._connection = pika.BlockingConnection(connection_params)
        self._channel = self._connection.channel()
        self._channel.exchange_declare(
            exchange=self._exchange_name, exchange_type="direct"
        )

    def register_handler(self, event_type: str, handler: EventHandler):
        self._event_handlers[event_type] = handler

    def subscribe_events(self, queue_name: str):
        self._channel.queue_declare(queue=queue_name, durable=True, auto_delete=False)
        self._channel.queue_bind(exchange=self._exchange_name, queue=queue_name)
        self._channel.basic_consume(
            queue=queue_name, on_message_callback=self._on_message, auto_ack=True
        )

    def _on_message(self, channel, method, properties, body):
        try:
            event_type = properties.headers.get("event_type")
            event_body = json.loads(body)

            if event_type in self._event_handlers:
                self._event_handlers[event_type].handle(event_body)
            else:
                print(f"No handler registered for event type: {event_type}")
        except json.JSONDecodeError:
            print(f"Failed to decode message body: {body}")
        except Exception as e:
            print(f"Error processing message: {e}")

    def start(self):
        try:
            self._channel.start_consuming()
        except KeyboardInterrupt:
            print("Subscriber stopped by user.")
        finally:
            if self._connection and self._connection.is_open:
                self._connection.close()
                print("Connection to RabbitMQ closed.")
