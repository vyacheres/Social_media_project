"""
Операции чтения/записи в базе данных (слой CRUD).

Здесь нет HTTP-логики: только SQLAlchemy Session и модели из ``models``.
Поиск постов использует LIKE с ESCAPE, чтобы символы % и _ в запросе
не работали как шаблоны SQL.
"""
from sqlalchemy import or_
from sqlalchemy.orm import Session

import models


def escape_like_pattern(query: str) -> str:
    """Экранирует спецсимволы LIKE: сначала ``\\``, затем ``%`` и ``_``."""
    return query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def get_user_by_username(db: Session, username: str):
    """Возвращает запись пользователя по уникальному логину или None."""
    return (
        db.query(models.User)
        .filter(models.User.username == username)
        .first()
    )


def create_user(db: Session, username: str, password_hash: str):
    """Создаёт пользователя (хеш пароля должен быть уже посчитан, см. auth_utils)."""
    db_user = models.User(username=username, password_hash=password_hash)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_post(db: Session, post_id: int):
    """Один пост по первичному ключу."""
    return db.query(models.Post).filter(models.Post.id == post_id).first()


def get_posts(db: Session, skip: int = 0, limit: int = 100):
    """Список постов с пагинацией (offset/limit)."""
    return db.query(models.Post).offset(skip).limit(limit).all()


def get_posts_by_user(db: Session, author: str):
    """Все посты, у которых поле author совпадает со строкой (логин из сессии при создании)."""
    return db.query(models.Post).filter(models.Post.author == author).all()


def create_post(db: Session, title: str, content: str, author: str):
    """Создаёт пост; author задаётся только сервером из сессии залогиненного пользователя."""
    db_post = models.Post(title=title, content=content, author=author)
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post


def search_posts(db: Session, query: str):
    """
    Поиск по подстроке в заголовке или теле поста.

    Строка запроса не интерпретируется как wildcard LIKE: ``%`` и ``_`` — обычные символы.
    """
    raw = query.strip()
    if not raw:
        return []
    pattern = f"%{escape_like_pattern(raw)}%"
    return (
        db.query(models.Post)
        .filter(
            or_(
                models.Post.title.like(pattern, escape="\\"),
                models.Post.content.like(pattern, escape="\\"),
            )
        )
        .all()
    )


def add_comment(db: Session, post_id: int, author: str, content: str):
    """Добавляет комментарий к посту (author — из сессии, не из формы)."""
    db_comment = models.Comment(post_id=post_id, author=author, content=content)
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment


def get_comments_by_post(db: Session, post_id: int):
    """Все комментарии для указанного поста."""
    return db.query(models.Comment).filter(models.Comment.post_id == post_id).all()
