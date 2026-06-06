from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_, update
from typing import List
from database import get_db
import models
import schemas
from auth import get_current_user_id

chat_router = APIRouter(prefix="/chat", tags=["chat"])

@chat_router.get("/conversations/", response_model=List[schemas.ConversationResponse])
async def list_conversations(db: AsyncSession = Depends(get_db), current_user_id: int = Depends(get_current_user_id)):
    result = await db.execute(
        select(models.Conversation).where(
            or_(
                models.Conversation.initiator_id == current_user_id,
                models.Conversation.receiver_id == current_user_id
            )
        ).order_by(models.Conversation.start_time.desc())
    )
    return result.scalars().all()

@chat_router.post("/conversations/start/", response_model=schemas.ConversationResponse)
async def start_conversation(data: schemas.ConversationCreate, db: AsyncSession = Depends(get_db), current_user_id: int = Depends(get_current_user_id)):
    # Check if conversation already exists
    result = await db.execute(
        select(models.Conversation).where(
            or_(
                and_(models.Conversation.initiator_id == current_user_id, models.Conversation.receiver_id == data.receiver_id),
                and_(models.Conversation.initiator_id == data.receiver_id, models.Conversation.receiver_id == current_user_id)
            )
        )
    )
    conv = result.scalars().first()
    if conv:
        return conv

    # Create new
    new_conv = models.Conversation(initiator_id=current_user_id, receiver_id=data.receiver_id)
    db.add(new_conv)
    await db.commit()
    await db.refresh(new_conv)
    return new_conv

@chat_router.get("/conversations/{id}/", response_model=schemas.ConversationResponse)
async def get_conversation(id: int, db: AsyncSession = Depends(get_db), current_user_id: int = Depends(get_current_user_id)):
    result = await db.execute(select(models.Conversation).where(models.Conversation.id == id))
    conv = result.scalars().first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if current_user_id not in [conv.initiator_id, conv.receiver_id]:
        raise HTTPException(status_code=403, detail="Not a participant in this conversation")
    return conv

@chat_router.get("/conversations/{id}/messages/", response_model=List[schemas.MessageResponse])
async def list_messages(id: int, skip: int = 0, limit: int = 50, db: AsyncSession = Depends(get_db), current_user_id: int = Depends(get_current_user_id)):
    await get_conversation(id, db, current_user_id) # Access check
    result = await db.execute(
        select(models.Message).where(
            models.Message.conversation_id == id
        ).order_by(models.Message.timestamp.desc()).offset(skip).limit(limit)
    )
    return result.scalars().all()

@chat_router.post("/conversations/{id}/messages/", response_model=schemas.MessageResponse)
async def send_message(id: int, data: schemas.MessageCreate, db: AsyncSession = Depends(get_db), current_user_id: int = Depends(get_current_user_id)):
    conv = await get_conversation(id, db, current_user_id) # Access check
    
    msg = models.Message(
        sender_id=current_user_id,
        text=data.text,
        attachment=data.attachment,
        conversation_id=id,
        reply_to_id=data.reply_to_id
    )
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    # TODO: WebSocket broadcast & FCM push here
    return msg

@chat_router.patch("/conversations/{id}/messages/read/")
async def mark_messages_read(id: int, db: AsyncSession = Depends(get_db), current_user_id: int = Depends(get_current_user_id)):
    await get_conversation(id, db, current_user_id)
    
    # Mark messages as read where sender is NOT the current user
    await db.execute(
        update(models.Message)
        .where(models.Message.conversation_id == id, models.Message.sender_id != current_user_id, models.Message.is_read == False)
        .values(is_read=True)
    )
    await db.commit()
    return {"status": "success"}

@chat_router.delete("/messages/{id}/")
async def delete_message(id: int, db: AsyncSession = Depends(get_db), current_user_id: int = Depends(get_current_user_id)):
    result = await db.execute(select(models.Message).where(models.Message.id == id))
    msg = result.scalars().first()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    if msg.sender_id != current_user_id:
        raise HTTPException(status_code=403, detail="Cannot delete someone else's message")
        
    msg.is_deleted = True
    await db.commit()
    return {"status": "success"}
