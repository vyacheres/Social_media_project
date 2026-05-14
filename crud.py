from sqlalchemy import or_
from sqlalchemy.orm import Session

import models


def escape_like_pattern(query: str) -> str:
    """Экранирование % и _ для LIKE (SQLite), обратный слэш — первым."""
    return (
        query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    )


def get_user_by_username(db: Session, username: str):
    return (
        db.query(models.User)
        .filter(models.User.username == username)
        .first()
    )


def create_user(db: Session, username: str, password_hash: str):
    db_user = models.User(username=username, password_hash=password_hash)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_post(db: Session, post_id: int):
    # Возвращаем пост по идентификатору
    return db.query(models.Post).filter(models.Post.id == post_id).first()


def get_posts(db: Session, skip: int = 0, limit: int = 100):
    # Возвращаем посты, пропуская skip элементов и ограничивая limit
    return db.query(models.Post).offset(skip).limit(limit).all()


def get_posts_by_user(db: Session, author: str):
    # Возвращаем все посты определенного автора
    return db.query(models.Post).filter(models.Post.author == author).all()


def create_post(db: Session, title: str, content: str, author: str):
    # Создаем новый пост и сохраняем его в базе данных
    db_post = models.Post(title=title, content=content, author=author)
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post


def search_posts(db: Session, query: str):
    """Поиск без интерпретации % и _ как шаблонов LIKE."""
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
    # Добавляем комментарий к посту
    db_comment = models.Comment(post_id=post_id, author=author, content=content)
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment


def get_comments_by_post(db: Session, post_id: int):
    # Возвращаем все комментарии для определенного поста
    return db.query(models.Comment).filter(models.Comment.post_id == post_id).all()
