from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.core.database import Base

class Duel(Base):
    __tablename__ = "duels"

    id                  = Column(Integer, primary_key=True, index=True)
    topic               = Column(Text, nullable=False)  # Debate topic
    challenger_id       = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    defender_id         = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    challenger_spell_id = Column(Integer, ForeignKey("spells.id", ondelete="CASCADE"), nullable=False)
    defender_spell_id   = Column(Integer, ForeignKey("spells.id", ondelete="CASCADE"), nullable=True)
    challenger_stance   = Column(String(10), default="FOR")     # FOR / AGAINST
    defender_stance     = Column(String(10), default="AGAINST") # Always opposite
    status              = Column(String(20), default="pending")
    # pending   = challenge bheja
    # active    = voting chal rahi hai
    # completed = winner decide ho gaya
    # declined  = defender ne decline kiya
    winner_id           = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at          = Column(DateTime(timezone=True), server_default=func.now())
    ends_at             = Column(DateTime(timezone=True), nullable=True)

    challenger       = relationship("User", foreign_keys=[challenger_id])
    defender         = relationship("User", foreign_keys=[defender_id])
    challenger_spell = relationship("Spell", foreign_keys=[challenger_spell_id])
    defender_spell   = relationship("Spell", foreign_keys=[defender_spell_id])
    winner           = relationship("User", foreign_keys=[winner_id])
    votes            = relationship("DuelVote", back_populates="duel", cascade="all, delete-orphan")


class DuelVote(Base):
    __tablename__ = "duel_votes"

    id         = Column(Integer, primary_key=True, index=True)
    duel_id    = Column(Integer, ForeignKey("duels.id", ondelete="CASCADE"), nullable=False)
    voter_id   = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    voted_for  = Column(String(20), nullable=False)  # "challenger" or "defender"
    reason     = Column(Text, nullable=True)          # Why they voted
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    duel  = relationship("Duel", back_populates="votes")
    voter = relationship("User")