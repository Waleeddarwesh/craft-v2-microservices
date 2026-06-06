from django.db.models.signals import post_save
from django.dispatch import receiver
from craft_common.events import EventPublisher, schemas
from .models import Order

publisher = EventPublisher()

@receiver(post_save, sender=Order)
def order_saved(sender, instance, created, **kwargs):
    if created:
        event = schemas.OrderCreatedEvent(
            order_id=instance.id,
            user_id=instance.user.id,
            items=[] # Items are added later
        )
        publisher.publish(event)
    else:
        # Check status changes if needed
        if instance.status == Order.OrderStatus.DELIVERED_SUCCESSFULLY:
            event = schemas.OrderDeliveredEvent(
                order_id=instance.id,
                delivered_at=instance.updated_at.isoformat()
            )
            publisher.publish(event)
        elif instance.status == Order.OrderStatus.CANCELLED:
            event = schemas.OrderCancelledEvent(
                order_id=instance.id,
                reason="Cancelled by user"
            )
            publisher.publish(event)
