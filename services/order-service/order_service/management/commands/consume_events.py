from django.core.management.base import BaseCommand
from craft_common.events import EventConsumer
from orders.models import Order
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Consume RabbitMQ events for order-service'

    def handle(self, *args, **options):
        consumer = EventConsumer(queue_name='order_service_queue')
        
        # Subscribe to payment events
        consumer.subscribe('payment.succeeded', self.handle_payment_succeeded)
        consumer.subscribe('payment.failed', self.handle_payment_failed)

        self.stdout.write(self.style.SUCCESS('Starting event consumer for order-service...'))
        try:
            consumer.start_consuming()
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('Consumer stopped.'))
            consumer.stop_consuming()

    def handle_payment_succeeded(self, payload):
        order_id = payload.get('order_id')
        if not order_id:
            return
            
        try:
            order = Order.objects.get(id=order_id)
            order.paid = True
            order.status = Order.OrderStatus.READY_TO_SHIP
            order.save(update_fields=['paid', 'status'])
            self.stdout.write(self.style.SUCCESS(f"Order {order_id} marked as PAID and READY_TO_SHIP"))
            
            # Here we would also publish order.paid and create shipments.
        except Order.DoesNotExist:
            logger.error(f"Order {order_id} not found when processing payment.succeeded")

    def handle_payment_failed(self, payload):
        order_id = payload.get('order_id')
        if not order_id:
            return
            
        try:
            order = Order.objects.get(id=order_id)
            order.status = Order.OrderStatus.CANCELLED
            order.save(update_fields=['status'])
            self.stdout.write(self.style.WARNING(f"Order {order_id} cancelled due to payment failure"))
            
            # Here we would also publish order.cancelled to release stock.
        except Order.DoesNotExist:
            logger.error(f"Order {order_id} not found when processing payment.failed")
