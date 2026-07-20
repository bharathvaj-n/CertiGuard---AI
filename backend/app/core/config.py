from pydantic_settings import BaseSettings
from typing import List
import os

_db_path = os.path.join(os.path.dirname(__file__), "../db/certiguard.db").replace("\\", "/")

class Settings(BaseSettings):
    PROJECT_NAME: str = "CertiGuard AI"
    API_V1_STR: str = "/api"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite+aiosqlite:///{_db_path}")
    BACKEND_CORS_ORIGINS: List[str] = ["*"]

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
