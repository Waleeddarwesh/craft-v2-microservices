import asyncio
from craft_common.events import EventConsumer
import logging
from database import AsyncSessionLocal
from models import UserProductInteraction, AnalyticsAggregate
from services import update_content_based_recommendations

logger = logging.getLogger(__name__)

async def handle_order_placed(payload):
    logger.info(f"Received order.placed: {payload}")
    user_id = payload.get("user_id")
    items = payload.get("items", [])
    
    async with AsyncSessionLocal() as session:
        for item in items:
            session.add(UserProductInteraction(
                user_id=user_id,
                product_id=item['product_id'],
                interaction_type='purchase'
            ))
        await session.commit()
        
        # Trigger async re-training (in reality we might want this batched)
        # await update_content_based_recommendations(session)

async def handle_product_viewed(payload):
    logger.info(f"Received product.viewed: {payload}")
    user_id = payload.get("user_id")
    product_id = payload.get("product_id")
    
    if user_id and product_id:
        async with AsyncSessionLocal() as session:
            session.add(UserProductInteraction(
                user_id=user_id,
                product_id=product_id,
                interaction_type='view'
            ))
            await session.commit()

def run_consumer():
    consumer = EventConsumer(queue_name='ml_service_queue')
    
    # We need to wrap async handlers to run in sync event callback from pika
    def sync_wrapper(coro):
        def wrapper(payload):
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop and loop.is_running():
                loop.create_task(coro(payload))
            else:
                asyncio.run(coro(payload))
        return wrapper

    consumer.subscribe('order.placed', sync_wrapper(handle_order_placed))
    consumer.subscribe('product.viewed', sync_wrapper(handle_product_viewed))
    
    logger.info("Starting ml-service event consumer...")
    try:
        consumer.start_consuming()
    except KeyboardInterrupt:
        logger.info("Stopping ml-service event consumer...")
        consumer.stop_consuming()

if __name__ == "__main__":
    run_consumer()
