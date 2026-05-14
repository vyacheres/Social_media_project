"""
Настройки приложения из переменных окружения.

Модуль не импортирует FastAPI/SQLAlchemy, чтобы его можно было подключать
из database.py без циклических зависимостей.

Переменные (см. также .env.example):
- SECRET_KEY — подпись cookie-сессии (в продакшене обязательно свой длинный ключ).
- API_KEY — опционально: доступ к JSON API по заголовку X-API-Key без браузерной сессии.
- DATABASE_URL — строка подключения SQLAlchemy (по умолчанию SQLite в файле).
- DISABLE_RATE_LIMIT — отключение slowapi (удобно для pytest).
"""
import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Снимок конфигурации на момент импорта модуля."""

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
