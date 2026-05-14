"""Пароли и CSRF."""
import secrets

import bcrypt
from fastapi import HTTPException, Request


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("ascii")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(
            password.encode("utf-8"), password_hash.encode("ascii")
        )
    except ValueError:
        return False


def ensure_session_csrf(request: Request) -> str:
    """Один токен на сессию для всех форм."""
    token = request.session.get("_csrf")
    if not token:
        token = secrets.token_urlsafe(32)
        request.session["_csrf"] = token
    return token


def validate_csrf(request: Request, token: str | None) -> None:
    expected = request.session.get("_csrf")
    if not token or not expected:
        raise HTTPException(status_code=403, detail="CSRF: отсутствует токен")
    if not secrets.compare_digest(token, expected):
        raise HTTPException(status_code=403, detail="CSRF: неверный токен")
