from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, Request
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from typing import Optional, List
from datetime import datetime, timezone
import os, uuid, shutil
from backend.core.database import get_db
from backend.core.security import get_current_user, get_optional_user
from backend.models.user import User
from backend.models.spell import Spell, Charm, Reply
from backend.schemas.spell import SpellOut, ReplyOut, ReplyCreate, FeedResponse
from backend.schemas.user import UserPublic
from backend.core.config import settings
from backend.core.location import locate_request

router = APIRouter(prefix="/api/spells", tags=["Spells"])

def _pub(author, cu=None):
    return UserPublic(
        id=author.id, username=author.username,
        display_name=author.display_name or author.username,
        profile_picture=author.profile_picture, house=author.house, bio=author.bio,
        followers_count=len(author.followers), following_count=len(author.following),
        is_following=cu in author.followers if cu else False
    )

def _fmt(spell, cu=None):
    is_charmed = any(c.user_id == cu.id for c in spell.charms) if cu else False
    is_echoed  = any(e.author_id == cu.id for e in spell.echoes) if cu and spell.echoes else False
    echo_of = None
    if spell.echo_of:
        o = spell.echo_of
        echo_of = SpellOut(
            id=o.id, content=o.content, image_url=o.image_url,
            author=_pub(o.author), echo_of_id=o.echo_of_id,
            created_at=o.created_at, charms_count=len(o.charms),
            replies_count=len(o.replies),
            echoes_count=len(o.echoes) if o.echoes else 0
        )
    return SpellOut(
        id=spell.id, content=spell.content, image_url=spell.image_url,
        author=_pub(spell.author, cu), echo_of_id=spell.echo_of_id, echo_of=echo_of,
        created_at=spell.created_at, charms_count=len(spell.charms),
        replies_count=len(spell.replies),
        echoes_count=len(spell.echoes) if spell.echoes else 0,
        is_charmed=is_charmed, is_echoed=is_echoed
    )

def _q(db):
    return db.query(Spell).options(
        joinedload(Spell.author).joinedload(User.followers),
        joinedload(Spell.charms),
        joinedload(Spell.replies),
        joinedload(Spell.echoes),
        joinedload(Spell.echo_of).joinedload(Spell.author),
        joinedload(Spell.echo_of).joinedload(Spell.charms),
        joinedload(Spell.echo_of).joinedload(Spell.replies),
    ).filter(Spell.is_deleted == False)

# ── HOUSE SCORING SYSTEM ──────────────────────────────
def calculate_score(spell, current_user):
    score = 0

    # 1. House bonus — sabse important factor
    if (current_user.house and
        spell.author.house and
        spell.author.house == current_user.house):
        score += 100  # pehle 50 tha, ab 100

    # 2. Following bonus
    following_ids = [u.id for u in current_user.following]
    if spell.author_id in following_ids:
        score += 40  # pehle 30 tha

    # 3. Engagement — charms aur replies
    score += min(len(spell.charms) * 2, 20)   # max 20 (pehle 40 tha)
    score += min(len(spell.replies) * 2, 10)  # max 10 (pehle 30 tha)

    # 4. Recency — ab bahut kam weight
    now = datetime.now(timezone.utc)
    created = spell.created_at
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    age_hours = (now - created).total_seconds() / 3600

    if age_hours < 1:
        score += 3   # pehle 10 tha
    elif age_hours < 24:
        score += 1   # pehle 5 tha

    return score

    # 1. House bonus
    if (current_user.house and
        spell.author.house and
        spell.author.house == current_user.house):
        score += 50

    # 2. Following bonus
    following_ids = [u.id for u in current_user.following]
    if spell.author_id in following_ids:
        score += 30

    # 3. Engagement bonus
    score += min(len(spell.charms) * 2, 40)   # max 40
    score += min(len(spell.replies) * 3, 30)  # max 30

    # 4. Recency bonus
    now = datetime.now(timezone.utc)
    # Make spell.created_at timezone aware
    created = spell.created_at
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    age_hours = (now - created).total_seconds() / 3600

    if age_hours < 1:
        score += 10
    elif age_hours < 24:
        score += 5

    return score

@router.post("/cast", response_model=SpellOut, status_code=201)
async def cast(
    request: Request,
    content: str = Form(...),
    echo_of_id: Optional[int] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    cu: User = Depends(get_current_user)
):
    if len(content) > 280:
        raise HTTPException(400, "Max 280 characters")
    img_url = None
    if image and image.filename:
        d = os.path.join(settings.UPLOAD_DIR, "spells")
        os.makedirs(d, exist_ok=True)
        ext = image.filename.split(".")[-1].lower()
        if ext not in ["jpg","jpeg","png","gif","webp"]:
            raise HTTPException(400, "Invalid image format")
        fn = f"{uuid.uuid4()}.{ext}"
        with open(os.path.join(d, fn), "wb") as f:
            shutil.copyfileobj(image.file, f)
        img_url = f"/static/uploads/spells/{fn}"
    location = None if cu.mischief_managed else await locate_request(request)
    s = Spell(
        content=content.strip(), image_url=img_url, author_id=cu.id,
        echo_of_id=echo_of_id, **(location or {})
    )
    db.add(s); db.commit(); db.refresh(s)
    return _fmt(_q(db).filter(Spell.id == s.id).first(), cu)

