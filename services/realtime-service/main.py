from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings
import asyncio
from consumer import start_consumer

app = FastAPI(title="Real-Time Service")

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(start_consumer())

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from api_chat import chat_router
from api_notifications import notif_router
from api_websockets import ws_router

app.include_router(chat_router)
app.include_router(notif_router)
app.include_router(ws_router)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "realtime-service"}
