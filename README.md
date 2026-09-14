# ⚡ Spellbook — The Wizard's Social Network

> *A Harry Potter-themed Twitter clone built with FastAPI, PostgreSQL, and vanilla JavaScript*

![Python](https://img.shields.io/badge/Python-3.9+-blue) ![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green) ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14+-blue) ![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3.x-cyan)

---

## 📸 Features

| Feature | HP Theme | Status |
|---|---|---|
| JWT Authentication | Owl-post login | ✅ |
| User profiles | Wizard registry | ✅ |
| Hogwarts house system | Sorting Hat | ✅ |
| Create posts | Cast Spells | ✅ |
| Image uploads | Enchanted photos | ✅ |
| Feed from followed users | The Great Hall | ✅ |
| Explore all posts | The Wizarding World | ✅ |
| Like posts | Charm | ✅ |
| Comment on posts | Reply | ✅ |
| Repost | Echo Spell | ✅ |
| Follow / Unfollow | Order of the Phoenix | ✅ |
| Delete posts | Evanesco | ✅ |
| Search users | Accio Wizard | ✅ |
| Edit profile + avatar | Polyjuice Potion | ✅ |

---

## 🛠️ Tech Stack

- **Backend**: Python 3.9+ with FastAPI
- **Database**: PostgreSQL via SQLAlchemy ORM
- **Auth**: JWT tokens (python-jose + passlib/bcrypt)
- **Frontend**: Vanilla HTML/JS + Tailwind CSS (CDN) + Jinja2
- **Migrations**: Alembic
- **File uploads**: Python multipart + aiofiles

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- PostgreSQL 14+ running locally
- Git

### 1. Clone / set up the project

```bash
git clone <your-repo> spellbook
cd spellbook
```

### 2. Create the database

```sql
-- In psql or pgAdmin:
CREATE DATABASE spellbook_db;
```

### 3. Configure environment

```bash
cp .env.example .env
```

Edit `.env`:
```env
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/spellbook_db
SECRET_KEY=some-very-long-random-secret-string-here
```

Generate a strong secret key:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 4. Run (Mac/Linux)

```bash
chmod +x run.sh
./run.sh
```

### 4. Run (Windows)

```bat
run.bat
```

### 4. Run (Manual)

```bash
python -m venv venv
source venv/bin/activate     # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 5. Seed sample data (optional)

```bash
python seed.py
```

This creates 7 Hogwarts characters with posts, follows, likes, and replies.

### 6. Open in browser

```
http://localhost:8000        ← App
http://localhost:8000/docs   ← Swagger API docs
http://localhost:8000/redoc  ← ReDoc API docs
```

---

## 🗂️ Project Structure

```
spellbook/
├── main.py                    # FastAPI app, mounts routes & static files
├── requirements.txt
├── seed.py                    # Sample data seeder
├── run.sh / run.bat           # One-command startup
├── alembic.ini                # Migration config
├── alembic/
│   ├── env.py
│   └── versions/              # Migration files
├── backend/
│   ├── core/
│   │   ├── config.py          # Settings from .env
│   │   ├── database.py        # SQLAlchemy engine & session
│   │   └── security.py        # JWT, hashing, auth dependencies
│   ├── models/
│   │   ├── user.py            # User, Follow SQLAlchemy models
│   │   └── spell.py           # Spell, Charm, Reply models
│   ├── schemas/
│   │   ├── user.py            # Pydantic request/response models
│   │   └── spell.py           # Pydantic schemas for spells
│   └── routers/
│       ├── auth.py            # /api/auth — signup, login
│       ├── users.py           # /api/users — profiles, follow
│       └── spells.py          # /api/spells — CRUD, feed, charms
└── frontend/
    ├── templates/
    │   └── index.html         # Single-page app (SPA)
    └── static/
        └── uploads/           # User-uploaded images (auto-created)
```

---

## 📡 API Endpoints

### Auth
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/auth/signup` | Register a new wizard |
| POST | `/api/auth/login` | Login and get JWT token |
| GET | `/api/auth/me` | Get current user |

### Users
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/users/{username}` | Get user profile |
| PUT | `/api/users/me/update` | Update profile + avatar |
| POST | `/api/users/{username}/follow` | Follow/unfollow toggle |
| GET | `/api/users/{username}/followers` | List followers |
| GET | `/api/users/{username}/following` | List following |
| GET | `/api/users/search/wizards?q=` | Search users |

### Spells (Posts)
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/spells/cast` | Create a spell (with optional image) |
| GET | `/api/spells/feed` | Feed from followed users |
| GET | `/api/spells/explore` | All spells chronologically |
| GET | `/api/spells/{id}` | Get single spell |
| DELETE | `/api/spells/{id}` | Vanish your spell |
| POST | `/api/spells/{id}/charm` | Toggle charm (like) |
| POST | `/api/spells/{id}/reply` | Add a reply |
| GET | `/api/spells/{id}/replies` | Get all replies |
| GET | `/api/spells/user/{username}` | Get a user's spells |

---

## 🗃️ Database Migrations (Alembic)

After making model changes:

```bash
# Generate a migration
alembic revision --autogenerate -m "describe your change"

# Apply migrations
alembic upgrade head

# Rollback one step
alembic downgrade -1
```

---

## 🔒 Security Notes

- Passwords are bcrypt-hashed (never stored in plain text)
- JWT tokens expire after 7 days (configurable in `.env`)
- File uploads are validated by extension
- SQL injection protected via SQLAlchemy ORM
- CORS configured (restrict origins in production)

---

## 🚢 Production Deployment

For deploying to a server:

1. Set `DEBUG=False` in `.env`
2. Use a strong, random `SECRET_KEY`
3. Restrict `allow_origins` in `main.py` CORS config to your domain
4. Use a production WSGI server: `gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker`
5. Put Nginx in front as a reverse proxy
6. Store uploads on S3 or similar (not local disk)
7. Use environment variables, never commit `.env`

---

## 🧪 Test Accounts (after seeding)

| Username | Password | House |
|---|---|---|
| harry_potter | expelliarmus123 | Gryffindor |
| hermione_granger | alohomora123 | Gryffindor |
| ron_weasley | wingardium123 | Gryffindor |
| draco_malfoy | serpensortia123 | Slytherin |
| luna_lovegood | revelio123 | Ravenclaw |
| neville_longbottom | mandrake123 | Gryffindor |
| cedric_diggory | accio123456 | Hufflepuff |

---

## 🪄 Extending the Project

Ideas for next features:
- **Notifications** — When someone charms/replies/follows you
- **Direct Messages** — Private owl-post between wizards
- **Trending Spells** — Sort by charm count in a time window
- **Hashtags** — #Quidditch #NEWTS #DA spell tagging
- **WebSockets** — Real-time feed updates
- **Redis caching** — Cache hot feed queries
- **Full-text search** — Search spell content with PostgreSQL FTS
- **Media compression** — Auto-resize images with Pillow

---

*Built with ⚡ and a lot of Butterbeer*
