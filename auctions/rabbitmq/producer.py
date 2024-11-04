import json
import os
import time
from typing import Any, Dict

import pika
from pika.exceptions import AMQPConnectionError, ChannelWrongStateError


class EventPublisher:
    def __init__(
        self,
        exchange_name: str,
        host: str,
        port: int,
        username: str,
        password: str,
        exchange_type: str = "direct",
    ):
        """
        Initializes RabbitMQ connection with the given parameters
        and declares the exchange if it doesn't exist.
        """
        self._connection = None
        self._channel = None
        self._exchange_name = exchange_name
        self._exchange_type = exchange_type
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._connect_with_retry()

    def _connect(self):
        """Establishes a connection to RabbitMQ and declares the exchange."""
        self._connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=self._host,
                port=self._port,
                credentials=pika.PlainCredentials(self._username, self._password),
                heartbeat=600,
                blocked_connection_timeout=300,
            )
        )
        self._channel = self._connection.channel()
        self._channel.exchange_declare(
            exchange=self._exchange_name,
            exchange_type=self._exchange_type,
            durable=True,
            auto_delete=False,
        )

    def _connect_with_retry(self, retries: int = 5, delay: int = 5):
        for attempt in range(retries):
            try:
                self._connect()
                print("Connected to RabbitMQ")
                return
            except AMQPConnectionError:
                print(
                    f"Connection attempt {attempt + 1} failed. Retrying in {delay} seconds..."
                )
                time.sleep(delay)

        raise ConnectionError("Failed to connect to RabbitMQ after multiple attempts.")

    def publish_event(self, body: Any, headers: Dict[str, str], routing_key: str):
        """
        Publishes an event to the Event-bus.

        Parameters:
        ----------
        body : Any
            The body of the event to publish.
        headers : Dict[str, str]
            The headers used by consumers for filtering.
        routing_key : str
            The routing key to determine which queue receives the message.
        """
        content = json.dumps(body).encode()
        properties = pika.BasicProperties(headers=headers)

        try:
            self._channel.basic_publish(
                exchange=self._exchange_name,
                routing_key=routing_key,
                body=content,
                properties=properties,
                mandatory=True,  # Ensures the message gets routed correctly
            )
            print(f"Publishing event with body: {body}, and headers: {headers}")
        except (ChannelWrongStateError, AMQPConnectionError) as e:
            print(
                f"Failed to publish message due to {str(e)}. Attempting to reconnect..."
            )
            self._connect_with_retry()
            self.publish_event(body, headers, routing_key)

    def close(self):
        """Closes the channel and connection gracefully."""
        if self._channel and self._channel.is_open:
            self._channel.close()
        if self._connection and self._connection.is_open:
            self._connection.close()
        print("Connection to RabbitMQ closed.")


# Usage example
event_publisher = EventPublisher(
    exchange_name="event_bus",
    host=os.environ["RABBITMQ_HOST"],
    port=int(os.environ["RABBITMQ_PORT"]),
    username=os.environ["RABBITMQ_DEFAULT_USER"],
    password=os.environ["RABBITMQ_DEFAULT_PASS"],
)
