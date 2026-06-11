from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.core.database import get_db
from backend.models.user import User
from backend.models.spell import Spell, Charm, Reply

router = APIRouter(prefix="/api", tags=["Health"])

@router.get("/health")
async def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {e}"
    return {"status": "🟢 Spellbook is open", "database": db_status, "version": "1.0.0"}

@router.get("/stats")
async def stats(db: Session = Depends(get_db)):
    return {
        "wizards": db.query(User).filter(User.is_active==True).count(),
        "spells_cast": db.query(Spell).filter(Spell.is_deleted==False).count(),
        "charms": db.query(Charm).count(),
        "replies": db.query(Reply).count(),
    }