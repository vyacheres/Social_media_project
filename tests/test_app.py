"""Интеграционные тесты приложения."""
import pytest

import crud
from main import app
from tests.conftest import parse_csrf


def _db():
    return app._test_session_factory()


def _add_post(title: str, content: str, author: str = "seed"):
    db = _db()
    try:
        return crud.create_post(db, title=title, content=content, author=author)
    finally:
        db.close()


def _register(client, username: str = "alice", password: str = "password12"):
    r = client.get("/register")
    assert r.status_code == 200
    token = parse_csrf(r.text)
    return client.post(
        "/register",
        data={
            "username": username,
            "password": password,
            "password2": password,
            "csrf_token": token,
        },
        follow_redirects=False,
    )


def _login(client, username: str, password: str, next_url: str = ""):
    r = client.get("/login")
    assert r.status_code == 200
    token = parse_csrf(r.text)
    return client.post(
        "/login",
        data={
            "username": username,
            "password": password,
            "csrf_token": token,
            "next": next_url,
        },
        follow_redirects=False,
    )


def test_api_posts_unauthorized(client):
    r = client.get("/api/posts")
    assert r.status_code == 401


def test_api_posts_with_session(client):
    reg = _register(client)
    assert reg.status_code == 303
    r = client.get("/api/posts")
    assert r.status_code == 200
    assert r.json() == []


def test_api_posts_with_api_key(client, monkeypatch):
    import settings as settings_mod

    monkeypatch.setattr(settings_mod.settings, "api_key", "secret-test-key")
    r = client.get("/api/posts", headers={"X-API-Key": "secret-test-key"})
    assert r.status_code == 200
    bad = client.get("/api/posts", headers={"X-API-Key": "wrong"})
    assert bad.status_code == 401


def test_search_percent_literal(client):
    """Символ % в поиске трактуется как литерал, а не wildcard LIKE."""
    _add_post("100% готов", "описание")
    _add_post("Без процента", "другой текст")

    r = client.get("/search", params={"s": "100%"})
    assert r.status_code == 200
    assert "100% готов" in r.text
    assert "Без процента" not in r.text

    r2 = client.get("/search", params={"s": "%"})
    assert r2.status_code == 200
    assert "100% готов" in r2.text
    assert "Без процента" not in r2.text


def test_comment_csrf_required(client):
    _register(client, "bob2", "password12")
    p = _add_post("t", "c", author="other")
    pid = p.id

    r = client.post(
        f"/posts/{pid}/comment",
        data={"content": "hi", "csrf_token": "wrong"},
        follow_redirects=False,
    )
    assert r.status_code == 403


def test_comment_requires_login(client):
    p = _add_post("t2", "c2", author="x")
    pid = p.id

    r = client.get("/register")
    token = parse_csrf(r.text)
    r = client.post(
        f"/posts/{pid}/comment",
        data={"content": "hi", "csrf_token": token},
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert "/login" in r.headers.get("location", "")


def test_view_increment_once_per_session(client):
    p = _add_post("v", "c", author="u")
    pid = p.id
    assert p.views == 0

    client.get(f"/posts/{pid}")
    client.get(f"/posts/{pid}")
    db = _db()
    try:
        p2 = crud.get_post(db, pid)
        assert p2.views == 1
    finally:
        db.close()


def test_create_post_redirect_without_login(client):
    r = client.get("/register")
    token = parse_csrf(r.text)
    r = client.post(
        "/posts/create",
        data={
            "title": "n",
            "content": "body",
            "csrf_token": token,
        },
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert "login" in r.headers.get("location", "")


def test_register_password_mismatch(client):
    r = client.get("/register")
    token = parse_csrf(r.text)
    resp = client.post(
        "/register",
        data={
            "username": "u1",
            "password": "password12",
            "password2": "password13",
            "csrf_token": token,
        },
    )
    assert resp.status_code == 400


def test_security_headers(client):
    r = client.get("/")
    assert r.headers.get("X-Frame-Options") == "DENY"
    assert r.headers.get("X-Content-Type-Options") == "nosniff"


def test_logged_in_comment_flow(client):
    _register(client, "carol", "password12")
    r = client.get("/posts/create")
    assert r.status_code == 200
    tok = parse_csrf(r.text)
    pr = client.post(
        "/posts/create",
        data={
            "title": "Привет",
            "content": "Текст поста",
            "csrf_token": tok,
        },
        follow_redirects=False,
    )
    assert pr.status_code == 200
    db = _db()
    try:
        posts = crud.get_posts(db)
        assert len(posts) == 1
        assert posts[0].author == "carol"
        pid = posts[0].id
    finally:
        db.close()

    page = client.get(f"/posts/{pid}")
    ctok = parse_csrf(page.text)
    cr = client.post(
        f"/posts/{pid}/comment",
        data={"content": "мой коммент", "csrf_token": ctok},
        follow_redirects=False,
    )
    assert cr.status_code == 200
    assert "мой коммент" in cr.text


def test_login_open_redirect_blocked(client):
    _register(client, "dave", "password12")
    r = client.get("/login")
    tok = parse_csrf(r.text)
    resp = client.post(
        "/login",
        data={
            "username": "dave",
            "password": "password12",
            "csrf_token": tok,
            "next": "https://evil.example/",
        },
        follow_redirects=False,
    )
    assert resp.status_code == 303
    assert resp.headers["location"] == "/"
