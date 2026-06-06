import pika
import logging
from typing import Callable, List
from django.conf import settings

logger = logging.getLogger(__name__)

class EventConsumer:
    """Consumes domain events from RabbitMQ"""

    def __init__(self, queue_name: str, routing_keys: List[str], amqp_url: str = None):
        self.amqp_url = amqp_url or getattr(settings, 'RABBITMQ_URL', 'amqp://guest:guest@localhost:5672/')
        self.queue_name = queue_name
        self.routing_keys = routing_keys
        self.exchange_name = 'craft_events'
        self._connection = None
        self._channel = None

    def connect(self):
        parameters = pika.URLParameters(self.amqp_url)
        self._connection = pika.BlockingConnection(parameters)
        self._channel = self._connection.channel()
        
        # Declare the exchange
        self._channel.exchange_declare(exchange=self.exchange_name, exchange_type='topic', durable=True)
        
        # Declare the queue
        self._channel.queue_declare(queue=self.queue_name, durable=True)
        
        # Bind the queue to the routing keys
        for key in self.routing_keys:
            self._channel.queue_bind(
                exchange=self.exchange_name,
                queue=self.queue_name,
                routing_key=key
            )

    def start_consuming(self, callback: Callable):
        self.connect()
        
        def on_message(ch, method, properties, body):
            try:
                # the callback should be able to process the json body
                callback(method.routing_key, body)
                ch.basic_ack(delivery_tag=method.delivery_tag)
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                # Reject and requeue or send to dead-letter queue
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

        self._channel.basic_qos(prefetch_count=1)
        self._channel.basic_consume(queue=self.queue_name, on_message_callback=on_message)
        
        logger.info(f"Started consuming on {self.queue_name} for keys {self.routing_keys}")
        try:
            self._channel.start_consuming()
        except KeyboardInterrupt:
            self._channel.stop_consuming()
        finally:
            if self._connection and not self._connection.is_closed:
                self._connection.close()
