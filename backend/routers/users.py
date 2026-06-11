from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional, List
import os, uuid, shutil
from backend.core.database import get_db
from backend.core.security import get_current_user, get_optional_user
from backend.models.user import User, Follow
from backend.schemas.user import UserOut, UserPublic
from backend.core.config import settings

router = APIRouter(prefix="/api/users", tags=["Users"])

def fmt(user, current_user=None):
    return {"id":user.id,"username":user.username,"email":user.email,
            "display_name":user.display_name or user.username,"bio":user.bio,
            "profile_picture":user.profile_picture,"house":user.house,
            "created_at":user.created_at,"followers_count":len(user.followers),
            "following_count":len(user.following),
            "is_following":current_user in user.followers if current_user else False}

def pub(user, current_user=None):
    return UserPublic(id=user.id,username=user.username,
                      display_name=user.display_name or user.username,
                      profile_picture=user.profile_picture,house=user.house,bio=user.bio,
                      followers_count=len(user.followers),following_count=len(user.following),
                      is_following=current_user in user.followers if current_user else False)

@router.get("/search/wizards", response_model=List[UserPublic])
async def search(q: str, db: Session = Depends(get_db), cu=Depends(get_optional_user)):
    users = db.query(User).filter(User.username.ilike(f"%{q}%") | User.display_name.ilike(f"%{q}%")).limit(20).all()
    return [pub(u, cu) for u in users]

@router.get("/{username}", response_model=UserOut)
async def get_user(username: str, db: Session = Depends(get_db), cu=Depends(get_optional_user)):
    user = db.query(User).filter(User.username == username.lower()).first()
    if not user: raise HTTPException(404, "Wizard not found")
    return UserOut(**fmt(user, cu))

@router.put("/me/update", response_model=UserOut)
async def update(display_name: Optional[str]=Form(None), bio: Optional[str]=Form(None),
                 house: Optional[str]=Form(None), profile_picture: Optional[UploadFile]=File(None),
                 db: Session=Depends(get_db), cu: User=Depends(get_current_user)):
    if display_name is not None: cu.display_name = display_name
    if bio is not None: cu.bio = bio
    if house is not None: cu.house = house
    if profile_picture and profile_picture.filename:
        d = os.path.join(settings.UPLOAD_DIR, "avatars"); os.makedirs(d, exist_ok=True)
        ext = profile_picture.filename.split(".")[-1].lower()
        if ext not in ["jpg","jpeg","png","gif","webp"]: raise HTTPException(400,"Invalid image format")
        fn = f"{uuid.uuid4()}.{ext}"; fp = os.path.join(d, fn)
        with open(fp,"wb") as f: shutil.copyfileobj(profile_picture.file, f)
        cu.profile_picture = f"/static/uploads/avatars/{fn}"
    db.commit(); db.refresh(cu)
    return UserOut(**fmt(cu, cu))

@router.post("/{username}/follow")
async def follow(username: str, db: Session=Depends(get_db), cu: User=Depends(get_current_user)):
    target = db.query(User).filter(User.username == username.lower()).first()
    if not target: raise HTTPException(404,"Wizard not found")
    if target.id == cu.id: raise HTTPException(400,"Cannot follow yourself")
    ex = db.query(Follow).filter(Follow.follower_id==cu.id, Follow.following_id==target.id).first()
    if ex:
        db.delete(ex); db.commit()
        return {"message":"Unfollowed","is_following":False,"followers_count":len(target.followers)-1}
    follow = Follow(follower_id=cu.id, following_id=target.id)
    db.add(follow); db.commit(); db.refresh(target)
    return {"message":"Following","is_following":True,"followers_count":len(target.followers)}

@router.get("/{username}/followers", response_model=List[UserPublic])
async def followers(username: str, db: Session=Depends(get_db), cu=Depends(get_optional_user)):
    user = db.query(User).filter(User.username==username.lower()).first()
    if not user: raise HTTPException(404,"Wizard not found")
    return [pub(f, cu) for f in user.followers]

@router.get("/{username}/following", response_model=List[UserPublic])
async def following(username: str, db: Session=Depends(get_db), cu=Depends(get_optional_user)):
    user = db.query(User).filter(User.username==username.lower()).first()
    if not user: raise HTTPException(404,"Wizard not found")
    return [pub(f, cu) for f in user.following]