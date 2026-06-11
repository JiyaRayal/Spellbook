from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime
from backend.schemas.user import UserPublic

class SpellCreate(BaseModel):
    content: str
    echo_of_id: Optional[int] = None

    @field_validator('content')
    @classmethod
    def content_valid(cls, v):
        if not v.strip():
            raise ValueError('Content cannot be empty')
        if len(v) > 280:
            raise ValueError('Spell cannot exceed 280 characters')
        return v

class ReplyCreate(BaseModel):
    content: str

    @field_validator('content')
    @classmethod
    def content_valid(cls, v):
        if not v.strip():
            raise ValueError('Reply cannot be empty')
        if len(v) > 280:
            raise ValueError('Reply cannot exceed 280 characters')
        return v

class ReplyOut(BaseModel):
    id: int
    content: str
    author: UserPublic
    spell_id: int
    created_at: datetime
    class Config:
        from_attributes = True

class SpellOut(BaseModel):
    id: int
    content: str
    image_url: Optional[str] = None
    author: UserPublic
    echo_of_id: Optional[int] = None
    echo_of: Optional['SpellOut'] = None
    created_at: datetime
    charms_count: Optional[int] = 0
    replies_count: Optional[int] = 0
    echoes_count: Optional[int] = 0
    is_charmed: Optional[bool] = False
    is_echoed: Optional[bool] = False
    class Config:
        from_attributes = True

SpellOut.model_rebuild()

class FeedResponse(BaseModel):
    spells: List[SpellOut]
    total: int
    page: int
    per_page: int