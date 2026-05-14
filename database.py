"""
Подключение к базе данных и фабрика сессий SQLAlchemy.

URL берётся из переменной окружения DATABASE_URL (см. settings и .env.example).
По умолчанию — файл SQLite ``social_media.db`` в корне проекта.

``get_db`` подключается в FastAPI как Depends: сессия создаётся на запрос
и закрывается в блоке finally.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from settings import settings

SQLALCHEMY_DATABASE_URL = settings.database_url

# Для SQLite в связке с FastAPI отключаем проверку «один поток — одно соединение»
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Зависимость FastAPI: выдаёт сессию БД и гарантирует её закрытие."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
