from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.core.database import Base

class Spell(Base):
    __tablename__ = "spells"
    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    image_url = Column(String(500), nullable=True)
    author_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    echo_of_id = Column(Integer, ForeignKey("spells.id", ondelete="SET NULL"), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    city = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    author = relationship("User", back_populates="spells")
    charms = relationship("Charm", back_populates="spell", cascade="all, delete-orphan")
    replies = relationship("Reply", back_populates="spell", cascade="all, delete-orphan")
    echo_of = relationship("Spell", remote_side="Spell.id", backref="echoes")

class Charm(Base):
    __tablename__ = "charms"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    spell_id = Column(Integer, ForeignKey("spells.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    user = relationship("User", back_populates="charms")
    spell = relationship("Spell", back_populates="charms")

class Reply(Base):
    __tablename__ = "replies"
    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    author_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    spell_id = Column(Integer, ForeignKey("spells.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    author = relationship("User", back_populates="replies")
    spell = relationship("Spell", back_populates="replies")