import json
import pika
from typing import Optional
from .schemas import BaseEvent
from django.conf import settings

class EventPublisher:
    """Publishes domain events to RabbitMQ"""
    
    def __init__(self, amqp_url: Optional[str] = None):
        self.amqp_url = amqp_url or getattr(settings, 'RABBITMQ_URL', 'amqp://guest:guest@localhost:5672/')
        self._connection = None
        self._channel = None
        self.exchange_name = 'craft_events'

    def connect(self):
        if not self._connection or self._connection.is_closed:
            parameters = pika.URLParameters(self.amqp_url)
            self._connection = pika.BlockingConnection(parameters)
            self._channel = self._connection.channel()
            self._channel.exchange_declare(exchange=self.exchange_name, exchange_type='topic', durable=True)

    def publish(self, event: BaseEvent):
        self.connect()
        routing_key = event.event_type
        message_body = event.model_dump_json()
        
        self._channel.basic_publish(
            exchange=self.exchange_name,
            routing_key=routing_key,
            body=message_body,
            properties=pika.BasicProperties(
                delivery_mode=2,  # make message persistent
                content_type='application/json'
            )
        )

    def close(self):
        if self._connection and not self._connection.is_closed:
            self._connection.close()

# Singleton instance for simple usage
publisher = EventPublisher()

def publish_event(event: BaseEvent):
    """Helper function to publish an event."""
    publisher.publish(event)
