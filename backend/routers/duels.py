from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from typing import List
from datetime import datetime, timezone, timedelta

from backend.core.database import get_db
from backend.core.security import get_current_user, get_optional_user
from backend.models.user import User
from backend.models.spell import Spell
from backend.models.duel import Duel, DuelVote
from backend.models.notification import Notification
from backend.schemas.duel import DuelOut, DuelChallenge, DuelAccept, VoteRequest
from backend.schemas.user import UserPublic
from backend.schemas.spell import SpellOut

router = APIRouter(prefix="/api/duels", tags=["Duels"])
VOTING_PERIOD = timedelta(hours=72)

def as_utc(value):
    if value is None:
        return None
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)

# ── HELPERS ───────────────────────────────────────────
def fmt_user(u):
    return UserPublic(
        id=u.id, username=u.username,
        display_name=u.display_name or u.username,
        profile_picture=u.profile_picture,
        house=u.house, bio=u.bio,
        followers_count=len(u.followers),
        following_count=len(u.following),
        duel_wins=u.duel_wins or 0,
        duel_losses=u.duel_losses or 0,
        is_champion=u.is_champion or False
    )

def fmt_spell(s):
    if not s: return None
    return SpellOut(
        id=s.id, content=s.content, image_url=s.image_url,
        author=fmt_user(s.author), echo_of_id=s.echo_of_id,
        created_at=s.created_at, charms_count=len(s.charms),
        replies_count=len(s.replies),
        echoes_count=len(s.echoes) if s.echoes else 0
    )

def fmt_duel(duel, current_user=None):
    challenger_votes = sum(1 for v in duel.votes if v.voted_for == "challenger")
    defender_votes   = sum(1 for v in duel.votes if v.voted_for == "defender")

    my_vote = my_reason = None
    if current_user:
        my_v = next((v for v in duel.votes if v.voter_id == current_user.id), None)
        if my_v:
            my_vote   = my_v.voted_for
            my_reason = my_v.reason

    # Top reasons
    for_votes     = [v for v in duel.votes if v.voted_for == "challenger" and v.reason]
    against_votes = [v for v in duel.votes if v.voted_for == "defender"   and v.reason]
    top_for     = for_votes[0].reason     if for_votes     else None
    top_against = against_votes[0].reason if against_votes else None

    return DuelOut(
        id=duel.id,
        topic=duel.topic,
        challenger=fmt_user(duel.challenger),
        defender=fmt_user(duel.defender),
        challenger_spell=fmt_spell(duel.challenger_spell),
        defender_spell=fmt_spell(duel.defender_spell),
        challenger_stance=duel.challenger_stance or "FOR",
        defender_stance=duel.defender_stance or "AGAINST",
        status=duel.status,
        winner=fmt_user(duel.winner) if duel.winner else None,
        challenger_votes=challenger_votes,
        defender_votes=defender_votes,
        my_vote=my_vote,
        my_reason=my_reason,
        top_for_reason=top_for,
        top_against_reason=top_against,
        created_at=duel.created_at,
        ends_at=duel.ends_at
    )

def load_duel(db, duel_id):
    return db.query(Duel).options(
        joinedload(Duel.challenger).joinedload(User.followers),
        joinedload(Duel.defender).joinedload(User.followers),
        joinedload(Duel.challenger_spell).joinedload(Spell.author),
        joinedload(Duel.challenger_spell).joinedload(Spell.charms),
        joinedload(Duel.challenger_spell).joinedload(Spell.replies),
        joinedload(Duel.challenger_spell).joinedload(Spell.echoes),
        joinedload(Duel.defender_spell).joinedload(Spell.author),
        joinedload(Duel.defender_spell).joinedload(Spell.charms),
        joinedload(Duel.defender_spell).joinedload(Spell.replies),
        joinedload(Duel.defender_spell).joinedload(Spell.echoes),
        joinedload(Duel.winner),
        joinedload(Duel.votes).joinedload(DuelVote.voter),
    ).filter(Duel.id == duel_id).first()

