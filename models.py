from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship

from database import Base


# Определяем модель Post для таблицы "posts"
class Post(Base):
    # Указываем имя таблицы в базе данных
    __tablename__ = "posts"

    # Первичный ключ - уникальный идентификатор поста
    id = Column(Integer, primary_key=True, index=True)
    # Заголовок поста, максимум 100 символов
    title = Column(String(100), nullable=False)
    # Содержимое поста (может быть длинным текстом)
    content = Column(Text, nullable=False)
    # Имя автора поста, максимум 50 символов
    author = Column(String(50), nullable=False)
    # Количество просмотров, по умолчанию 0
    views = Column(Integer, default=0)
    # Количество лайков, по умолчанию 0
    likes = Column(Integer, default=0)

    # Связь "один-ко-многим" с моделью Comment (back_populates обеспечивает двустороннюю связь)
    comments = relationship("Comment", back_populates="post_rel")


# Определяем модель Comment для таблицы "comments"
class Comment(Base):
    # Указываем имя таблицы в базе данных
    __tablename__ = "comments"

    # Первичный ключ - уникальный идентификатор комментария
    id = Column(Integer, primary_key=True, index=True)
    # Внешний ключ, ссылающийся на id поста
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)
    # Текст комментария
    content = Column(Text, nullable=False)
    # Имя автора комментария
    author = Column(String(50), nullable=False)
    post_rel = relationship("Post", back_populates="comments")
