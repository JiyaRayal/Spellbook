from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List
from backend.core.database import get_db
from backend.core.security import get_current_user
from backend.models.notification import Notification
from backend.models.user import User
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])

class NotifOut(BaseModel):
    id         : int
    type       : str
    message    : str
    link_id    : Optional[int] = None
    is_read    : bool
    created_at : datetime
    class Config:
        from_attributes = True

@router.get("/", response_model=List[NotifOut])
async def get_notifications(
    db: Session = Depends(get_db),
    cu: User = Depends(get_current_user)
):
    return db.query(Notification)\
             .filter(Notification.user_id == cu.id)\
             .order_by(desc(Notification.created_at))\
             .limit(30).all()

@router.get("/unread-count")
async def unread_count(
    db: Session = Depends(get_db),
    cu: User = Depends(get_current_user)
):
    count = db.query(Notification)\
              .filter(Notification.user_id == cu.id, Notification.is_read == False)\
              .count()
    return {"count": count}

@router.post("/mark-read")
async def mark_all_read(
    db: Session = Depends(get_db),
    cu: User = Depends(get_current_user)
):
    db.query(Notification)\
      .filter(Notification.user_id == cu.id, Notification.is_read == False)\
      .update({"is_read": True})
    db.commit()
    return {"message": "All marked as read"}