# ── PERSONALIZED FEED ─────────────────────────────────
@router.get("/feed", response_model=FeedResponse)
async def feed(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
    cu: User = Depends(get_current_user)
):
    # sabke spells fetch karo — sab dikhenge lekin scoring se order decide hoga
    all_spells = (
        _q(db)
        .order_by(desc(Spell.created_at))
        .limit(200)
        .all()
    )

    # Score karo
    scored = []
    for spell in all_spells:
        score = calculate_score(spell, cu)
        scored.append((score, spell.created_at, spell))

    # score se sort karo, same score mein time se
    scored.sort(key=lambda x: (x[0], x[1]), reverse=True)

    # Paginate
    total = len(scored)
    start = (page - 1) * per_page
    end   = start + per_page
    page_spells = [spell for score, time, spell in scored[start:end]]

    return FeedResponse(
        spells=[_fmt(s, cu) for s in page_spells],
        total=total, page=page, per_page=per_page
    )

@router.get("/explore", response_model=FeedResponse)
async def explore(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
    cu=Depends(get_optional_user)
):
    total = _q(db).count()
    spells = (
        _q(db)
        .order_by(desc(Spell.created_at))
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    return FeedResponse(
        spells=[_fmt(s, cu) for s in spells],
        total=total, page=page, per_page=per_page
    )

@router.get("/search/spells", response_model=FeedResponse)
async def search_spells(
    q: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
    cu=Depends(get_optional_user)
):
    total = _q(db).filter(Spell.content.ilike(f"%{q}%")).count()
    spells = (
        _q(db)
        .filter(Spell.content.ilike(f"%{q}%"))
        .order_by(desc(Spell.created_at))
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    return FeedResponse(
        spells=[_fmt(s, cu) for s in spells],
        total=total, page=page, per_page=per_page
    )

@router.get("/user/{username}", response_model=FeedResponse)
async def user_spells(
    username: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
    cu=Depends(get_optional_user)
):
    user = db.query(User).filter(User.username == username.lower()).first()
    if not user:
        raise HTTPException(404, "Wizard not found")
    total = _q(db).filter(Spell.author_id == user.id).count()
    spells = (
        _q(db)
        .filter(Spell.author_id == user.id)
        .order_by(desc(Spell.created_at))
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    return FeedResponse(
        spells=[_fmt(s, cu) for s in spells],
        total=total, page=page, per_page=per_page
    )

@router.get("/{spell_id}", response_model=SpellOut)
async def get_spell(
    spell_id: int,
    db: Session = Depends(get_db),
    cu=Depends(get_optional_user)
):
    s = _q(db).filter(Spell.id == spell_id).first()
    if not s:
        raise HTTPException(404, "Spell not found")
    return _fmt(s, cu)

@router.delete("/{spell_id}")
async def vanish(
    spell_id: int,
    db: Session = Depends(get_db),
    cu: User = Depends(get_current_user)
):
    s = db.query(Spell).filter(Spell.id == spell_id).first()
    if not s:
        raise HTTPException(404, "Spell not found")
    if s.author_id != cu.id:
        raise HTTPException(403, "Not your spell")
    s.is_deleted = True; db.commit()
    return {"message": "Evanesco!"}

@router.post("/{spell_id}/charm")
async def charm(
    spell_id: int,
    db: Session = Depends(get_db),
    cu: User = Depends(get_current_user)
):
    s = db.query(Spell).filter(Spell.id == spell_id, Spell.is_deleted == False).first()
    if not s:
        raise HTTPException(404, "Spell not found")
    ex = db.query(Charm).filter(Charm.user_id == cu.id, Charm.spell_id == spell_id).first()
    if ex:
        db.delete(ex); db.commit()
        return {"is_charmed": False, "charms_count": db.query(Charm).filter(Charm.spell_id == spell_id).count()}
    db.add(Charm(user_id=cu.id, spell_id=spell_id)); db.commit()
    return {"is_charmed": True,  "charms_count": db.query(Charm).filter(Charm.spell_id == spell_id).count()}

@router.post("/{spell_id}/reply", response_model=ReplyOut, status_code=201)
async def reply(
    spell_id: int,
    data: ReplyCreate,
    db: Session = Depends(get_db),
    cu: User = Depends(get_current_user)
):
    s = db.query(Spell).filter(Spell.id == spell_id, Spell.is_deleted == False).first()
    if not s:
        raise HTTPException(404, "Spell not found")
    r = Reply(content=data.content, author_id=cu.id, spell_id=spell_id)
    db.add(r); db.commit(); db.refresh(r)
    return ReplyOut(
        id=r.id, content=r.content, spell_id=spell_id, created_at=r.created_at,
        author=UserPublic(
            id=cu.id, username=cu.username,
            display_name=cu.display_name or cu.username,
            profile_picture=cu.profile_picture, house=cu.house, bio=cu.bio,
            followers_count=0, following_count=0
        )
    )

@router.get("/{spell_id}/replies", response_model=List[ReplyOut])
async def get_replies(spell_id: int, db: Session = Depends(get_db)):
    replies = (
        db.query(Reply)
        .options(joinedload(Reply.author))
        .filter(Reply.spell_id == spell_id)
        .order_by(desc(Reply.created_at))
        .all()
    )
    return [
        ReplyOut(
            id=r.id, content=r.content,
            spell_id=r.spell_id, created_at=r.created_at,
            author=UserPublic(
                id=r.author.id, username=r.author.username,
                display_name=r.author.display_name or r.author.username,
                profile_picture=r.author.profile_picture,
                house=r.author.house, bio=r.author.bio,
                followers_count=0, following_count=0
            )
        ) for r in replies
    ]