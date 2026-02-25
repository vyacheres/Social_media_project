from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# URL для подключения к базе данных SQLite.
# В данном случае, база данных будет храниться в файле social_media.db
SQLALCHEMY_DATABASE_URL = "sqlite:///./social_media.db"

# Создаем движок SQLAlchemy.
# connect_args={"check_same_thread": False} необходим для SQLite при работе с FastAPI
# во избежание проблем с многопоточностью.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Создаем класс SessionLocal, который будет экземпляром сессии базы данных.
# autocommit=False гарантирует, что изменения не будут автоматически зафиксированы.
# autoflush=False отключает автоматическую очистку сессии.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовый класс для объявления моделей SQLAlchemy.
Base = declarative_base()


# Функция для получения сессии базы данных.
# Используется как зависимость в FastAPI маршрутах.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
