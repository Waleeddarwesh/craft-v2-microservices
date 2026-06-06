import asyncio
import json
import logging
from aio_pika import connect_robust, IncomingMessage
from config import settings
from database import async_sessionmaker, AsyncSessionLocal
import models
from websockets_manager import manager
from fcm import send_push_notification

logger = logging.getLogger(__name__)

async def process_event(message: IncomingMessage):
    async with message.process():
        event_data = json.loads(message.body.decode())
        event_type = event_data.get("event_type")
        
        logger.info(f"Received event: {event_type}")
        
        # Determine if this event should trigger a notification
        notification_info = None
        
        if event_type == "order.placed":
            # For this example, we notify the user. In reality we might notify the supplier.
            user_id = event_data.get("user_id")
            order_id = event_data.get("order_id")
            notification_info = {
                "user_id": user_id,
                "message": f"Your order #{order_id} has been placed successfully.",
                "content_type": "order",
                "object_id": order_id
            }
        elif event_type == "order.delivered":
            user_id = event_data.get("user_id")
            order_id = event_data.get("order_id")
            notification_info = {
                "user_id": user_id,
                "message": f"Your order #{order_id} has been delivered.",
                "content_type": "order",
                "object_id": order_id
            }
        elif event_type == "payment.succeeded":
            user_id = event_data.get("user_id", 0) # Assuming payment event might need user_id or order_id to lookup
            order_id = event_data.get("order_id")
            notification_info = {
                "user_id": user_id,
                "message": f"Payment for order #{order_id} was successful.",
                "content_type": "payment",
                "object_id": order_id
            }
            
        # Add other event types as needed
        
        if notification_info and notification_info["user_id"]:
            await create_and_send_notification(notification_info)


async def create_and_send_notification(info: dict):
    user_id = info["user_id"]
    
    async with AsyncSessionLocal() as db:
        # Create DB record
        notif = models.Notification(
            user_id=user_id,
            message=info["message"],
            content_type=info.get("content_type"),
            object_id=info.get("object_id")
        )
        db.add(notif)
        await db.commit()
        await db.refresh(notif)
        
        # Push via WebSocket
        ws_msg = {
            "type": "new_notification",
            "data": {
                "id": notif.id,
                "message": notif.message,
                "timestamp": notif.timestamp.isoformat(),
                "content_type": notif.content_type,
                "object_id": notif.object_id
            }
        }
        await manager.send_personal_message(ws_msg, user_id)
        
        # Check preferences and optionally send FCM
        from sqlalchemy import select
        result = await db.execute(select(models.NotificationPreference).where(models.NotificationPreference.user_id == user_id))
        pref = result.scalars().first()
        
        if not pref or pref.push:
            await send_push_notification(user_id, "New Notification", info["message"])


async def start_consumer():
    while True:
        try:
            logger.info(f"Connecting to RabbitMQ at {settings.rabbitmq_url}")
            connection = await connect_robust(settings.rabbitmq_url)
            channel = await connection.channel()
            
            exchange = await channel.declare_exchange('craft_events', type='topic', durable=True)
            queue = await channel.declare_queue('realtime_notifications_queue', durable=True)
            
            # Subscribe to all events for now, or specific ones
            await queue.bind(exchange, routing_key='#')
            
            logger.info("Started RabbitMQ consumer for realtime-service")
            await queue.consume(process_event)
            
            # Keep running
            await asyncio.Future()
        except Exception as e:
            logger.error(f"RabbitMQ consumer error: {e}. Reconnecting in 5s...")
            await asyncio.sleep(5)
