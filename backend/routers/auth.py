from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.core.database import get_db
from backend.core.security import verify_password, get_password_hash, create_access_token, get_current_user
from backend.models.user import User
from backend.schemas.user import UserCreate, UserLogin, Token, UserOut

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

def fmt_user(user, current_user=None):
    return {
        "id": user.id, "username": user.username, "email": user.email,
        "display_name": user.display_name or user.username,
        "bio": user.bio, "profile_picture": user.profile_picture,
        "house": user.house, "created_at": user.created_at,
        "followers_count": len(user.followers),
        "following_count": len(user.following),
        "is_following": current_user in user.followers if current_user else False,
    }

@router.post("/signup", response_model=Token, status_code=201)
async def signup(data: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(400, "Username already taken")
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(400, "Email already registered")
    user = User(
        username=data.username, email=data.email,
        hashed_password=get_password_hash(data.password),
        display_name=data.display_name or data.username,
        house=data.house,
    )
    db.add(user); db.commit(); db.refresh(user)
    token = create_access_token({"sub": user.username})
    return Token(access_token=token, token_type="bearer", user=UserOut(**fmt_user(user)))

@router.post("/login", response_model=Token)
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == credentials.username.lower()).first()
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(401, "Incorrect username or password")
    token = create_access_token({"sub": user.username})
    return Token(access_token=token, token_type="bearer", user=UserOut(**fmt_user(user)))

@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserOut(**fmt_user(current_user, current_user))