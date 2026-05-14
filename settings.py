"""Переменные окружения приложения (без импорта FastAPI/SQLAlchemy)."""
import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    secret_key: str = os.getenv(
        "SECRET_KEY", "dev-only-change-in-production-min-32-chars!!"
    )
    api_key: str | None = os.getenv("API_KEY") or None
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./social_media.db")
    disable_rate_limit: bool = os.getenv("DISABLE_RATE_LIMIT", "").lower() in (
        "1",
        "true",
        "yes",
    )


settings = Settings()
