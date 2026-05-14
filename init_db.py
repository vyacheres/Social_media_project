"""
Скрипт первичного заполнения базы демонстрационными постами и комментариями.

Запуск: ``python init_db.py`` из корня проекта (после установки зависимостей).
Создаёт таблицы по metadata и добавляет данные только если таблица posts пуста.

Импорт моделей User обязателен, чтобы таблица users попала в create_all.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base, SQLALCHEMY_DATABASE_URL
from models import Post, Comment, User  # noqa: F401 — User регистрирует таблицу users

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})

Base.metadata.create_all(bind=engine)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Добавляет демо-посты и комментарии при пустой таблице posts."""
    db = SessionLocal()
    try:
        if db.query(Post).count() == 0:
            post1 = Post(
                title="Первый пост",
                content="Это содержание первого тестового поста. Здесь будет много интересной информации, которую можно прочитать и обсудить.",
                author="Иван",
            )
            post2 = Post(
                title="Второй пост о технологиях",
                content="В этом посте мы рассмотрим последние достижения в мире технологий и их влияние на нашу жизнь. От искусственного интеллекта до блокчейна – все самое интересное здесь.",
                author="Мария",
            )
            post3 = Post(
                title="Кулинарные рецепты",
                content="Сегодня делимся простыми, но очень вкусными рецептами, которые сможет приготовить каждый. Наслаждайтесь новыми вкусами и радуйте своих близких!",
                author="Иван",
            )

            db.add(post1)
            db.add(post2)
            db.add(post3)
            db.commit()
            db.refresh(post1)
            db.refresh(post2)
            db.refresh(post3)

            comment1 = Comment(
                post_id=post1.id, author="Петр", content="Отличный пост, Иван!"
            )
            comment2 = Comment(
                post_id=post1.id, author="Анна", content="Очень интересно, жду продолжения."
            )
            comment3 = Comment(
                post_id=post2.id,
                author="Алексей",
                content="Согласен, технологии меняют мир.",
            )

            db.add(comment1)
            db.add(comment2)
            db.add(comment3)
            db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
