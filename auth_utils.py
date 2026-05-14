"""
Вспомогательные функции безопасности: хеширование паролей и CSRF-токен в сессии.

Пароли никогда не хранятся в открытом виде — только результат bcrypt.
CSRF: один токен на сессию в ключе ``_csrf``; формы отправляют его скрытым полем.
"""
import secrets

import bcrypt
from fastapi import HTTPException, Request


def hash_password(password: str) -> str:
    """Возвращает bcrypt-хеш в виде ASCII-строки для колонки password_hash."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("ascii")


def verify_password(password: str, password_hash: str) -> bool:
    """Проверяет пароль против сохранённого хеша; при битых данных возвращает False."""
    try:
        return bcrypt.checkpw(
            password.encode("utf-8"), password_hash.encode("ascii")
        )
    except ValueError:
        return False


def ensure_session_csrf(request: Request) -> str:
    """
    Гарантирует наличие токена в сессии (создаёт при первом обращении).

    Вызывается из middleware на каждый запрос, чтобы шаблоны могли
    подставить значение в скрытые поля форм.
    """
    token = request.session.get("_csrf")
    if not token:
        token = secrets.token_urlsafe(32)
        request.session["_csrf"] = token
    return token


def validate_csrf(request: Request, token: str | None) -> None:
    """
    Сравнивает токен из формы с значением в сессии (constant-time).

    При несовпадении выбрасывает HTTP 403.
    """
    expected = request.session.get("_csrf")
    if not token or not expected:
        raise HTTPException(status_code=403, detail="CSRF: отсутствует токен")
    if not secrets.compare_digest(token, expected):
        raise HTTPException(status_code=403, detail="CSRF: неверный токен")
