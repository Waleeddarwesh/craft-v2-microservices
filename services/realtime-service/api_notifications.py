from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from typing import List
from database import get_db
import models
import schemas
from auth import get_current_user_id

notif_router = APIRouter(prefix="/notifications", tags=["notifications"])

@notif_router.get("/", response_model=List[schemas.NotificationResponse])
async def list_notifications(skip: int = 0, limit: int = 50, db: AsyncSession = Depends(get_db), current_user_id: int = Depends(get_current_user_id)):
    result = await db.execute(
        select(models.Notification).where(
            models.Notification.user_id == current_user_id
        ).order_by(models.Notification.timestamp.desc()).offset(skip).limit(limit)
    )
    return result.scalars().all()

@notif_router.post("/{id}/read/")
async def mark_read(id: int, db: AsyncSession = Depends(get_db), current_user_id: int = Depends(get_current_user_id)):
    result = await db.execute(select(models.Notification).where(models.Notification.id == id))
    notif = result.scalars().first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    if notif.user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
        
    notif.is_read = True
    await db.commit()
    return {"status": "success"}

@notif_router.post("/read-all/")
async def mark_all_read(db: AsyncSession = Depends(get_db), current_user_id: int = Depends(get_current_user_id)):
    await db.execute(
        update(models.Notification)
        .where(models.Notification.user_id == current_user_id, models.Notification.is_read == False)
        .values(is_read=True)
    )
    await db.commit()
    return {"status": "success"}

@notif_router.delete("/{id}/")
async def delete_notification(id: int, db: AsyncSession = Depends(get_db), current_user_id: int = Depends(get_current_user_id)):
    result = await db.execute(select(models.Notification).where(models.Notification.id == id))
    notif = result.scalars().first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    if notif.user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
        
    await db.delete(notif)
    await db.commit()
    return {"status": "success"}

@notif_router.get("/unread-count/")
async def get_unread_count(db: AsyncSession = Depends(get_db), current_user_id: int = Depends(get_current_user_id)):
    result = await db.execute(
        select(func.count(models.Notification.id))
        .where(models.Notification.user_id == current_user_id, models.Notification.is_read == False)
    )
    count = result.scalar()
    return {"unread_count": count}

@notif_router.get("/preferences/", response_model=schemas.NotificationPreferenceResponse)
async def get_preferences(db: AsyncSession = Depends(get_db), current_user_id: int = Depends(get_current_user_id)):
    result = await db.execute(select(models.NotificationPreference).where(models.NotificationPreference.user_id == current_user_id))
    pref = result.scalars().first()
    if not pref:
        pref = models.NotificationPreference(user_id=current_user_id)
        db.add(pref)
        await db.commit()
        await db.refresh(pref)
    return pref

@notif_router.put("/preferences/", response_model=schemas.NotificationPreferenceResponse)
async def update_preferences(data: schemas.NotificationPreferenceUpdate, db: AsyncSession = Depends(get_db), current_user_id: int = Depends(get_current_user_id)):
    pref = await get_preferences(db, current_user_id)
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(pref, key, value)
    await db.commit()
    await db.refresh(pref)
    return pref
