from sqlalchemy import create_engine, inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from backend.core.config import settings

# SQLite aur PostgreSQL dono ke liye kaam karega
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def ensure_schema():
    """Add nullable feature columns to databases created before this feature."""
    inspector = inspect(engine)
    dialect = engine.dialect.name
    additions = {
        "users": {
            "mischief_managed": "BOOLEAN NOT NULL DEFAULT FALSE" if dialect == "postgresql" else "BOOLEAN NOT NULL DEFAULT 0",
        },
        "spells": {
            "latitude": "FLOAT",
            "longitude": "FLOAT",
            "city": "VARCHAR(100)",
            "country": "VARCHAR(100)",
        },
    }
    with engine.begin() as connection:
        for table, columns in additions.items():
            existing = {column["name"] for column in inspect(connection).get_columns(table)}
            for column, definition in columns.items():
                if column not in existing:
                    connection.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {definition}"))

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()