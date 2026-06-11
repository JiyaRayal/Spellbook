from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./spellbook.db"
    SECRET_KEY: str = "my-super-secret-spellbook-key-change-this"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080
    APP_NAME: str = "Spellbook"
    DEBUG: bool = True
    UPLOAD_DIR: str = "frontend/static/uploads"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()