"""Валидация входных данных (Pydantic)."""
from pydantic import BaseModel, ConfigDict, Field, field_validator


class PostCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=1, max_length=50_000)

    @field_validator("title", "content")
    @classmethod
    def not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Поле не может быть пустым или только из пробелов")
        return v.strip()


class CommentCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    content: str = Field(min_length=1, max_length=10_000)

    @field_validator("content")
    @classmethod
    def not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Комментарий не может быть пустым")
        return v.strip()


class RegisterUser(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("username")
    @classmethod
    def username_chars(cls, v: str) -> str:
        s = v.strip()
        if not all(ch.isalnum() or ch == "_" for ch in s):
            raise ValueError("Имя: только буквы, цифры и подчёркивание")
        return s

    @field_validator("password")
    @classmethod
    def password_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Пароль не может быть пустым")
        return v


class LoginUser(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1, max_length=128)
