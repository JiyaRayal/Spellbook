from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from datetime import datetime, date, timezone, timedelta
from typing import Optional
import anthropic
import json

from backend.core.database import get_db
from backend.core.config import settings
from backend.core.security import get_optional_user
from backend.models.spell import Spell, Charm
from backend.models.user import User
from backend.models.duel import Duel

router = APIRouter(prefix="/api/prophet", tags=["Daily Prophet"])

# Cache — taaki bar bar AI call na karna pade
_prophet_cache = {}

def get_today_key():
    return date.today().isoformat()

def get_top_spells(db: Session, limit: int = 10):
    """Aaj ke top spells — sabse zyada charmed"""
    today_start = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    # Aaj ke spells
    today_spells = db.query(Spell).filter(
        Spell.is_deleted == False,
        Spell.created_at >= today_start
    ).order_by(desc(Spell.created_at)).limit(50).all()

    # Agar aaj ke spells kam hain toh last 7 days ke lo
    if len(today_spells) < 5:
        week_start = datetime.now(timezone.utc) - timedelta(days=7)
        today_spells = db.query(Spell).filter(
            Spell.is_deleted == False,
            Spell.created_at >= week_start
        ).order_by(desc(Spell.created_at)).limit(50).all()

    # Charms ke hisaab se sort karo
    spells_with_charms = []
    for spell in today_spells:
        charm_count = len(spell.charms)
        spells_with_charms.append({
            "id"          : spell.id,
            "content"     : spell.content,
            "author"      : spell.author.display_name or spell.author.username,
            "house"       : spell.author.house or "Unknown",
            "charms"      : charm_count,
            "replies"     : len(spell.replies),
            "created_at"  : spell.created_at.isoformat()
        })

    spells_with_charms.sort(key=lambda x: x["charms"], reverse=True)
    return spells_with_charms[:limit]

def get_platform_stats(db: Session):
    """Aaj ke platform stats"""
    today_start = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    week_start = datetime.now(timezone.utc) - timedelta(days=7)

    total_spells = db.query(Spell).filter(
        Spell.is_deleted == False,
        Spell.created_at >= week_start
    ).count()

    total_charms = db.query(Charm).filter(
        Charm.created_at >= week_start
    ).count()

    total_wizards = db.query(User).filter(
        User.is_active == True
    ).count()

    active_duels = db.query(Duel).filter(
        Duel.status == "active"
    ).count()

    completed_duels = db.query(Duel).filter(
        Duel.status == "completed"
    ).count()

    # House activity
    house_counts = {}
    spells = db.query(Spell).filter(
        Spell.is_deleted == False,
        Spell.created_at >= week_start
    ).all()

    for spell in spells:
        house = spell.author.house or "Unknown"
        house_counts[house] = house_counts.get(house, 0) + 1

    most_active_house = max(house_counts, key=house_counts.get) if house_counts else "Unknown"

    return {
        "total_spells"      : total_spells,
        "total_charms"      : total_charms,
        "total_wizards"     : total_wizards,
        "active_duels"      : active_duels,
        "completed_duels"   : completed_duels,
        "most_active_house" : most_active_house,
        "house_counts"      : house_counts
    }

def get_duel_highlights(db: Session):
    """Recent duel highlights"""
    recent_duels = db.query(Duel).filter(
        Duel.status.in_(["active", "completed"])
    ).order_by(desc(Duel.created_at)).limit(3).all()

    highlights = []
    for duel in recent_duels:
        challenger_votes = sum(1 for v in duel.votes if v.voted_for == "challenger")
        defender_votes   = sum(1 for v in duel.votes if v.voted_for == "defender")
        total = challenger_votes + defender_votes

        highlights.append({
            "topic"            : duel.topic,
            "challenger"       : duel.challenger.display_name or duel.challenger.username,
            "defender"         : duel.defender.display_name or duel.defender.username,
            "challenger_votes" : challenger_votes,
            "defender_votes"   : defender_votes,
            "total_votes"      : total,
            "status"           : duel.status,
            "winner"           : duel.winner.display_name if duel.winner else None
        })

    return highlights

