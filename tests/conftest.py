"""
Фикстуры pytest для приложения Social Media.

Перед импортом main задаются SECRET_KEY и DISABLE_RATE_LIMIT, чтобы
сессии подписывались и лимиты slowapi не мешали тестам.

База — SQLite в памяти с StaticPool: все соединения делят одну БД,
иначе create_all и запросы через TestClient попадали бы в разные :memory:.
"""
import os
import re

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ.setdefault("SECRET_KEY", "test-secret-key-must-be-at-least-32-chars")
os.environ.setdefault("DISABLE_RATE_LIMIT", "1")

from database import Base, get_db  # noqa: E402
from main import app  # noqa: E402


@pytest.fixture()
def client():
    """HTTP-клиент к приложению с подменённой БД на время теста."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=engine
    )
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    app._test_session_factory = TestingSessionLocal  # noqa: SLF001 — только для тестов
    with TestClient(app) as tc:
        yield tc
    app.dependency_overrides.clear()
    engine.dispose()


def parse_csrf(html: str) -> str:
    """Достаёт значение скрытого поля csrf_token из HTML (для POST в тестах)."""
    m = re.search(r'name="csrf_token"\s+value="([^"]+)"', html)
    assert m, "csrf_token not found in HTML"
    return m.group(1)