def award_champion_badge(db, winner: User, loser: User):
    """Winner ko stats update karo aur badge do"""
    winner.duel_wins = (winner.duel_wins or 0) + 1
    loser.duel_losses = (loser.duel_losses or 0) + 1

    # 3+ wins = Champion badge
    if winner.duel_wins >= 3:
        winner.is_champion = True
    db.commit()

def check_and_complete_duels(db):
    """Complete active duels only after their persisted UTC deadline."""
    now = datetime.now(timezone.utc)
    active_duels = db.query(Duel).filter(Duel.status == "active").all()
    expired_duels = []
    for duel in active_duels:
        if duel.ends_at is None:
            continue
        deadline = as_utc(duel.ends_at)
        if now >= deadline:
            expired_duels.append(duel)

    for duel in expired_duels:
        challenger_v = sum(1 for v in duel.votes if v.voted_for == "challenger")
        defender_v   = sum(1 for v in duel.votes if v.voted_for == "defender")

        if challenger_v >= defender_v:
            duel.winner_id = duel.challenger_id
            winner = db.query(User).get(duel.challenger_id)
            loser  = db.query(User).get(duel.defender_id)
        else:
            duel.winner_id = duel.defender_id
            winner = db.query(User).get(duel.defender_id)
            loser  = db.query(User).get(duel.challenger_id)
        duel.status = "completed"

        if winner and loser:
            became_champion = award_champion_badge(
            db,
            winner,
            loser
        )
            # Winner notification
            winner_notif = Notification(
                user_id=winner.id,
                type="duel_completed",
                message=f"🏆 Tumne Duel jeeta! '{duel.topic}' — Duel Champion! 🎉",
                link_id=duel.id
            )

            # Loser notification
            loser_notif = Notification(
                user_id=loser.id,
                type="duel_completed",
                message=f"⚔️ Duel khatam hua. '{duel.topic}' — Better luck next time!",
                link_id=duel.id
            )

            db.add(winner_notif)
            db.add(loser_notif)

            # Champion badge notification
            if became_champion:
                champ_notif = Notification(
                    user_id=winner.id,
                    type="champion",
                    message="🏆✨ Badhaai ho! Tumne 3 duels jeete — ab tum DUEL CHAMPION ho!",
                    link_id=None
                )

                db.add(champ_notif)
             

         

    if expired_duels:
        db.commit()

# ── ROUTES ────────────────────────────────────────────

@router.post("/challenge/{spell_id}", response_model=DuelOut)
async def challenge(
    spell_id: int,
    data: DuelChallenge,
    db: Session = Depends(get_db),
    cu: User = Depends(get_current_user)
):
    if not data.topic or not data.topic.strip():
        raise HTTPException(400, "Debate topic required!")
    if len(data.topic) > 200:
        raise HTTPException(400, "Topic too long — max 200 chars")
    if data.challenger_stance not in ["FOR", "AGAINST"]:
        raise HTTPException(400, "Stance must be FOR or AGAINST")

    spell = db.query(Spell).filter(
        Spell.id == spell_id, Spell.is_deleted == False
    ).first()
    if not spell:
        raise HTTPException(404, "Spell not found")
    if spell.author_id != cu.id:
        raise HTTPException(400, "Sirf apni spell se challenge karo")

    defender = db.query(User).filter(
        User.username == data.defender_username.lower()
    ).first()
    if not defender:
        raise HTTPException(404, "Wizard not found")
    if defender.id == cu.id:
        raise HTTPException(400, "Khud ko challenge nahi kar sakte!")

    existing = db.query(Duel).filter(
        Duel.challenger_id == cu.id,
        Duel.defender_id   == defender.id,
        Duel.status == "pending"
    ).first()
    if existing:
        raise HTTPException(400, "Already ek pending duel hai")

    # Defender stance is always opposite
    defender_stance = "AGAINST" if data.challenger_stance == "FOR" else "FOR"

    duel = Duel(
        topic               = data.topic.strip(),
        challenger_id       = cu.id,
        defender_id         = defender.id,
        challenger_spell_id = spell_id,
        challenger_stance   = data.challenger_stance,
        defender_stance     = defender_stance,
        status              = "pending"
    )
    db.add(duel); db.commit(); db.refresh(duel)

    # notification sending to defender
    notif = Notification(
        user_id = defender.id,
        type    = "duel_challenge",
        message = f"⚔️ {cu.display_name or cu.username} ne tumhe Spell Duel ke liye challenge kiya! Topic: '{data.topic}'",
        link_id = duel.id
    )
    db.add(notif)
    db.commit()

    return fmt_duel(load_duel(db, duel.id), cu)

