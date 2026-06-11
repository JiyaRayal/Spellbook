from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    display_name: Optional[str] = None
    house: Optional[str] = None

    @field_validator('username')
    @classmethod
    def username_valid(cls, v):
        if not v.replace('_','').isalnum():
            raise ValueError('Username must be alphanumeric')
        if len(v) < 3 or len(v) > 50:
            raise ValueError('Username must be 3-50 characters')
        return v.lower()

    @field_validator('password')
    @classmethod
    def password_valid(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v

class UserLogin(BaseModel):
    username: str
    password: str

class UserUpdate(BaseModel):
    display_name: Optional[str] = None
    bio: Optional[str] = None
    house: Optional[str] = None

class UserOut(BaseModel):
    id: int
    username: str
    email: str
    display_name: Optional[str] = None
    bio: Optional[str] = None
    profile_picture: Optional[str] = None
    house: Optional[str] = None
    created_at: datetime
    followers_count: Optional[int] = 0
    following_count: Optional[int] = 0
    is_following: Optional[bool] = False
    class Config:
        from_attributes = True

class UserPublic(BaseModel):
    id              : int
    username        : str
    display_name    : Optional[str] = None
    profile_picture : Optional[str] = None
    house           : Optional[str] = None
    bio             : Optional[str] = None
    followers_count : Optional[int] = 0
    following_count : Optional[int] = 0
    is_following    : Optional[bool] = False
    # Duel stats
    duel_wins       : Optional[int] = 0
    duel_losses     : Optional[int] = 0
    is_champion     : Optional[bool] = False

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserOut