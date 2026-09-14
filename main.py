import logging
import os

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse

from backend.core.config import settings
from backend.core.database import engine, Base, ensure_schema
from backend.core.middleware import RequestLoggingMiddleware, RateLimitMiddleware
from backend.models import user, spell  # noqa
from backend.routers import auth, users, spells, health , duels , notification , prophet, map

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s - %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("spellbook")

# DB tables
try:
    Base.metadata.create_all(bind=engine)
    ensure_schema()
    logger.info("Database tables ready")
except Exception as exc:
    logger.warning("Could not create tables: %s", exc)

# Upload dirs
for sub in ("avatars", "spells"):
    os.makedirs(os.path.join(settings.UPLOAD_DIR, sub), exist_ok=True)

# App
app = FastAPI(
    title="Spellbook",
    description="Harry Potter themed social network",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Middleware
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

# API routers
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(spells.router)
app.include_router(duels.router)
app.include_router(notification.router)
app.include_router(prophet.router)
app.include_router(map.router)

# Serve frontend HTML directly — no Jinja2 templating needed
@app.get("/{full_path:path}", response_class=HTMLResponse, include_in_schema=False)
async def serve_spa(request: Request, full_path: str):
    return FileResponse("frontend/templates/index.html")