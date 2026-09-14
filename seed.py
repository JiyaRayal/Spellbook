#!/usr/bin/env python3
"""
Seed the database with sample Harry Potter characters and spells.
Run: python seed.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.core.database import SessionLocal, engine, Base
from backend.core.security import get_password_hash
from backend.models.user import User, Follow
from backend.models.spell import Spell, Charm, Reply

# Create tables
Base.metadata.create_all(bind=engine)

WIZARDS = [
    {
        "username": "harry_potter",
        "email": "harry@hogwarts.edu",
        "display_name": "Harry Potter",
        "bio": "The Boy Who Lived. Seeker for Gryffindor. Trying to survive my seventh year.",
        "house": "Gryffindor",
        "password": "expelliarmus123",
    },
    {
        "username": "hermione_granger",
        "email": "hermione@hogwarts.edu",
        "display_name": "Hermione Granger",
        "bio": "Books and cleverness. There are more important things — friendship and bravery.",
        "house": "Gryffindor",
        "password": "alohomora123",
    },
    {
        "username": "ron_weasley",
        "email": "ron@hogwarts.edu",
        "display_name": "Ron Weasley",
        "bio": "Blood traitor, apparently. But Mum's cooking is unmatched. Chess champion.",
        "house": "Gryffindor",
        "password": "wingardium123",
    },
    {
        "username": "draco_malfoy",
        "email": "draco@hogwarts.edu",
        "display_name": "Draco Malfoy",
        "bio": "My father will hear about this.",
        "house": "Slytherin",
        "password": "serpensortia123",
    },
    {
        "username": "luna_lovegood",
        "email": "luna@hogwarts.edu",
        "display_name": "Luna Lovegood",
        "bio": "Things we lose have a way of coming back to us in the end. Wrackspurts enthusiast.",
        "house": "Ravenclaw",
        "password": "revelio123",
    },
    {
        "username": "neville_longbottom",
        "email": "neville@hogwarts.edu",
        "display_name": "Neville Longbottom",
        "bio": "Herbology is my passion. Also, Gryffindor Sword wielder. Gran is proud.",
        "house": "Gryffindor",
        "password": "mandrake123",
    },
    {
        "username": "cedric_diggory",
        "email": "cedric@hogwarts.edu",
        "display_name": "Cedric Diggory",
        "bio": "Hufflepuff Triwizard Champion. Fair play and loyalty above all.",
        "house": "Hufflepuff",
        "password": "accio123456",

    },
    {
    "username": "fred_weasley",
    "email": "fred@hogwarts.edu",
    "display_name": "Fred Weasley",
    "bio": "Gryffindor prankster and co-founder of Weasleys' Wizard Wheezes. Mischief is my specialty.",
    "house": "Gryffindor",
    "password": "mischief123"
    },
    {
    "username": "george_weasley",
    "email": "george@hogwarts.edu",
    "display_name": "George Weasley",
    "bio": "Gryffindor prankster and magical inventor. Keeping Hogwarts entertained one joke at a time.",
    "house": "Gryffindor",
    "password": "wheezes123"
    },
    {
    "username": "ginny_weasley",
    "email": "ginny@hogwarts.edu",
    "display_name": "Ginny Weasley",
    "bio": "Gryffindor Quidditch player with a fierce spirit. Brave, determined, and never backing down.",
    "house": "Gryffindor",
    "password": "batbogey123"
    },
    {
    "username": "seamus_finnigan",
    "email": "seamus@hogwarts.edu",
    "display_name": "Seamus Finnigan",
    "bio": "Gryffindor student with a talent for experimental magic and spectacular explosions.",
    "house": "Gryffindor",
    "password": "boom123456"
    },
    {
    "username": "dean_thomas",
    "email": "dean@hogwarts.edu",
    "display_name": "Dean Thomas",
    "bio": "Gryffindor student and talented artist. Always ready to stand beside his friends.",
    "house": "Gryffindor",
    "password": "dean123456"
    },
    {
    "username": "parvati_patil",
    "email": "parvati@hogwarts.edu",
    "display_name": "Parvati Patil",
    "bio": "Gryffindor student with a love for Divination, magical adventures, and Hogwarts gossip.",
    "house": "Gryffindor",
    "password": "parvati123"
    },
    {
    "username": "cho_chang",
    "email": "cho@hogwarts.edu",
    "display_name": "Cho Chang",
    "bio": "Ravenclaw Seeker with a sharp mind and a passion for Quidditch.",
    "house": "Ravenclaw",
    "password": "cho123456"
    },
    {
    "username": "padma_patil",
    "email": "padma@hogwarts.edu",
    "display_name": "Padma Patil",
    "bio": "Ravenclaw prefect known for intelligence, discipline, and a thoughtful approach to magic.",
    "house": "Ravenclaw",
    "password": "padma123456"
    },
    {
    "username": "terry_boot",
    "email": "terry@hogwarts.edu",
    "display_name": "Terry Boot",
    "bio": "Ravenclaw student fascinated by magical theory, clever spells, and discovering how things work.",
    "house": "Ravenclaw",
    "password": "terry123456"
    },
    {
    "username": "millicent_bulstrode",
    "email": "millicent@hogwarts.edu",
    "display_name": "Millicent Bulstrode",
    "bio": "Slytherin student known for her tough attitude and determination.",
    "house": "Slytherin",
    "password": "millicent123"
    },
    {
    "username": "pansy_parkinson",
    "email": "pansy@hogwarts.edu",
    "display_name": "Pansy Parkinson",
    "bio": "Slytherin student with a sharp tongue, strong opinions, and unwavering house pride.",
    "house": "Slytherin",
    "password": "pansy123456"
    },
    {
    "username": "blaise_zabini",
    "email": "blaise@hogwarts.edu",
    "display_name": "Blaise Zabini",
    "bio": "Slytherin student with a cool attitude and an appreciation for ambition and cleverness.",
    "house": "Slytherin",
    "password": "blaise123456"
    },
    {
    "username": "theodore_nott",
    "email": "theodore@hogwarts.edu",
    "display_name": "Theodore Nott",
    "bio": "Quiet Slytherin student with a sharp mind and a talent for observing what others miss.",
    "house": "Slytherin",
    "password": "theodore123"
    },
    {
    "username": "ernie_macmillan",
    "email": "ernie@hogwarts.edu",
    "display_name": "Ernie Macmillan",
    "bio": "Hufflepuff prefect who values loyalty, responsibility, and doing what is right.",
    "house": "Hufflepuff",
    "password": "ernie123456"
    },
    {
    "username": "hannah_abbott",
    "email": "hannah@hogwarts.edu",
    "display_name": "Hannah Abbott",
    "bio": "Hufflepuff student who values friendship, kindness, and standing up for what matters.",
    "house": "Hufflepuff",
    "password": "hannah123456"
    },
    {
    "username": "susan_bones",
    "email": "susan@hogwarts.edu",
    "display_name": "Susan Bones",
    "bio": "Hufflepuff student with a strong sense of justice and a brave heart.",
    "house": "Hufflepuff",
    "password": "susan123456"
    },
    {
    "username": "justin_finch_fletchley",
    "email": "justin@hogwarts.edu",
    "display_name": "Justin Finch-Fletchley",
    "bio": "Hufflepuff student with a curious mind and a friendly personality.",
    "house": "Hufflepuff",
    "password": "justin123456"
    }

    
]

SPELLS_DATA = [
    ("harry_potter", "Just survived another encounter with a Dementor near the Quidditch pitch. Expecto Patronum! 🦌 My stag is getting stronger."),
    ("harry_potter", "Training session with the DA today. Dumbledore's Army never gives up. If you want to learn defensive magic, find me in the Room of Requirement. ⚡"),
    ("hermione_granger", "Finished reading 'Hogwarts: A History' for the 12th time. Still finding new details. Did you know the moving staircases were enchanted by the founders themselves? 📚"),
    ("hermione_granger", "SPEW update: House-elf rights matter. If you won't wear the badge, at least think about it. Magical creatures deserve dignity and fair wages. 🧦"),
    ("ron_weasley", "Mum sent another care package. Twelve Chocolate Frogs, Bertie Bott's Every Flavour Beans (got earwax again), and fresh treacle fudge. Best day. 🍫"),
    ("ron_weasley", "Chess club: 23 wins, 0 losses this term. Come at me, Ravenclaw. The Weasley family chess tradition lives on. ♟️"),
    ("draco_malfoy", "The Manor's peacocks are magnificent, as usual. Some of you could learn a thing or two about proper breeding. 🦚"),
    ("draco_malfoy", "Slytherin will win the House Cup this year. It's practically tradition at this point. Certain Gryffindors should prepare to be disappointed."),
    ("luna_lovegood", "Spotted three Wrackspurts floating above the Great Hall at dinner. That explains why Dumbledore seemed distracted. No one else can see them, but I know. 🌙"),
    ("luna_lovegood", "Reading the Quibbler's latest edition — Fudge is definitely being controlled by the Rotfang Conspiracy. The evidence is undeniable if you look with open eyes. ⭐"),
    ("neville_longbottom", "My Mimbulus Mimbletonia grew three new shoots overnight! Professor Sprout said it's exceptional. Gran actually sent a congratulatory owl. First time for everything! 🌱"),
    ("cedric_diggory", "Hufflepuffs — reminder that practice makes perfect. No shortcuts, no cheating. Just hard work and fair play. See you all on the pitch! 🦡"),
]

FOLLOWS = [
    ("harry_potter", "hermione_granger"),
    ("harry_potter", "ron_weasley"),
    ("harry_potter", "neville_longbottom"),
    ("harry_potter", "luna_lovegood"),
    ("hermione_granger", "harry_potter"),
    ("hermione_granger", "ron_weasley"),
    ("hermione_granger", "luna_lovegood"),
    ("ron_weasley", "harry_potter"),
    ("ron_weasley", "hermione_granger"),
    ("ron_weasley", "neville_longbottom"),
    ("luna_lovegood", "harry_potter"),
    ("luna_lovegood", "hermione_granger"),
    ("neville_longbottom", "harry_potter"),
    ("neville_longbottom", "hermione_granger"),
    ("draco_malfoy", "harry_potter"),
    ("cedric_diggory", "harry_potter"),
    ("cedric_diggory", "hermione_granger"),
]

CHARMS = [
    ("hermione_granger", 0),
    ("ron_weasley", 0),
    ("neville_longbottom", 0),
    ("luna_lovegood", 0),
    ("harry_potter", 2),
    ("hermione_granger", 2),
    ("harry_potter", 4),
    ("ron_weasley", 4),
    ("harry_potter", 8),
    ("ron_weasley", 8),
    ("hermione_granger", 8),
    ("draco_malfoy", 6),
    ("harry_potter", 10),
    ("hermione_granger", 10),
    ("ron_weasley", 10),
]

REPLIES_DATA = [
    ("hermione_granger", 0, "Harry, you need to practice more! I've been helping Ron with the counter-jinx. Come find us in the common room. 📚"),
    ("ron_weasley", 0, "Brilliant mate. Mine just looks like a... small terrier. Still proud of it though."),
    ("harry_potter", 2, "Thanks, Hermione. The DA sessions are really working! Neville's Reducto is incredible now."),
    ("ron_weasley", 2, "I'm the strategic genius of this operation, obviously. Hermione handles the books, I handle the plans."),
    ("harry_potter", 4, "RON. Send some over. Immediately. The house elves gave us mystery soup AGAIN."),
    ("hermione_granger", 4, "Ron, those beans are made by magical creatures who deserve proper working conditions! ... But yes please send some to me too."),
]

def seed():
    db = SessionLocal()
    try:
        # Add newly defined accounts without duplicating existing seed data.
        existing_usernames = {
            username for (username,) in db.query(User.username).all()
        }
        missing_wizards = [
            wizard for wizard in WIZARDS
            if wizard["username"] not in existing_usernames
        ]
        if existing_usernames:
            for wizard_data in missing_wizards:
                db.add(User(
                    username=wizard_data["username"],
                    email=wizard_data["email"],
                    display_name=wizard_data["display_name"],
                    bio=wizard_data["bio"],
                    house=wizard_data["house"],
                    hashed_password=get_password_hash(wizard_data["password"]),
                ))
            db.commit()
            print(f"✅ Added {len(missing_wizards)} missing wizard accounts")
            print("   Existing spells and relationships were left unchanged.")
            return

        print("🌱 Seeding Spellbook database with Hogwarts wizards...")

        # Create users
        users = {}
        for w in WIZARDS:
            user = User(
                username=w["username"],
                email=w["email"],
                display_name=w["display_name"],
                bio=w["bio"],
                house=w["house"],
                hashed_password=get_password_hash(w["password"]),
            )
            db.add(user)
            users[w["username"]] = user
        db.commit()
        print(f"✅ Created {len(users)} wizard accounts")

        # Refresh to get IDs
        for username in users:
            db.refresh(users[username])

        # Create spells
        spells = []
        for username, content in SPELLS_DATA:
            spell = Spell(content=content, author_id=users[username].id)
            db.add(spell)
            spells.append(spell)
        db.commit()
        print(f"✅ Cast {len(spells)} spells")

        for s in spells:
            db.refresh(s)

        # Create follows
        for follower, following in FOLLOWS:
            if follower in users and following in users:
                follow = Follow(follower_id=users[follower].id, following_id=users[following].id)
                db.add(follow)
        db.commit()
        print(f"✅ Created {len(FOLLOWS)} follow relationships")

        # Create charms (likes)
        for username, spell_idx in CHARMS:
            if spell_idx < len(spells) and username in users:
                charm = Charm(user_id=users[username].id, spell_id=spells[spell_idx].id)
                db.add(charm)
        db.commit()
        print(f"✅ Added {len(CHARMS)} charms")

        # Create replies
        for username, spell_idx, content in REPLIES_DATA:
            if spell_idx < len(spells) and username in users:
                reply = Reply(
                    content=content,
                    author_id=users[username].id,
                    spell_id=spells[spell_idx].id
                )
                db.add(reply)
        db.commit()
        print(f"✅ Added {len(REPLIES_DATA)} replies")

        print()
        print("🎉 Spellbook database seeded successfully!")
        print()
        print("📋 Test accounts (password shown):")
        for w in WIZARDS:
            print(f"   @{w['username']:<20} password: {w['password']}")
        print()
        print("🌐 Visit: http://localhost:8000")

    except Exception as e:
        db.rollback()
        print(f"❌ Seed failed: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed()
