from fastapi import FastAPI, BackgroundTasks, Depends
import logging
from contextlib import asynccontextmanager
from database import engine, get_db, Base
from sqlalchemy.ext.asyncio import AsyncSession
from services import get_collaborative_filtering_recommendations, update_content_based_recommendations

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up ML service...")
    # Initialize DB tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    logger.info("Shutting down ML service...")

app = FastAPI(title="ML Service", version="1.0", lifespan=lifespan)

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/recommendations/{user_id}/collaborative")
async def get_collaborative(user_id: int, product_id: int, db: AsyncSession = Depends(get_db)):
    rec_ids = await get_collaborative_filtering_recommendations(product_id, db)
    return {"user_id": user_id, "recommendations": rec_ids}

@app.post("/internal/recommendations/train")
async def train_recommendations(background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    background_tasks.add_task(update_content_based_recommendations, db)
    return {"status": "training_started"}
