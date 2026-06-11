import sys
sys.path.insert(0, '.')
from backend.core.database import engine, Base
from backend.models.user import User, Follow
from backend.models.spell import Spell, Charm, Reply
from backend.models.duel import Duel, DuelVote

try:
    from backend.models.notification import Notification
    print("Notification model OK")
except:
    print("Notification model MISSING")

Base.metadata.create_all(bind=engine)
print("All tables created successfully!")