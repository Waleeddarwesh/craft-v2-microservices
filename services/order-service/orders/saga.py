import requests
import uuid
import logging
from django.conf import settings
from orders.models import Order, OrderItem
from django.db import transaction

logger = logging.getLogger(__name__)

class PlaceOrderSaga:
    """
    Saga Coordinator for the Place Order workflow.
    Handles the distributed transaction: Create Order -> Reserve Stock -> Process Payment.
    """
    def __init__(self, user_id, address_id, payment_method, order_items, coupon_code=None):
        self.user_id = user_id
        self.address_id = address_id
        self.payment_method = payment_method
        self.order_items = order_items # list of dicts: [{'product_id': 1, 'quantity': 2, 'price': 100.0, 'product_name': 'A'}]
        self.coupon_code = coupon_code
        self.order = None
        self.reserved_products = []

    def execute(self):
        try:
            # Step 1: Create order
            self._create_order()
            
            # Step 2: Reserve Stock
            self._reserve_stock()
            
            # Step 3: Initiate Payment
            return self._initiate_payment()
            
        except Exception as e:
            logger.error(f"Saga failed: {str(e)}")
            self._compensate()
            raise e

    def _create_order(self):
        total_amount = sum(item['price'] * item['quantity'] for item in self.order_items)
        
        with transaction.atomic():
            self.order = Order.objects.create(
                user_id=self.user_id,
                address_id=self.address_id,
                payment_method=self.payment_method,
                total_amount=total_amount,
                status=Order.OrderStatus.CREATED
            )
            
            for item in self.order_items:
                OrderItem.objects.create(
                    order=self.order,
                    product_id=item['product_id'],
                    product_name=item.get('product_name', ''),
                    quantity=item['quantity'],
                    price=item['price']
                )

    def _reserve_stock(self):
        catalog_url = getattr(settings, 'CATALOG_SERVICE_INTERNAL_URL', 'http://localhost:8002/internal/products')
        
        for item in self.order_items:
            product_id = item['product_id']
            quantity = item['quantity']
            resp = requests.post(f"{catalog_url}/{product_id}/reserve-stock/", json={"quantity": quantity}, timeout=5)
            
            if resp.status_code == 200:
                self.reserved_products.append({'product_id': product_id, 'quantity': quantity})
            else:
                raise Exception(f"Failed to reserve stock for product {product_id}. Status: {resp.status_code}")

    def _initiate_payment(self):
        payment_url = getattr(settings, 'PAYMENT_SERVICE_INTERNAL_URL', 'http://localhost:8004/internal/payments/initiate/')
        
        payload = {
            "order_id": str(self.order.id),
            "user_id": self.user_id,
            "amount": float(self.order.total_amount),
            "payment_method": self.payment_method
        }
        
        resp = requests.post(payment_url, json=payload, timeout=5)
        
        if resp.status_code in [200, 201]:
            return resp.json()
        else:
            raise Exception(f"Failed to initiate payment. Status: {resp.status_code}")

    def _compensate(self):
        logger.info("Executing compensating transactions...")
        
        # 1. Release reserved stock
        catalog_url = getattr(settings, 'CATALOG_SERVICE_INTERNAL_URL', 'http://localhost:8002/internal/products')
        for item in self.reserved_products:
            try:
                requests.post(f"{catalog_url}/{item['product_id']}/release-stock/", json={"quantity": item['quantity']}, timeout=5)
            except Exception as e:
                logger.error(f"Failed to release stock for product {item['product_id']}: {str(e)}")
                
        # 2. Cancel order
        if self.order:
            self.order.status = Order.OrderStatus.CANCELLED
            self.order.save(update_fields=['status'])
            logger.info(f"Order {self.order.id} cancelled.")
