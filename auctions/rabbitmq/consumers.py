import os

import pika


class EventSubscriber:
    _exchange_name = None
    _channel = None

    def __init__(
        self, exchange_name: str, host: str, port: int, username: str, password: str
    ):
        connection_params = pika.ConnectionParameters(
            host=host,
            port=port,
            credentials=pika.PlainCredentials(username, password),
            heartbeat=600,
            blocked_connection_timeout=600,
        )
        connection = pika.BlockingConnection(connection_params)
        self._channel = connection.channel()
        self._exchange_name = exchange_name
        self._channel.exchange_declare(exchange=exchange_name, exchange_type="fanout")

    def start(self):
        self._channel.start_consuming()

    def subscribe_events(self, queue_name: str, callback):
        print(f"Create queue {queue_name}")

        self._channel.queue_declare(queue=queue_name, durable=True, auto_delete=False)
        self._channel.queue_bind(exchange=self._exchange_name, queue=queue_name)
        self._channel.basic_consume(
            queue=queue_name, on_message_callback=callback, auto_ack=True
        )


def create_handler(name):
    """
    Creates event handler function with specific name for debug purposes.
    :param name: The name of the handler.
    :return: The handler function.
    """

    def on_every_event_received(channel, method, properties, body):
        print(
            f"Handler '{name}' has received event with headers '{properties.headers}':",
            body,
        )
        return

    return on_every_event_received


event_subscriber = EventSubscriber(
    exchange_name="event_bus",
    host=os.environ["RABBITMQ_HOST"],
    port=int(os.environ["RABBITMQ_PORT"]),
    username=os.environ["RABBITMQ_DEFAULT_USER"],
    password=os.environ["RABBITMQ_DEFAULT_PASS"],
)

event_subscriber.subscribe_events("user_deletion", create_handler("deletion_callback"))
