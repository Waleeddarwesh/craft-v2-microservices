from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

# --- Chat Schemas ---

class ConversationCreate(BaseModel):
    receiver_id: int

class ConversationResponse(BaseModel):
    id: int
    initiator_id: int
    receiver_id: int
    start_time: datetime
    model_config = ConfigDict(from_attributes=True)

class MessageCreate(BaseModel):
    text: Optional[str] = None
    attachment: Optional[str] = None
    reply_to_id: Optional[int] = None

class MessageResponse(BaseModel):
    id: int
    sender_id: int
    text: Optional[str]
    attachment: Optional[str]
    conversation_id: int
    timestamp: datetime
    is_read: bool
    is_deleted: bool
    reply_to_id: Optional[int]
    model_config = ConfigDict(from_attributes=True)

# --- Notification Schemas ---

class NotificationResponse(BaseModel):
    id: int
    user_id: int
    message: str
    image: Optional[str]
    timestamp: datetime
    is_read: bool
    content_type: Optional[str]
    object_id: Optional[int]
    model_config = ConfigDict(from_attributes=True)

class NotificationPreferenceUpdate(BaseModel):
    in_app: Optional[bool] = None
    email: Optional[bool] = None
    push: Optional[bool] = None
    sms: Optional[bool] = None

class NotificationPreferenceResponse(BaseModel):
    id: int
    user_id: int
    in_app: bool
    email: bool
    push: bool
    sms: bool
    model_config = ConfigDict(from_attributes=True)
