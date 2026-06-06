from django.db import models
import uuid

class PaymentHistory(models.Model):
    """
    Model to log payment attempts and their status.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.BigIntegerField(
        blank=True,
        null=True,
        help_text="The user who initiated the payment."
    )
    order_id = models.UUIDField(
        blank=True,
        null=True,
        help_text="The associated order for the payment, if any."
    )
    cart_id = models.UUIDField(
        blank=True,
        null=True,
        help_text="The associated cart for the payment."
    )
    address_id = models.BigIntegerField(
        blank=True,
        null=True,
        help_text="The address used for the order."
    )
    coupon_code = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="The coupon code used for the order."
    )
    course_id = models.BigIntegerField(
        blank=True,
        null=True,
        help_text="The associated course for the payment, if any."
    )
    stripe_session_id = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True,
        help_text="The ID of the Stripe checkout session."
    )
    stripe_payment_intent_id = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True,
        help_text="The ID of the Stripe Payment Intent associated with the transaction."
    )
    date = models.DateTimeField(
        auto_now_add=True,
        help_text="The date and time the payment record was created."
    )
    payment_status = models.CharField(
        max_length=50,
        default='pending',
        choices=[('pending', 'Pending'), ('succeeded', 'Succeeded'), ('failed', 'Failed')],
        help_text="The status of the payment (e.g., pending, succeeded, failed)."
    )

    class Meta:
        verbose_name_plural = "Payment Histories"

    def __str__(self):
        if self.order_id:
            return f"Payment for Order {self.order_id} - {self.payment_status}"
        elif self.course_id:
            return f"Payment for Course {self.course_id} - {self.payment_status}"
        return f"Payment by User {self.user_id} - {self.payment_status}"

class StripeWebhookEvent(models.Model):
    event_id = models.CharField(max_length=255, unique=True)
    event_type = models.CharField(max_length=255)
    status = models.CharField(max_length=50, default='processed')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.event_type} - {self.event_id}"