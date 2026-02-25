from sqlalchemy.orm import Session
import models


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
    # Ищем посты по заголовку или содержимому
    return (
        db.query(models.Post)
        .filter(models.Post.title.contains(query) | models.Post.content.contains(query))
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
