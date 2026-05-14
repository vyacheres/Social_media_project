# Социальная сеть (Social Media Project)

Учебное веб-приложение на **FastAPI**: лента постов, комментарии, поиск, демо-страница с цитатой, JSON API. Реализованы **регистрация и вход**, защита форм **CSRF**, ограничение частоты запросов (**slowapi**), безопасные HTTP-заголовки и контроль доступа к API.

---

## Оглавление (RU)

1. [Возможности](#возможности)  
2. [Стек технологий](#стек-технологий)  
3. [Структура репозитория](#структура-репозитория)  
4. [Быстрый старт](#быстрый-старт)  
5. [Переменные окружения](#переменные-окружения)  
6. [Маршруты](#маршруты)  
7. [Безопасность](#безопасность)  
8. [База данных](#база-данных)  
9. [Тестирование](#тестирование)  
10. [Лицензия](#лицензия)  
11. [English documentation](#social-media-project-english-documentation)  

---

## Возможности

| Область | Описание |
|--------|----------|
| Лента | Главная страница со списком постов (до 100 записей за запрос в коде CRUD). |
| Пост | Просмотр поста, комментарии; счётчик просмотров увеличивается **не чаще одного раза на пост в рамках сессии браузера**. |
| Авторы | Посты и комментарии привязаны к **логину вошедшего пользователя**; подделать имя через форму нельзя. |
| Поиск | Подстрока в заголовке и тексте; символы `%` и `_` **не** работают как SQL-wildcards. |
| Профиль | Страница `/users/{username}` — все посты, у которых в БД поле `author` совпадает с именем. |
| Цитата | Страница со случайной цитатой с [Quotable API](https://api.quotable.io). |
| API | JSON-список и один пост — только с **сессией после входа** или с заголовком **`X-API-Key`**, если задан `API_KEY`. |

---

## Стек технологий

| Компонент | Роль |
|-----------|------|
| **FastAPI** | HTTP API и HTML-ответы через Jinja2. |
| **SQLAlchemy 2** | ORM, модели `User`, `Post`, `Comment`. |
| **SQLite** | Файл БД по умолчанию `social_media.db` (путь задаётся в `DATABASE_URL`). |
| **Jinja2** | Шаблоны в каталоге `Templates/`. |
| **Starlette** | Сессии, middleware, `TestClient` в тестах. |
| **bcrypt** | Хеширование паролей. |
| **slowapi** | Rate limit на чувствительных POST-маршрутах. |
| **httpx** | Асинхронный клиент для внешнего API цитат. |
| **pytest** | Интеграционные тесты в `tests/`. |

---

## Структура репозитория

```
Social_media_project/
├── main.py              # Точка входа FastAPI: маршруты, middleware, лимиты
├── database.py          # Engine, SessionLocal, get_db, declarative Base
├── models.py            # ORM: User, Post, Comment
├── crud.py              # Операции с БД + безопасный поиск LIKE
├── init_db.py           # Создание таблиц и демо-данные при пустой ленте
├── settings.py          # SECRET_KEY, DATABASE_URL, API_KEY, флаги из .env
├── schemas.py           # Pydantic-схемы для постов, комментариев, регистрации
├── auth_utils.py        # bcrypt и CSRF-токен в сессии
├── middlewares.py       # Заголовки безопасности и подготовка CSRF
├── requirements.txt
├── .env.example         # Пример переменных окружения (без секретов)
├── test_functionality.py # Ручные проверки CRUD в консоли
├── simple_test.py       # Проверка файла social_media.db без сервера
├── tests/
│   ├── conftest.py      # Фикстура клиента и in-memory SQLite (StaticPool)
│   └── test_app.py      # Интеграционные сценарии (см. таблицу ниже)
├── Static/
│   └── style.css
└── Templates/
    ├── index.html, post.html, search.html, user.html, quote.html
    ├── login.html, register.html, create_post.html
    └── partials/        # nav.html, csrf_field.html
```

---

## Быстрый старт

**Требования:** Python 3.10+ (рекомендуется 3.11+), `pip`.

```bash
cd Social_media_project
pip install -r requirements.txt
copy .env.example .env   # Windows; на Linux/macOS: cp .env.example .env
# Отредактируйте .env: задайте свой SECRET_KEY перед публичным деплоем.
python init_db.py
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Откройте в браузере: **http://127.0.0.1:8000** — зарегистрируйте пользователя, затем создавайте посты и комментарии.

Альтернатива запуску через uvicorn:

```bash
python main.py
```

---

## Переменные окружения

| Переменная | Назначение |
|------------|------------|
| `SECRET_KEY` | Подпись cookie-сессии (**обязательно** сменить в продакшене, длина ≥ 32 символов). |
| `DATABASE_URL` | Строка SQLAlchemy (по умолчанию `sqlite:///./social_media.db`). |
| `API_KEY` | Если задан, JSON API доступен с заголовком `X-API-Key: <значение>` без входа в браузере. |
| `DISABLE_RATE_LIMIT` | Значения `1` / `true` / `yes` — отключить slowapi (удобно для CI и pytest). |

Подробности — в файле **`.env.example`**.

---

## Маршруты

### HTML

| Метод | URL | Назначение |
|-------|-----|------------|
| GET | `/` | Главная, список постов |
| GET | `/posts/create` | Форма нового поста (нужна сессия) |
| POST | `/posts/create` | Создание поста |
| GET | `/posts/{id}` | Пост и комментарии |
| POST | `/posts/{id}/comment` | Новый комментарий |
| GET | `/search?s=...` | Поиск |
| GET | `/users/{username}` | Посты автора |
| GET/POST | `/register`, `/login`, POST `/logout` | Учётная запись |
| GET | `/random_quote` | Случайная цитата |

> Маршрут **`/posts/create`** объявлен в коде **выше** `/posts/{post_id}`, иначе слово `create` воспринимается как числовой id и возникает ошибка валидации.

### JSON API

| Метод | URL | Доступ |
|-------|-----|--------|
| GET | `/api/posts` | Сессия с логином **или** валидный `X-API-Key` (если настроен `API_KEY`) |
| GET | `/api/posts/{id}` | То же |

Пример с ключом:

```bash
curl -H "X-API-Key: ваш_секрет" http://127.0.0.1:8000/api/posts
```

---

## Безопасность

- Пароли хранятся как **bcrypt-хеши**; в открытом виде не сохраняются.  
- **CSRF:** скрытое поле во всех POST-формах, проверка на сервере.  
- **Сессия:** подписанная cookie (`SessionMiddleware`, `SECRET_KEY`).  
- **Заголовки:** `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`.  
- **Редирект после входа:** только относительные пути вида `/...`, без `//` (защита от open redirect).  
- **Rate limiting** на регистрации, входе, создании поста и комментариях.

---

## База данных

После `python init_db.py` создаётся файл SQLite (имя из `DATABASE_URL`).

Основные таблицы:

- **`users`** — `id`, `username`, `password_hash`  
- **`posts`** — `id`, `title`, `content`, `author`, `views`, `likes`  
- **`comments`** — `id`, `post_id`, `author`, `content`  

Демо-посты в `init_db.py` используют имён авторов «Иван», «Мария» и т.д.; после регистрации новые посты получают **ваш логин** в поле `author`.

---

## Тестирование

### Pytest (основной набор)

Запуск из корня репозитория:

```bash
pytest tests/ -v
```

Фикстура **`client`** в `tests/conftest.py` подменяет `get_db` на SQLite **в памяти** с пулом `StaticPool` (одна общая БД для всех соединений в тесте), создаёт таблицы и выставляет переменные `SECRET_KEY` и `DISABLE_RATE_LIMIT` до импорта приложения.

Ниже — все автоматические тесты из **`tests/test_app.py`** (12 шт.).

| Тест | Что проверяет |
|------|----------------|
| `test_api_posts_unauthorized` | `GET /api/posts` без сессии и без `X-API-Key` возвращает **401**. |
| `test_api_posts_with_session` | После успешной регистрации (303) тот же клиент получает `GET /api/posts` **200** и пустой JSON-массив `[]`. |
| `test_api_posts_with_api_key` | При подменённом `settings.api_key` верный заголовок **`X-API-Key`** даёт **200**, неверный ключ — **401**. |
| `test_search_percent_literal` | Поиск `100%` и `%` не использует `%` как SQL-wildcard: находится пост с символом «%» в заголовке, пост без «%» в выдаче по `%` не попадает. |
| `test_comment_csrf_required` | Залогиненный пользователь при **неверном** `csrf_token` получает **403** на POST комментария. |
| `test_comment_requires_login` | Без сессии POST комментария с валидным CSRF с `/register` ведёт к **303** и `Location` содержит **`/login`**. |
| `test_view_increment_once_per_session` | Два подряд `GET` одного поста увеличивают **`views` только до 1** (дедупликация в сессии). |
| `test_create_post_redirect_without_login` | POST `/posts/create` без входа с валидным CSRF даёт **303** и редирект на страницу входа. |
| `test_register_password_mismatch` | Регистрация с разными `password` и `password2` возвращает **400**. |
| `test_security_headers` | `GET /` отдаёт **`X-Frame-Options: DENY`** и **`X-Content-Type-Options: nosniff`**. |
| `test_logged_in_comment_flow` | Сквозной сценарий: регистрация → создание поста (автор из сессии) → комментарий; текст комментария виден в HTML ответа. |
| `test_login_open_redirect_blocked` | После входа параметр `next` с абсолютным URL (`https://…`) игнорируется — редирект на **`/`**, не на внешний сайт. |

### Другие скрипты (без pytest)

| Файл | Назначение |
|------|------------|
| `test_functionality.py` | Консольный сценарий: таблицы в БД, CRUD, вывод в stdout (ручной прогон). |
| `simple_test.py` | Проверяет наличие файла `social_media.db` и таблиц `posts`, `comments`, `users` через `sqlite3`. |

---

## Лицензия

MIT License

---

# Social Media Project — English documentation

Educational **FastAPI** app: post feed, comments, search, a demo random-quote page, and a JSON API. Includes **registration and login**, **CSRF** protection for forms, **slowapi** rate limits, security-related HTTP headers, and gated API access.

---

## Table of contents (EN)

1. [Features](#features)  
2. [Tech stack](#tech-stack)  
3. [Repository layout](#repository-layout)  
4. [Quick start](#quick-start)  
5. [Environment variables](#environment-variables)  
6. [Routes](#routes)  
7. [Security](#security)  
8. [Database](#database)  
9. [Testing](#testing)  
10. [License](#license)  

---

## Features

| Area | Description |
|------|---------------|
| Feed | Home page lists posts (up to 100 per default CRUD call). |
| Post | Post page with comments; **view counter** increases **at most once per post per browser session**. |
| Authors | Posts and comments are tied to the **logged-in username**; the HTML form cannot spoof another author. |
| Search | Substring match in title and body; `%` and `_` are **not** treated as SQL `LIKE` wildcards. |
| Profile | `/users/{username}` lists posts whose `author` field equals that string. |
| Quote | Random quote page using [Quotable API](https://api.quotable.io). |
| API | JSON list/detail only with **session after login** or **`X-API-Key`** when `API_KEY` is configured. |

---

## Tech stack

| Piece | Role |
|-------|------|
| **FastAPI** | HTTP API and HTML via Jinja2. |
| **SQLAlchemy 2** | ORM models `User`, `Post`, `Comment`. |
| **SQLite** | Default DB file `social_media.db` (overridable via `DATABASE_URL`). |
| **Jinja2** | Templates under `Templates/`. |
| **Starlette** | Sessions, middleware, `TestClient` in tests. |
| **bcrypt** | Password hashing. |
| **slowapi** | Rate limits on sensitive POST routes. |
| **httpx** | Async client for the external quotes API. |
| **pytest** | Integration tests in `tests/`. |

---

## Repository layout

```
Social_media_project/
├── main.py              # FastAPI entry: routes, middleware, limits
├── database.py          # Engine, SessionLocal, get_db, declarative Base
├── models.py            # ORM: User, Post, Comment
├── crud.py              # DB helpers + safe LIKE search
├── init_db.py           # create_all + demo seed when posts table is empty
├── settings.py          # SECRET_KEY, DATABASE_URL, API_KEY, flags from .env
├── schemas.py           # Pydantic schemas for posts, comments, registration
├── auth_utils.py        # bcrypt + CSRF token in session
├── middlewares.py       # Security headers + CSRF priming middleware
├── requirements.txt
├── .env.example
├── test_functionality.py # Manual console checks for CRUD
├── simple_test.py       # Checks social_media.db file and tables
├── tests/
│   ├── conftest.py      # TestClient + in-memory SQLite (StaticPool)
│   └── test_app.py      # Integration scenarios (see table below)
├── Static/
│   └── style.css
└── Templates/
    ├── index.html, post.html, search.html, user.html, quote.html
    ├── login.html, register.html, create_post.html
    └── partials/        # nav.html, csrf_field.html
```

---

## Quick start

**Requirements:** Python 3.10+ (3.11+ recommended), `pip`.

```bash
cd Social_media_project
pip install -r requirements.txt
cp .env.example .env   # Windows: copy .env.example .env
# Edit .env: set a strong SECRET_KEY before any public deployment.
python init_db.py
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Open **http://127.0.0.1:8000**, register, then create posts and comments.

Alternative:

```bash
python main.py
```

---

## Environment variables

| Variable | Purpose |
|----------|---------|
| `SECRET_KEY` | Signs the session cookie (**change in production**, length ≥ 32). |
| `DATABASE_URL` | SQLAlchemy URL (default `sqlite:///./social_media.db`). |
| `API_KEY` | When set, JSON API accepts `X-API-Key: <value>` without a browser session. |
| `DISABLE_RATE_LIMIT` | `1` / `true` / `yes` disables slowapi (handy for CI/pytest). |

See **`.env.example`** for details.

---

## Routes

### HTML

| Method | URL | Purpose |
|--------|-----|---------|
| GET | `/` | Home, post list |
| GET | `/posts/create` | New post form (session required) |
| POST | `/posts/create` | Create post |
| GET | `/posts/{id}` | Post + comments |
| POST | `/posts/{id}/comment` | New comment |
| GET | `/search?s=...` | Search |
| GET | `/users/{username}` | Posts by author string |
| GET/POST | `/register`, `/login`, POST `/logout` | Account |
| GET | `/random_quote` | Random quote |

> **`/posts/create` must be registered before** `/posts/{post_id}`; otherwise `create` is parsed as an integer path param and validation fails.

### JSON API

| Method | URL | Access |
|--------|-----|--------|
| GET | `/api/posts` | Logged-in session **or** valid `X-API-Key` (if `API_KEY` is set) |
| GET | `/api/posts/{id}` | Same |

Example:

```bash
curl -H "X-API-Key: your_secret" http://127.0.0.1:8000/api/posts
```

---

## Security

- Passwords stored as **bcrypt hashes** only.  
- **CSRF** hidden field on mutating forms, validated server-side.  
- **Session:** signed cookie (`SessionMiddleware`, `SECRET_KEY`).  
- **Headers:** `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`.  
- **Post-login redirect:** only relative paths like `/...`, rejecting `//...` (open-redirect mitigation).  
- **Rate limits** on register, login, post create, and comment create.

---

## Database

After `python init_db.py`, SQLite is created (filename from `DATABASE_URL`).

Main tables:

- **`users`** — `id`, `username`, `password_hash`  
- **`posts`** — `id`, `title`, `content`, `author`, `views`, `likes`  
- **`comments`** — `id`, `post_id`, `author`, `content`  

Demo posts use display names like “Иван”; new posts after registration use **your username** in `author`.

---

## Testing

### Pytest (primary suite)

```bash
pytest tests/ -v
```

The **`client`** fixture in `tests/conftest.py` overrides `get_db` with an in-memory SQLite database using **`StaticPool`** (shared DB across connections), creates schema, and sets `SECRET_KEY` / `DISABLE_RATE_LIMIT` before importing the app.

All automated tests live in **`tests/test_app.py`** (12 tests).

| Test | What it covers |
|------|----------------|
| `test_api_posts_unauthorized` | `GET /api/posts` with no session and no `X-API-Key` returns **401**. |
| `test_api_posts_with_session` | After successful registration (303), the same client gets `GET /api/posts` **200** and JSON `[]`. |
| `test_api_posts_with_api_key` | With `settings.api_key` monkeypatched, a correct **`X-API-Key`** yields **200**, a wrong key **401**. |
| `test_search_percent_literal` | Queries `100%` and `%` treat `%` as a literal character (no wildcard inflation); posts without `%` are excluded from the `%` result as expected. |
| `test_comment_csrf_required` | Logged-in user posting a comment with a **wrong** `csrf_token` gets **403**. |
| `test_comment_requires_login` | Without a session, POST comment with CSRF from `/register` returns **303** and `Location` contains **`/login`**. |
| `test_view_increment_once_per_session` | Two `GET`s for the same post leave **`views` at 1** (per-session dedupe). |
| `test_create_post_redirect_without_login` | `POST /posts/create` while logged out (valid CSRF) returns **303** toward login. |
| `test_register_password_mismatch` | Registration with mismatched passwords returns **400**. |
| `test_security_headers` | `GET /` returns **`X-Frame-Options: DENY`** and **`X-Content-Type-Options: nosniff`**. |
| `test_logged_in_comment_flow` | End-to-end: register → create post (author from session) → comment; comment text appears in HTML. |
| `test_login_open_redirect_blocked` | After login, `next` pointing to `https://…` is ignored — redirect is **`/`**, not an external site. |

### Other scripts (non-pytest)

| File | Purpose |
|------|---------|
| `test_functionality.py` | Console-oriented checks for tables and CRUD (stdout). |
| `simple_test.py` | Verifies `social_media.db` exists and required tables (`posts`, `comments`, `users`) via `sqlite3`. |

---

## License

MIT License
