from django.db.models.signals import post_save
from django.dispatch import receiver
from craft_common.events import EventPublisher, schemas
from .models import PaymentHistory

publisher = EventPublisher()

@receiver(post_save, sender=PaymentHistory)
def payment_saved(sender, instance, created, **kwargs):
    if instance.status == PaymentHistory.PaymentStatus.SUCCESS:
        event = schemas.PaymentSucceededEvent(
            order_id=instance.order.id,
            transaction_id=instance.transaction_id or ""
        )
        publisher.publish(event)
    elif instance.status == PaymentHistory.PaymentStatus.FAILED:
        event = schemas.PaymentFailedEvent(
            order_id=instance.order.id,
            reason="Payment failed"
        )
        publisher.publish(event)