async def generate_with_claude(
    top_spells: list,
    stats: dict,
    duel_highlights: list
) -> tuple[dict, bool]:
    """Claude se Daily Prophet generate karo"""

    if not settings.ANTHROPIC_API_KEY:
        # API key nahi hai toh mock response do
        return generate_mock_prophet(top_spells, stats, duel_highlights), False

    try:
        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

        spells_text = "\n".join([
            f"- {s['author']} ({s['house']}): \"{s['content']}\" "
            f"[{s['charms']} charms, {s['replies']} replies]"
            for s in top_spells[:8]
        ])

        duel_text = "\n".join([
            f"- Topic: \"{d['topic']}\" | "
            f"{d['challenger']} vs {d['defender']} | "
            f"Votes: {d['challenger_votes']} vs {d['defender_votes']}"
            f"{' | Winner: ' + d['winner'] if d['winner'] else ''}"
            for d in duel_highlights
        ]) if duel_highlights else "No duels today"

        prompt = f"""You are the editor of The Daily Prophet — the magical newspaper 
from the Harry Potter wizarding world. 

Based on today's activity on Spellbook (a wizard social network), 
write today's newspaper edition. Be creative, dramatic, and use 
Harry Potter style language. Keep it fun and engaging.

TODAY'S TOP SPELLS (posts) on Spellbook:
{spells_text}

SPELL DUELS (debates):
{duel_text}

PLATFORM STATS:
- Total Spells Cast: {stats['total_spells']}
- Total Charms Given: {stats['total_charms']}  
- Active Wizards: {stats['total_wizards']}
- Active Duels: {stats['active_duels']}
- Most Active House: {stats['most_active_house']}

Write a Daily Prophet newspaper with these EXACT sections.
Respond ONLY with valid JSON, no markdown, no extra text:

{{
  "headline": "Main headline of the day (dramatic, HP style)",
  "headline_summary": "2-3 sentences expanding on the headline",
  "top_story": {{
    "title": "Top story title",
    "content": "3-4 sentences about the most interesting spell/activity today"
  }},
  "duel_report": {{
    "title": "Duel section title",
    "content": "2-3 sentences about today's duels and debates"
  }},
  "house_news": {{
    "title": "House standings title",
    "content": "2-3 sentences about house activity"
  }},
  "wizarding_gossip": {{
    "title": "Gossip column title (fun and dramatic)",
    "content": "2-3 funny/dramatic sentences about today's wizard activity"
  }},
  "editor_note": "Short dramatic closing note from the editor (1-2 sentences)",
  "stats_summary": "One dramatic sentence summarizing today in numbers"
}}"""

        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )

        # Response parse karo
        response_text = message.content[0].text.strip()

        # Clean JSON
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()

        return json.loads(response_text), True

    except Exception as e:
        print(f"Claude API error: {e}")
        return generate_mock_prophet(top_spells, stats, duel_highlights), False

def generate_mock_prophet(top_spells, stats, duel_highlights):
    """Agar API key nahi hai ya error aaye toh mock newspaper"""
    top_spell = top_spells[0] if top_spells else None
    top_author = top_spell["author"] if top_spell else "A mysterious wizard"
    top_content = top_spell["content"][:80] if top_spell else "The wizarding world stirs"
    most_active = stats.get("most_active_house", "Gryffindor")

    return {
        "headline": f"SPELLBOOK BUZZING WITH MAGICAL ACTIVITY!",
        "headline_summary": f"The wizarding social network Spellbook saw remarkable activity today, with {stats['total_spells']} spells cast and {stats['total_charms']} charms distributed among {stats['total_wizards']} registered wizards.",
        "top_story": {
            "title": "TODAY'S MOST CHARMED SPELL",
            "content": f"{top_author} captured the wizarding world's attention with: \"{top_content}...\" — earning widespread praise from the magical community."
        },
        "duel_report": {
            "title": "SPELL DUELS — THE GREAT DEBATES",
            "content": f"The dueling grounds were {'active today with ' + str(stats['active_duels']) + ' ongoing debates' if stats['active_duels'] > 0 else 'quiet today'}. {'Champions have been crowned!' if stats['completed_duels'] > 0 else 'Challengers await worthy opponents.'}"
        },
        "house_news": {
            "title": f"{most_active.upper()} LEADS THE CHARGE!",
            "content": f"House {most_active} has been the most active on Spellbook today. The rivalry between houses continues to fuel passionate discussions across the platform."
        },
        "wizarding_gossip": {
            "title": "RITA SKEETER'S CORNER 🪄",
            "content": f"Sources close to this reporter reveal that the magical community has never been more engaged! With {stats['total_charms']} charms flying about, it seems love for fellow wizards is very much in the air."
        },
        "editor_note": "Stay magical, stay curious — and remember, The Daily Prophet sees all! 👁️",
        "stats_summary": f"Today's Numbers: {stats['total_spells']} spells · {stats['total_charms']} charms · {stats['active_duels']} duels · {stats['total_wizards']} wizards"
    }

# ── ROUTES ────────────────────────────────────────────

@router.get("/today")
async def get_today_prophet(
    refresh: bool = False,
    db: Session = Depends(get_db),
    cu = Depends(get_optional_user)
):
    """Aaj ka Daily Prophet"""
    today_key = get_today_key()

    # Cache check — same day pe dobara generate mat karo
    if not refresh and today_key in _prophet_cache:
        return _prophet_cache[today_key]

    # Data fetch karo
    top_spells     = get_top_spells(db)
    stats          = get_platform_stats(db)
    duel_highlights = get_duel_highlights(db)

    # Claude se generate karo
    newspaper, ai_powered = await generate_with_claude(top_spells, stats, duel_highlights)

    # Response banao
    result = {
        "date"            : datetime.now().strftime("%B %d, %Y"),
        "edition"         : f"Vol. {(date.today() - date(2024, 1, 1)).days + 1}",
        "newspaper"       : newspaper,
        "top_spells"      : top_spells[:5],
        "stats"           : stats,
        "duel_highlights" : duel_highlights,
        "generated_at"    : datetime.now().isoformat(),
        "ai_powered"      : ai_powered
    }

    # Cache mein save karo
    _prophet_cache[today_key] = result
    return result

@router.get("/refresh")
async def refresh_prophet(
    db: Session = Depends(get_db),
    cu = Depends(get_optional_user)
):
    """Force refresh — naya newspaper generate karo"""
    today_key = get_today_key()
    if today_key in _prophet_cache:
        del _prophet_cache[today_key]

    return await get_today_prophet(refresh=True, db=db, cu=cu)