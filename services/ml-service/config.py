import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    rabbitmq_url: str = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
    database_url: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./ml_service.db")

settings = Settings()
