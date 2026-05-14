"""
Точка входа веб-приложения «Социальная сеть» (FastAPI).

Здесь собраны маршруты HTML и JSON, подключение middleware (сессия, CSRF,
заголовки безопасности), лимиты запросов (slowapi) и раздача статики.

Важно: маршрут ``/posts/create`` объявлен выше ``/posts/{post_id}``, иначе
слово ``create`` попадёт в параметр ``post_id`` и даст ошибку валидации.
"""
import secrets
from urllib.parse import quote

# HTTP-клиент для запроса цитат у внешнего API
import httpx
from fastapi import Depends, FastAPI, Form, Header, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

import crud
from auth_utils import (
    ensure_session_csrf,
    hash_password,
    validate_csrf,
    verify_password,
)
from database import get_db
from middlewares import CsrfSessionMiddleware, SecurityHeadersMiddleware
from schemas import CommentCreate, LoginUser, PostCreate, RegisterUser
from settings import settings


def require_login(request: Request, next_path: str) -> str:
    """
    Возвращает имя пользователя из сессии или отдаёт редирект на /login?next=...

    next_path — куда вернуть пользователя после успешного входа (относительный URL).
    """
    user = request.session.get("username")
    if not user:
        raise HTTPException(
            status_code=303,
            detail="Требуется вход",
            headers={"Location": "/login?next=" + quote(next_path, safe="")},
        )
    return user


# Лимитер: ключ по IP; можно отключить переменной DISABLE_RATE_LIMIT (см. settings)
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[],
    enabled=not settings.disable_rate_limit,
)

app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Порядок middleware: внешний слой первым в цепочке запроса — см. middlewares.py
app.add_middleware(CsrfSessionMiddleware)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    same_site="lax",
    https_only=False,
)
app.add_middleware(SecurityHeadersMiddleware)

# Статика по префиксу /static
app.mount("/static", StaticFiles(directory="Static"), name="static")
# Jinja2: шаблоны в каталоге Templates; request передаётся первым аргументом TemplateResponse
templates = Jinja2Templates(directory="Templates")


def _api_authorized(request: Request, x_api_key: str | None) -> bool:
    """Доступ к JSON API: сессия с логином или корректный X-API-Key."""
    if request.session.get("username"):
        return True
    if settings.api_key and x_api_key:
        return secrets.compare_digest(x_api_key, settings.api_key)
    return False


# --- Главная: лента постов (до 100 шт. по умолчанию в crud.get_posts) ---
@app.get("/", response_class=HTMLResponse)
async def read_posts(request: Request, db: Session = Depends(get_db)):
    posts = crud.get_posts(db)
    return templates.TemplateResponse(request, "index.html", {"posts": posts})


# --- Создание поста (только авторизованный; автор подставляется с сервера) ---
@app.get("/posts/create", response_class=HTMLResponse)
async def create_post_form(request: Request):
    if not request.session.get("username"):
        return RedirectResponse(
            "/login?next=" + quote("/posts/create", safe=""),
            status_code=303,
        )
    return templates.TemplateResponse(request, "create_post.html", {})


@app.post("/posts/create", response_class=HTMLResponse)
@limiter.limit("30/minute")
async def create_post(
    request: Request,
    title: str = Form(...),
    content: str = Form(...),
    csrf_token: str = Form(...),
    db: Session = Depends(get_db),
):
    validate_csrf(request, csrf_token)
    author = require_login(request, "/posts/create")
    try:
        body = PostCreate(title=title, content=content)
    except ValidationError as e:
        err = e.errors()[0].get("msg", "Ошибка валидации")
        return templates.TemplateResponse(
            request,
            "create_post.html",
            {"error": str(err), "title": title, "content": content},
            status_code=400,
        )
    new_post = crud.create_post(
        db, title=body.title, content=body.content, author=author
    )
    comments = crud.get_comments_by_post(db, new_post.id)
    return templates.TemplateResponse(
        request, "post.html", {"post": new_post, "comments": comments}
    )


