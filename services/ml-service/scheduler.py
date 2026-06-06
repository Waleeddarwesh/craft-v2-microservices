import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from services import update_content_based_recommendations
from database import AsyncSessionLocal
import logging

logger = logging.getLogger(__name__)

async def run_nightly_training():
    logger.info("Running nightly content-based recommendation training...")
    async with AsyncSessionLocal() as session:
        await update_content_based_recommendations(session)
    logger.info("Nightly training complete.")

async def run_daily_analytics():
    logger.info("Running daily analytics aggregation...")
    # Add analytics aggregation logic here
    pass

def start_scheduler():
    scheduler = AsyncIOScheduler()
    # Run at 2 AM every day
    scheduler.add_job(run_nightly_training, 'cron', hour=2, minute=0)
    # Run at 3 AM every day
    scheduler.add_job(run_daily_analytics, 'cron', hour=3, minute=0)
    
    scheduler.start()
    logger.info("Scheduler started.")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    start_scheduler()
    try:
        asyncio.get_event_loop().run_forever()
    except (KeyboardInterrupt, SystemExit):
        pass
