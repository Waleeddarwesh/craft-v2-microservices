from django.utils.translation import gettext_lazy as _
from django.db import models
import uuid
from django.db.models import Q, CheckConstraint
import random
import string
from django.core.validators import MinValueValidator
from django.db.models.signals import pre_save
from django.dispatch import receiver
from returnrequest.models import ReturnRequest

class OrderManager(models.Manager):
    pass # Needs refactoring since we don't have direct access to user.delivery anymore

class Wishlist(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    user_id = models.BigIntegerField(unique=True)
    Created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Wishlist for User: {self.user_id}"

class WishlistItem(models.Model):
    wishlist = models.ForeignKey(Wishlist, on_delete=models.CASCADE, related_name="items")
    product_id = models.BigIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['wishlist', 'product_id'], name='unique_wishlist_item')
        ]

    def __str__(self):
        return f"Wishlist Item: Product {self.product_id}"

class Cart(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    user_id = models.BigIntegerField(unique=True)
    Created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)

    def __str__(self):
        return f"Cart ID:{self.id} for User {self.user_id}"

class CartItems(models.Model):
    CartID = models.ForeignKey(Cart, on_delete=models.CASCADE,related_name="items", null=True, blank=True)
    product_id = models.BigIntegerField(null=True, blank=True)
    Quantity = models.PositiveIntegerField()
    Color = models.CharField(max_length=20,blank=True, null=True)
    Size = models.CharField(max_length=20,blank=True, null=True)

    def __str__(self):
        return f"Cart ID {self.CartID} Cart Item: Product {self.product_id}"

class Order(models.Model):
    class OrderStatus(models.TextChoices):
        CREATED = 'created'
        READY_TO_SHIP ='ready_to_ship'
        ON_MY_WAY = 'on my way'
        DELIVERED_TO_First_WAREHOUSE = 'delivered to First warehouse'
        In_Transmit='In Transmit'
        DELIVERED_TO_Second_WAREHOUSE = 'delivered to Second warehouse'
        DELIVERED_SUCCESSFULLY = 'delivered successfully'
        FAILED_DELIVERY = 'failed delivery'
        CANCELLED = 'cancelled'

    class PaymentMethod(models.TextChoices):
        CASH_ON_DELIVERY = 'Cash on Delivery'
        CREDIT_CARD='Credit Card'
        BALANCE = 'Balance'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_number = models.CharField(max_length=20, unique=True, db_index=True)
    user_id = models.BigIntegerField()
    address_id = models.BigIntegerField()
    payment_method = models.CharField(max_length=50, choices=PaymentMethod.choices, default=PaymentMethod.CASH_ON_DELIVERY)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    delivery_fee =  models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    final_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    status = models.CharField(max_length=50, choices=OrderStatus.choices, default=OrderStatus.CREATED)
    paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = OrderManager()

    def __str__(self):
        return f"Order ID: {self.order_number} for User {self.user_id}"

    def generate_order_number(self):
        prefix = '20'
        while True:
            unique_part = ''.join(random.choices(string.digits, k=10))
            order_number = prefix + unique_part
            if not Order.objects.filter(order_number=order_number).exists():
                return order_number

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user_id", "created_at"])]

@receiver(pre_save, sender=Order)
def set_order_number(sender, instance, **kwargs):
    if not instance.order_number:
        instance.order_number = instance.generate_order_number()

class DeliveryBatch(models.Model):
    class BatchStatus(models.TextChoices):
        PENDING = 'pending'
        ASSIGNED = 'assigned'
        IN_PROGRESS = 'in_progress'
        COMPLETED = 'completed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    delivery_person_id = models.BigIntegerField(null=True, blank=True)
    target_state = models.CharField(max_length=250)
    status = models.CharField(max_length=50, choices=BatchStatus.choices, default=BatchStatus.PENDING)
    total_base_payout = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Batch {self.id} for {self.target_state} ({self.status})"