@router.post("/{duel_id}/accept", response_model=DuelOut)
async def accept(
    duel_id: int,
    data: DuelAccept,
    db: Session = Depends(get_db),
    cu: User = Depends(get_current_user)
):
    duel = load_duel(db, duel_id)
    if not duel: raise HTTPException(404, "Duel not found")
    if duel.defender_id != cu.id: raise HTTPException(403, "Tum defender nahi ho")
    if duel.status != "pending": raise HTTPException(400, "Duel already " + duel.status)

    spell = db.query(Spell).filter(
        Spell.id == data.defender_spell_id,
        Spell.author_id == cu.id,
        Spell.is_deleted == False
    ).first()
    if not spell: raise HTTPException(404, "Apni spell select karo")

    duel.defender_spell_id = data.defender_spell_id
    duel.status            = "active"
    duel.ends_at           = datetime.now(timezone.utc) + VOTING_PERIOD
    db.commit()

    # informing challenger that challange has been accepted
    notif = Notification(
        user_id = duel.challenger_id,
        type    = "duel_accepted",
        message = f"⚔️ {cu.display_name or cu.username} ne tumhara Duel Challenge accept kar liya! Voting shuru ho gayi!",
        link_id = duel_id
    )
    db.add(notif)
    db.commit()

    return fmt_duel(load_duel(db, duel_id), cu)

@router.post("/{duel_id}/decline")
async def decline(
    duel_id: int,
    db: Session = Depends(get_db),
    cu: User = Depends(get_current_user)
):
    duel = db.query(Duel).filter(Duel.id == duel_id).first()
    if not duel: raise HTTPException(404, "Duel not found")
    if duel.defender_id != cu.id: raise HTTPException(403, "Tum defender nahi ho")
    if duel.status != "pending": raise HTTPException(400, "Already " + duel.status)
    duel.status = "declined"; db.commit()
    return {"message": "Duel declined!"}

@router.post("/{duel_id}/vote", response_model=DuelOut)
async def vote(
    duel_id: int,
    vote_data: VoteRequest,
    db: Session = Depends(get_db),
    cu: User = Depends(get_current_user)
):
    if vote_data.voted_for not in ["challenger", "defender"]:
        raise HTTPException(400, "voted_for must be challenger or defender")

    duel = load_duel(db, duel_id)
    if not duel: raise HTTPException(404, "Duel not found")
    if duel.status != "active": raise HTTPException(400, "Duel active nahi hai")
    if cu.id in [duel.challenger_id, duel.defender_id]:
        raise HTTPException(400, "Tum duel mein ho — vote nahi kar sakte!")
    if duel.ends_at and as_utc(duel.ends_at) <= datetime.now(timezone.utc):
        check_and_complete_duels(db)
        raise HTTPException(400, "Voting period has ended")

    existing = db.query(DuelVote).filter(
        DuelVote.duel_id  == duel_id,
        DuelVote.voter_id == cu.id
    ).first()

    if existing:
        existing.voted_for = vote_data.voted_for
        existing.reason    = vote_data.reason
    else:
        v = DuelVote(
            duel_id   = duel_id,
            voter_id  = cu.id,
            voted_for = vote_data.voted_for,
            reason    = vote_data.reason
        )
        db.add(v)

    db.commit()
    check_and_complete_duels(db)
    return fmt_duel(load_duel(db, duel_id), cu)

