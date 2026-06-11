from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.core.database import Base

class Follow(Base):
    __tablename__ = "follows"
    follower_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    following_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    display_name = Column(String(100), nullable=True)
    bio = Column(Text, nullable=True)
    profile_picture = Column(String(500), nullable=True)
    house = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True)
    # ── Duel Stats (ADD THESE 3 LINES) ──
    duel_wins   = Column(Integer, default=0)
    duel_losses = Column(Integer, default=0)
    is_champion = Column(Boolean, default=False)
    # ────────────────────────────────────
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    spells = relationship("Spell", back_populates="author", cascade="all, delete-orphan")
    charms = relationship("Charm", back_populates="user", cascade="all, delete-orphan")
    replies = relationship("Reply", back_populates="author", cascade="all, delete-orphan")
    followers = relationship(
        "User", secondary="follows",
        primaryjoin="User.id == Follow.following_id",
        secondaryjoin="User.id == Follow.follower_id",
        backref="following"
    )