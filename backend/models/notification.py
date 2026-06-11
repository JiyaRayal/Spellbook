from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.core.database import Base

class Notification(Base):
    __tablename__ = "notifications"

    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    type       = Column(String(50), nullable=False)
    # Types:
    # "duel_challenge"  — someone challenged you
    # "duel_accepted"   — your challenge was accepted
    # "duel_completed"  — duel ended, here's winner
    # "charm"           — someone charmed your spell
    # "reply"           — someone replied to your spell
    # "follow"          — someone followed you
    # "champion"        — you earned champion badge
    message    = Column(Text, nullable=False)
    link_id    = Column(Integer, nullable=True)   # duel_id or spell_id
    is_read    = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")