@router.get("/my/pending", response_model=List[DuelOut])
async def my_pending(
    db: Session = Depends(get_db),
    cu: User = Depends(get_current_user)
):
    check_and_complete_duels(db)
    duels = db.query(Duel).filter(
        Duel.defender_id == cu.id,
        Duel.status      == "pending"
    ).order_by(desc(Duel.created_at)).all()
    return [fmt_duel(load_duel(db, d.id), cu) for d in duels]

@router.get("/my/pending/sent", response_model=List[DuelOut])
async def my_sent_pending(
    db: Session = Depends(get_db),
    cu: User = Depends(get_current_user)
):
    """Pending challenges sent by the current user."""
    duels = db.query(Duel).filter(
        Duel.challenger_id == cu.id,
        Duel.status == "pending"
    ).order_by(desc(Duel.created_at)).all()
    return [fmt_duel(load_duel(db, d.id), cu) for d in duels]

@router.get("/active", response_model=List[DuelOut])
async def active_duels(
    db: Session = Depends(get_db),
    cu=Depends(get_optional_user)
):
    check_and_complete_duels(db)
    duels = db.query(Duel).filter(
        Duel.status == "active"
    ).order_by(desc(Duel.created_at)).limit(20).all()
    return [fmt_duel(load_duel(db, d.id), cu) for d in duels]


@router.get("/completed", response_model=List[DuelOut])
async def completed_duels(
    db: Session = Depends(get_db),
    cu=Depends(get_optional_user)
):
    check_and_complete_duels(db)
    duels = db.query(Duel).filter(
        Duel.status == "completed"
    ).order_by(desc(Duel.created_at)).limit(20).all()
    return [fmt_duel(load_duel(db, d.id), cu) for d in duels]

@router.get("/{duel_id}", response_model=DuelOut)
async def get_duel(
    duel_id: int,
    db: Session = Depends(get_db),
    cu=Depends(get_optional_user)
):
    check_and_complete_duels(db)
    duel = load_duel(db, duel_id)
    if not duel: raise HTTPException(404, "Duel not found")
    return fmt_duel(duel, cu)

@router.get("/user/{username}/stats")
async def user_duel_stats(
    username: str,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == username.lower()).first()
    if not user: raise HTTPException(404, "Wizard not found")

    won  = db.query(Duel).filter(Duel.winner_id == user.id, Duel.status == "completed").count()
    lost = db.query(Duel).filter(
        Duel.status == "completed",
        Duel.winner_id != user.id,
        (Duel.challenger_id == user.id) | (Duel.defender_id == user.id)
    ).count()

    return {
        "username"    : user.username,
        "duel_wins"   : user.duel_wins or won,
        "duel_losses" : user.duel_losses or lost,
        "is_champion" : user.is_champion or False,
        "win_rate"    : round((won / (won + lost) * 100) if (won + lost) > 0 else 0, 1)
    }
@router.post("/{duel_id}/force-complete")
async def force_complete(
    duel_id: int,
    db: Session = Depends(get_db),
    cu: User = Depends(get_current_user)
):
    """
    Testing ke liye — duel manually complete karo.
    Sirf duel ke challenger ya defender use kar sakte hain.
    """
    duel = load_duel(db, duel_id)
    if not duel:
        raise HTTPException(404, "Duel not found")
    if cu.id not in [duel.challenger_id, duel.defender_id]:
        raise HTTPException(403, "Sirf duel participants complete kar sakte hain")
    if duel.status != "active":
        raise HTTPException(400, "Duel active nahi hai")
    if not duel.ends_at or as_utc(duel.ends_at) > datetime.now(timezone.utc):
        raise HTTPException(400, "Voting period is still active")

    duel.ends_at = datetime.now(timezone.utc)
    db.commit()
    check_and_complete_duels(db)

    return fmt_duel(load_duel(db, duel_id), cu)