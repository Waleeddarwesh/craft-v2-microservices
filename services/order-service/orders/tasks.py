from celery import shared_task
from .services import (
    _process_payments,
    _update_product_stock,
    cancel_pending_credit_card_orders as cancel_pending_orders,
)
from .models import Order
from django.contrib.auth import get_user_model


@shared_task
def create_order_task(user_id, cart_id, address_id, coupon_code, payment_method, is_paid=False):
    """
    Asynchronous task to create an order.
    """
    from .services import create_order_from_cart
    from .models import Cart

    class MockUser:
        def __init__(self, id):
            self.id = id
            self.Balance = 0

    user = MockUser(user_id)
    cart = Cart.objects.get(id=cart_id)

    create_order_from_cart(user, cart, address_id, coupon_code, payment_method, is_paid)

@shared_task
def send_order_notification_task(user_id, message, order_id=None):
    """
    Asynchronous task to send a notification to a user.
    """
    # User = get_user_model()
    try:
        # user = User.objects.get(id=user_id)
        related_object = None
        if order_id:
            related_object = Order.objects.get(id=order_id)
        
        # create_notification_for_user(
        #     user=user,
        #     message=message,
        #     related_object=related_object
        # )
    # except User.DoesNotExist:
    #     print(f"Could not send notification: User with id {user_id} not found.")
    except Order.DoesNotExist:
        print(f"Could not send notification: Order with id {order_id} not found for user {user_id}.")


@shared_task
def process_payments_task(user_id, shipment_id, warehouse_id):
    """
    Asynchronous task to process payments.
    """
    from .services import _process_payments
    from .models import Shipment, Warehouse

    class MockUser:
        def __init__(self, id):
            self.id = id
            self.Balance = 0
        def save(self, *args, **kwargs):
            pass

    user = MockUser(user_id)
    shipment = Shipment.objects.get(id=shipment_id)
    warehouse = Warehouse.objects.get(id=warehouse_id)
    _process_payments(user, shipment, warehouse)


@shared_task
def update_product_stock_task(cart_items):
    """
    Asynchronous task to update product stock.
    """
    from .services import _update_product_stock
    _update_product_stock(cart_items)


@shared_task
def cancel_pending_credit_card_orders_task():
    """
    Periodic task to cancel pending credit card orders.
    """
    cancel_pending_orders()

@shared_task
def batch_pending_shipments_task():
    """
    Periodic task to group READY_TO_SHIP shipments into geographic batches.
    """
    from .models import Shipment, DeliveryBatch
    from django.db.models import Sum
    
    # Get unbatched shipments ready to ship
    unbatched = Shipment.objects.filter(
        status=Shipment.ShipmentStatus.READY_TO_SHIP,
        delivery_batch__isnull=True
    ).exclude(to_state='')

    # Group by state
    states = unbatched.values_list('to_state', flat=True).distinct()
    
    for state in states:
        state_shipments = unbatched.filter(to_state=state)[:5] # Max 5 per batch
        if state_shipments.exists():
            batch = DeliveryBatch.objects.create(
                target_state=state,
                status=DeliveryBatch.BatchStatus.PENDING
            )
            for s in state_shipments:
                s.delivery_batch = batch
                s.save(update_fields=['delivery_batch'])
            
            # Simple static base payout logic for MVP (e.g. 15 fixed + 5 per extra)
            batch.total_base_payout = 15.0 + (5.0 * (state_shipments.count() - 1))
            batch.save(update_fields=['total_base_payout'])