"""
ORM-модели SQLAlchemy для таблиц users, posts, comments.

Базовый класс ``Base`` импортируется из database, чтобы metadata.create_all
создавал все таблицы из одного реестра.

Поле Post.author / Comment.author — строка с логином (совпадает с User.username
для контента, созданного после внедрения регистрации). Старые демо-данные
могут содержать произвольные имена.
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship

from database import Base


class User(Base):
    """Зарегистрированный пользователь: логин и bcrypt-хеш пароля."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)


class Post(Base):
    """Пост в ленте: заголовок, текст, автор (строка), счётчики просмотров и лайков."""

    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    content = Column(Text, nullable=False)
    author = Column(String(50), nullable=False)
    views = Column(Integer, default=0)
    likes = Column(Integer, default=0)

    comments = relationship("Comment", back_populates="post_rel")


class Comment(Base):
    """Комментарий к посту; связь с постом через внешний ключ post_id."""

    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)
    content = Column(Text, nullable=False)
    author = Column(String(50), nullable=False)
    post_rel = relationship("Post", back_populates="comments")