class Shipment(models.Model):
    class ShipmentStatus(models.TextChoices):
        CREATED = 'created'
        READY_TO_SHIP ='ready_to_ship'
        ON_MY_WAY = 'on my way'
        DELIVERED_TO_First_WAREHOUSE = 'delivered to First warehouse'
        In_Transmit='In Transmit'
        DELIVERED_TO_Second_WAREHOUSE = 'delivered to Second warehouse'
        DELIVERED_SUCCESSFULLY = 'delivered successfully'
        FAILED_DELIVERY = 'failed delivery'
        CANCELLED = 'cancelled'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="shipments", null=True, blank=True)
    return_request = models.ForeignKey(ReturnRequest, on_delete=models.CASCADE, related_name="shipments", null=True, blank=True)
    supplier_id = models.BigIntegerField(null=True)
    delivery_person_id = models.BigIntegerField(null=True, blank=True)
    from_state = models.CharField(max_length=250, blank=True)
    to_state = models.CharField(max_length=250, blank=True)
    from_address_id = models.BigIntegerField(null=True, blank=True)
    to_address_id = models.BigIntegerField(null=True, blank=True)
    confirmation_code = models.CharField(max_length=6, null=True, blank=True)
    delivery_confirmed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=50, choices=ShipmentStatus.choices, default=ShipmentStatus.CREATED)
    order_total_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    base_payout = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    delivery_batch = models.ForeignKey(DeliveryBatch, on_delete=models.SET_NULL, null=True, blank=True, related_name='shipments')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        constraints = [
            CheckConstraint(
                check=(
                    (Q(order__isnull=False) & Q(return_request__isnull=True)) |
                    (Q(order__isnull=True) & Q(return_request__isnull=False))
                ),
                name='shipment_has_one_parent'
            )
        ]

    def save(self, *args, **kwargs):
        if not self.confirmation_code:
            self.confirmation_code = ''.join(random.choices(string.digits, k=4))
        super().save(*args, **kwargs)

    def __str__(self):
        parent_id = self.order.id if self.order else self.return_request.id
        return f"Shipment for {parent_id} from Supplier {self.supplier_id}"

class OrderItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product_id = models.BigIntegerField()
    product_name = models.CharField(max_length=255, default='')
    supplier_id = models.BigIntegerField(null=True)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    color = models.CharField(max_length=20,blank=True, null=True)
    size = models.CharField(max_length=20,blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"OrderItem {self.product_name} for User {self.order.user_id}"

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["order", "product_id"])]

    def get_cost(self):
        return self.price * self.quantity

class ShipmentItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name="items")
    order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE, related_name="shipment_items", null=True, blank=True)
    return_request = models.ForeignKey(ReturnRequest, on_delete=models.CASCADE, related_name="shipment_items", null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    
    class Meta:
        constraints = [
            CheckConstraint(
                check=(
                    (Q(order_item__isnull=False) & Q(return_request__isnull=True)) |
                    (Q(order_item__isnull=True) & Q(return_request__isnull=False))
                ),
                name='shipment_item_has_one_parent'
            )
        ]

    def __str__(self):
        product_name = self.order_item.product_name if self.order_item else "Returned Product"
        return f"Shipment Item {product_name} in Shipment {self.shipment.id}"

class Coupon(models.Model):
    class DiscountType(models.TextChoices):
        PERCENTAGE = 'percentage'
        FIXED_AMOUNT = 'fixed_amount'

    supplier_id = models.BigIntegerField()
    code = models.CharField(max_length=50, unique=True)
    discount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    discount_type = models.CharField(max_length=12, choices=DiscountType.choices, default=DiscountType.PERCENTAGE)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    active = models.BooleanField(default=True)
    min_purchase_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, validators=[MinValueValidator(0)])
    max_uses = models.IntegerField(default=100)
    uses_count = models.IntegerField(default=0)
    max_uses_per_user = models.IntegerField(default=1)
    terms = models.TextField()
    product_ids = models.JSONField(default=list, blank=True)

    def __str__(self):
        return self.code

class CouponUsage(models.Model):
    user_id = models.BigIntegerField()
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE)
    used_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user_id', 'coupon')

class Warehouse(models.Model):
    name = models.CharField(max_length=100)
    address_id = models.BigIntegerField()
    contact_person = models.CharField(max_length=100, blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    delivery_fee= models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return self.name