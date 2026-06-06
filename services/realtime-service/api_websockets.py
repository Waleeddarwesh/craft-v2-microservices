from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from websockets_manager import manager
from auth import get_current_user_id
import json

ws_router = APIRouter(prefix="/ws", tags=["websockets"])

@ws_router.websocket("/notifications/")
async def websocket_notifications(websocket: WebSocket, token: str):
    # Manually extract user id since Security dependencies behave differently in WebSockets
    # We accept token as a query parameter: /ws/notifications/?token=...
    class FakeRequest:
        def __init__(self, token):
            self.query_params = {"token": token}
            self.headers = {}
            
    try:
        class FakeToken:
            def __init__(self, t):
                self.credentials = t
        user_id = get_current_user_id(FakeRequest(token), FakeToken(token))
    except Exception as e:
        await websocket.close(code=1008, reason="Unauthorized")
        return

    await manager.connect(websocket, user_id)
    try:
        while True:
            # Notifications connection is mostly write-only from server to client
            # But we can listen for pings or acks
            data = await websocket.receive_text()
            # Handle incoming data if needed
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)


@ws_router.websocket("/chat/{conversation_id}/")
async def websocket_chat(websocket: WebSocket, conversation_id: int, token: str):
    class FakeRequest:
        def __init__(self, token):
            self.query_params = {"token": token}
            self.headers = {}
            
    try:
        class FakeToken:
            def __init__(self, t):
                self.credentials = t
        user_id = get_current_user_id(FakeRequest(token), FakeToken(token))
    except Exception as e:
        await websocket.close(code=1008, reason="Unauthorized")
        return

    # TODO: Validate that user is part of the conversation via DB lookup
    
    await manager.connect(websocket, user_id)
    manager.subscribe_to_chat(user_id, conversation_id)
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Here we could handle typing indicators
            if message_data.get("type") == "typing":
                # Broadcast typing indicator to other participant
                pass
                
    except WebSocketDisconnect:
        manager.unsubscribe_from_chat(user_id, conversation_id)
        manager.disconnect(websocket, user_id)
