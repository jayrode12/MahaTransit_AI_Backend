from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application Settings loaded dynamically from .env file or environment variables.
    """

    PROJECT_NAME: str = "MahaTransit AI - Complaint Management System"
    API_V1_STR: str = "/api/v1"

    # PostgreSQL Database Connection URL (loaded from .env)
    DATABASE_URL: str = ""

    # Supabase Credentials (loaded from .env)
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    SUPABASE_BUCKET: str = "attachments"
    SUPABASE_ATTACHMENTS_BUCKET: str = "attachments"
    SUPABASE_VOICE_BUCKET: str = "voice-files"

    # CORS Origins allowed for Frontend (React + Vite)
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
