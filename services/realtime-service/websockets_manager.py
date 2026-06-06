from fastapi import WebSocket
from typing import Dict, List
import asyncio
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        # user_id -> list of active WebSocket connections
        self.active_connections: Dict[int, List[WebSocket]] = {}
        # user_id -> set of conversation_ids they are actively watching
        self.active_chats: Dict[int, set[int]] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
            self.active_chats[user_id] = set()
            # TODO: Update user presence to online in DB
        self.active_connections[user_id].append(websocket)
        logger.info(f"User {user_id} connected via WebSocket. Total connections: {len(self.active_connections[user_id])}")

    def disconnect(self, websocket: WebSocket, user_id: int):
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                del self.active_chats[user_id]
                # TODO: Update user presence to offline in DB
                logger.info(f"User {user_id} completely disconnected.")

    async def send_personal_message(self, message: dict, user_id: int):
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending message to user {user_id}: {e}")

    async def broadcast_to_conversation(self, message: dict, conversation_id: int, participants: List[int]):
        for user_id in participants:
            if user_id in self.active_connections:
                # User is online, send the message
                await self.send_personal_message(message, user_id)

    def subscribe_to_chat(self, user_id: int, conversation_id: int):
        if user_id in self.active_chats:
            self.active_chats[user_id].add(conversation_id)

    def unsubscribe_from_chat(self, user_id: int, conversation_id: int):
        if user_id in self.active_chats:
            self.active_chats[user_id].discard(conversation_id)

manager = ConnectionManager()