# --- Просмотр поста: счётчик views не чаще одного раза на id в рамках сессии ---
@app.get("/posts/{post_id}", response_class=HTMLResponse)
async def read_post(request: Request, post_id: int, db: Session = Depends(get_db)):
    post = crud.get_post(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Пост не найден")

    comments = crud.get_comments_by_post(db, post_id)

    viewed = request.session.get("viewed_post_ids") or []
    if post_id not in viewed:
        post.views += 1
        db.commit()
        db.refresh(post)
        viewed = [*viewed, post_id]
        if len(viewed) > 120:
            viewed = viewed[-120:]
        request.session["viewed_post_ids"] = viewed

    return templates.TemplateResponse(
        request, "post.html", {"post": post, "comments": comments}
    )


# --- Комментарий: автор из сессии, CSRF обязателен ---
@app.post("/posts/{post_id}/comment", response_class=HTMLResponse)
@limiter.limit("60/minute")
async def add_comment(
    request: Request,
    post_id: int,
    content: str = Form(...),
    csrf_token: str = Form(...),
    db: Session = Depends(get_db),
):
    validate_csrf(request, csrf_token)
    author = require_login(request, f"/posts/{post_id}")
    post = crud.get_post(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Пост не найден")
    try:
        body = CommentCreate(content=content)
    except ValidationError as e:
        err = e.errors()[0].get("msg", "Ошибка валидации")
        comments = crud.get_comments_by_post(db, post_id)
        return templates.TemplateResponse(
            request,
            "post.html",
            {
                "post": post,
                "comments": comments,
                "comment_error": str(err),
            },
            status_code=400,
        )
    crud.add_comment(db, post_id=post_id, author=author, content=body.content)
    comments = crud.get_comments_by_post(db, post_id)
    return templates.TemplateResponse(
        request, "post.html", {"post": post, "comments": comments}
    )


# --- Поиск и страница «все посты автора» (строка author в таблице posts) ---
@app.get("/search", response_class=HTMLResponse)
async def search_posts(request: Request, s: str = "", db: Session = Depends(get_db)):
    results = []
    if s.strip():
        results = crud.search_posts(db, s.strip())
    return templates.TemplateResponse(
        request, "search.html", {"posts": results, "query": s}
    )


@app.get("/users/{username}", response_class=HTMLResponse)
async def user_posts(request: Request, username: str, db: Session = Depends(get_db)):
    posts = crud.get_posts_by_user(db, username)
    return templates.TemplateResponse(
        request, "user.html", {"posts": posts, "username": username}
    )


# --- JSON API: только сессия с логином или заголовок X-API-Key (если задан API_KEY) ---
@app.get("/api/posts")
async def api_get_posts(
    request: Request,
    db: Session = Depends(get_db),
    x_api_key: str | None = Header(None, alias="X-API-Key"),
):
    if not _api_authorized(request, x_api_key):
        raise HTTPException(status_code=401, detail="Unauthorized")
    posts = crud.get_posts(db)
    return [
        {
            "id": p.id,
            "title": p.title,
            "author": p.author,
            "content": p.content,
            "views": p.views,
            "likes": p.likes,
        }
        for p in posts
    ]


@app.get("/api/posts/{post_id}")
async def api_get_post(
    request: Request,
    post_id: int,
    db: Session = Depends(get_db),
    x_api_key: str | None = Header(None, alias="X-API-Key"),
):
    if not _api_authorized(request, x_api_key):
        raise HTTPException(status_code=401, detail="Unauthorized")
    post = crud.get_post(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Пост не найден")
    return {
        "id": post.id,
        "title": post.title,
        "content": post.content,
        "author": post.author,
        "views": post.views,
        "likes": post.likes,
    }


# --- Регистрация и вход (редирект после логина защищён от open redirect) ---
@app.get("/register", response_class=HTMLResponse)
async def register_form(request: Request):
    return templates.TemplateResponse(request, "register.html", {})


@app.post("/register")
@limiter.limit("10/minute")
async def register_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    password2: str = Form(...),
    csrf_token: str = Form(...),
    db: Session = Depends(get_db),
):
    validate_csrf(request, csrf_token)
    if password != password2:
        return templates.TemplateResponse(
            request,
            "register.html",
            {"error": "Пароли не совпадают"},
            status_code=400,
        )
    try:
        data = RegisterUser(username=username, password=password)
    except ValidationError as e:
        msg = e.errors()[0].get("msg", "Ошибка валидации")
        if isinstance(msg, dict):
            msg = str(msg)
        return templates.TemplateResponse(
            request, "register.html", {"error": str(msg)}, status_code=400
        )
    if crud.get_user_by_username(db, data.username):
        return templates.TemplateResponse(
            request,
            "register.html",
            {"error": "Имя пользователя уже занято"},
            status_code=400,
        )
    crud.create_user(db, data.username, hash_password(data.password))
    request.session["username"] = data.username
    ensure_session_csrf(request)
    return RedirectResponse("/", status_code=303)


@app.get("/login", response_class=HTMLResponse)
async def login_form(
    request: Request, next_url: str | None = Query(None, alias="next")
):
    return templates.TemplateResponse(
        request, "login.html", {"next": next_url or ""}
    )


@app.post("/login")
@limiter.limit("20/minute")
async def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    csrf_token: str = Form(...),
    next: str = Form(""),
    db: Session = Depends(get_db),
):
    validate_csrf(request, csrf_token)
    try:
        creds = LoginUser(username=username, password=password)
    except ValidationError:
        return templates.TemplateResponse(
            request,
            "login.html",
            {"error": "Неверные данные", "next": next},
            status_code=400,
        )
    user = crud.get_user_by_username(db, creds.username.strip())
    if not user or not verify_password(creds.password, user.password_hash):
        return templates.TemplateResponse(
            request,
            "login.html",
            {"error": "Неверное имя или пароль", "next": next},
            status_code=400,
        )
    request.session["username"] = user.username
    ensure_session_csrf(request)
    dest = next if next.startswith("/") and not next.startswith("//") else "/"
    return RedirectResponse(dest, status_code=303)


# --- Выход: очистка сессии (имя и CSRF-токен) ---
@app.post("/logout")
async def logout(
    request: Request,
    csrf_token: str = Form(...),
):
    validate_csrf(request, csrf_token)
    request.session.clear()
    return RedirectResponse("/", status_code=303)


# --- Случайная цитата с quotable.io (сеть недоступна — показываем заглушку) ---
@app.get("/random_quote", response_class=HTMLResponse)
async def random_quote(request: Request):
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get("https://api.quotable.io/random", timeout=5.0)
            resp.raise_for_status()
            data = resp.json()
            quote_text = data.get("content", "Цитата недоступна")
            quote_author = data.get("author", "Неизвестный")
    except httpx.RequestError:
        quote_text = "Цитата недоступна"
        quote_author = "Администрация"
    return templates.TemplateResponse(
        request, "quote.html", {"quote": quote_text, "author": quote_author}
    )


if __name__ == "__main__":
    # Режим разработки: автоперезагрузка при изменении кода
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
