from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from backend.schemas.user import UserPublic
from backend.schemas.spell import SpellOut

class DuelOut(BaseModel):
    id                : int
    topic             : str
    challenger        : UserPublic
    defender          : UserPublic
    challenger_spell  : SpellOut
    defender_spell    : Optional[SpellOut] = None
    challenger_stance : str = "FOR"
    defender_stance   : str = "AGAINST"
    status            : str
    winner            : Optional[UserPublic] = None
    challenger_votes  : int = 0
    defender_votes    : int = 0
    my_vote           : Optional[str] = None
    my_reason         : Optional[str] = None
    top_for_reason    : Optional[str] = None
    top_against_reason: Optional[str] = None
    created_at        : datetime
    ends_at           : Optional[datetime] = None

    class Config:
        from_attributes = True

class DuelChallenge(BaseModel):
    defender_username : str
    topic             : str      # Debate topic
    challenger_stance : str = "FOR"  # FOR or AGAINST

class DuelAccept(BaseModel):
    defender_spell_id : int

class VoteRequest(BaseModel):
    voted_for : str   # "challenger" or "defender"
    reason    : Optional[str] = None  # Why voting