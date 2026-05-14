"""HTTP middleware."""
from starlette.middleware.base import BaseHTTPMiddleware

from auth_utils import ensure_session_csrf


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Базовые заголовки безопасности для ответов."""

    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response


class CsrfSessionMiddleware(BaseHTTPMiddleware):
    """Гарантирует наличие CSRF-токена в сессии до обработки маршрута."""

    async def dispatch(self, request, call_next):
        ensure_session_csrf(request)
        return await call_next(request)
