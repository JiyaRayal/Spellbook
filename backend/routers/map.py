from datetime import datetime

from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.core.database import get_db
from backend.core.security import get_current_user, get_optional_user
from backend.models.spell import Spell
from backend.models.user import User

router = APIRouter(prefix="/api/map", tags=["Marauder's Map"])


class PrivacyUpdate(BaseModel):
    enabled: bool


@router.get("/activity")
async def recent_activity(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    query = (
        db.query(Spell)
        .join(Spell.author)
        .filter(
            Spell.is_deleted == False,
            Spell.latitude.isnot(None),
            Spell.longitude.isnot(None),
            User.mischief_managed == False,
        )
        .order_by(desc(Spell.created_at))
        .limit(200)
    )
    activities = []
    for spell in query.all():
        activities.append({
            "id": spell.id,
            "username": spell.author.username,
            "content": spell.content,
            "latitude": spell.latitude,
            "longitude": spell.longitude,
            "city": spell.city,
            "country": spell.country,
            "created_at": spell.created_at,
        })
    return {"activities": activities, "generated_at": datetime.utcnow()}


@router.get("/privacy")
async def get_privacy(current_user: User = Depends(get_current_user)):
    return {"mischief_managed": bool(current_user.mischief_managed)}


@router.put("/privacy")
async def update_privacy(
    payload: PrivacyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    current_user.mischief_managed = payload.enabled
    db.commit()
    return {"mischief_managed": payload.enabled}
