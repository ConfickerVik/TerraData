"""Тесты аутентификации, авторизации, API-ключей, ролей и квот (Фаза 5)."""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import require_admin, require_auth
from app.models.base import Base
from app.services import auth_service
from main import app


@pytest.fixture
async def db_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def client(db_engine):
    session_factory = async_sessionmaker(db_engine, expire_on_commit=False)

    async def override_get_db():
        async with session_factory() as session:
            yield session

    # Снимаем legacy-заглушку авторизации — тестируем реальный поток auth + БД.
    app.dependency_overrides.pop(require_auth, None)
    app.dependency_overrides.pop(require_admin, None)
    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

    app.dependency_overrides.pop(get_db, None)


async def _register_and_key(client: AsyncClient, username: str) -> tuple[str, str]:
    r = await client.post("/auth/register", json={"username": username, "password": "secret123"})
    assert r.status_code == 201, r.text
    token = (
        await client.post("/auth/login", json={"username": username, "password": "secret123"})
    ).json()["access_token"]
    key = (
        await client.post(
            "/auth/api-keys",
            json={"name": "k1"},
            headers={"Authorization": f"Bearer {token}"},
        )
    ).json()["key"]
    return key, token


# --- Регистрация и вход ---


async def test_register_and_login(client):
    r = await client.post("/auth/register", json={"username": "alice", "password": "secret123"})
    assert r.status_code == 201
    body = r.json()
    assert body["username"] == "alice"
    assert body["role"] == "user"
    assert "password_hash" not in body

    r = await client.post("/auth/login", json={"username": "alice", "password": "secret123"})
    assert r.status_code == 200
    assert r.json()["access_token"]


async def test_login_wrong_password(client):
    await client.post("/auth/register", json={"username": "bob", "password": "secret123"})
    r = await client.post("/auth/login", json={"username": "bob", "password": "wrongpass"})
    assert r.status_code == 401


async def test_register_duplicate_conflict(client):
    payload = {"username": "carol", "password": "secret123"}
    assert (await client.post("/auth/register", json=payload)).status_code == 201
    assert (await client.post("/auth/register", json=payload)).status_code == 409


# --- Авторизация (JWT и API-ключ) ---


async def test_me_without_credentials_401(client):
    assert (await client.get("/auth/me")).status_code == 401


async def test_protected_router_without_credentials_401(client):
    r = await client.get("/rosreestr/info", params={"cad_num": "38:00:000000:1"})
    assert r.status_code == 401


async def test_me_with_api_key_and_jwt(client):
    key, token = await _register_and_key(client, "dave")

    r = await client.get("/auth/me", headers={"X-API-Key": key})
    assert r.status_code == 200
    assert r.json()["username"] == "dave"

    r = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["username"] == "dave"


async def test_invalid_api_key_401(client):
    r = await client.get("/auth/me", headers={"X-API-Key": "not-a-real-key"})
    assert r.status_code == 401


# --- Жизненный цикл API-ключа ---


async def test_api_key_lifecycle(client):
    key, token = await _register_and_key(client, "eve")
    headers = {"X-API-Key": key}
    assert (await client.get("/auth/me", headers=headers)).status_code == 200

    keys = (await client.get("/auth/api-keys", headers={"Authorization": f"Bearer {token}"})).json()
    assert len(keys) == 1
    key_id = keys[0]["id"]
    # Маскированный вывод: полный ключ повторно не возвращается.
    assert "key" not in keys[0]

    r = await client.patch(
        f"/auth/api-keys/{key_id}",
        json={"is_active": False},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    assert (await client.get("/auth/me", headers=headers)).status_code == 401

    r = await client.delete(
        f"/auth/api-keys/{key_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert r.status_code == 204
    keys = (await client.get("/auth/api-keys", headers={"Authorization": f"Bearer {token}"})).json()
    assert keys == []


# --- Роли ---


async def test_user_cannot_access_admin(client):
    await client.post("/auth/register", json={"username": "frank", "password": "secret123"})
    token = (
        await client.post("/auth/login", json={"username": "frank", "password": "secret123"})
    ).json()["access_token"]
    r = await client.get("/admin/users", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403


async def test_admin_can_list_users(client, db_engine):
    factory = async_sessionmaker(db_engine, expire_on_commit=False)
    async with factory() as session:
        await auth_service.create_user(session, "admin1", "secret123", role="admin")

    token = (
        await client.post("/auth/login", json={"username": "admin1", "password": "secret123"})
    ).json()["access_token"]
    r = await client.get("/admin/users", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert any(u["username"] == "admin1" for u in r.json())


# --- Квота запросов ---


async def test_quota_exceeded_429(client, db_engine):
    factory = async_sessionmaker(db_engine, expire_on_commit=False)
    async with factory() as session:
        await auth_service.create_user(session, "quota1", "secret123", request_limit=2)

    token = (
        await client.post("/auth/login", json={"username": "quota1", "password": "secret123"})
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    assert (await client.get("/auth/me", headers=headers)).status_code == 200
    assert (await client.get("/auth/me", headers=headers)).status_code == 200
    assert (await client.get("/auth/me", headers=headers)).status_code == 429


# --- Bootstrap администратора ---


async def test_ensure_admin_user_idempotent(client, db_engine, monkeypatch):
    monkeypatch.setattr(settings, "admin_username", "root")
    monkeypatch.setattr(settings, "admin_password", "adminpass")

    factory = async_sessionmaker(db_engine, expire_on_commit=False)
    async with factory() as session:
        await auth_service.ensure_admin_user(session)
        await auth_service.ensure_admin_user(session)
        user = await auth_service.get_user_by_username(session, "root")

    assert user is not None
    assert user.role == "admin"
