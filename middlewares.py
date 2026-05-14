"""
ASGI-middleware на базе Starlette BaseHTTPMiddleware.

- SecurityHeadersMiddleware — добавляет «безопасные» HTTP-заголовки к ответу.
- CsrfSessionMiddleware — до обработки маршрута вызывает ensure_session_csrf,
  чтобы в сессии всегда был токен для шаблонов (после SessionMiddleware).
"""
from starlette.middleware.base import BaseHTTPMiddleware

from auth_utils import ensure_session_csrf


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Снижает риск MIME-sniffing, clickjacking и утечки полного URL в Referer."""

    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response


class CsrfSessionMiddleware(BaseHTTPMiddleware):
    """Готовит CSRF-токен в сессии до вызова обработчиков маршрутов."""

    async def dispatch(self, request, call_next):
        ensure_session_csrf(request)
        return await call_next(request)
