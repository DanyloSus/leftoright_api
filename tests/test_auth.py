import os

import pytest
from fastapi import status

_is_sqlite = os.getenv("TEST_DATABASE_URL", "sqlite+aiosqlite:///:memory:").startswith(
    "sqlite"
)

REGISTER_PAYLOAD = {
    "email": "user@example.com",
    "username": "someuser",
    "password": "strongpassword1",
}


async def test_register_returns_token_pair(client):
    resp = await client.post("/api/auth/register", json=REGISTER_PAYLOAD)
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.skipif(
    _is_sqlite, reason="duplicate detection uses pgcode — requires PostgreSQL"
)
async def test_register_duplicate_email_returns_409(client):
    await client.post("/api/auth/register", json=REGISTER_PAYLOAD)
    resp = await client.post("/api/auth/register", json=REGISTER_PAYLOAD)
    assert resp.status_code == status.HTTP_409_CONFLICT


async def test_login_returns_token_pair(client):
    await client.post("/api/auth/register", json=REGISTER_PAYLOAD)
    resp = await client.post(
        "/api/auth/login",
        json={
            "email": REGISTER_PAYLOAD["email"],
            "password": REGISTER_PAYLOAD["password"],
        },
    )
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data


async def test_login_wrong_password_returns_403(client):
    await client.post("/api/auth/register", json=REGISTER_PAYLOAD)
    resp = await client.post(
        "/api/auth/login",
        json={
            "email": REGISTER_PAYLOAD["email"],
            "password": "wrongpassword1",
        },
    )
    assert resp.status_code == status.HTTP_403_FORBIDDEN


async def test_get_me_returns_user(auth_client):
    resp = await auth_client.get("/api/auth/me")
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["email"] == "test@example.com"
    assert data["username"] == "testuser"
    assert "id" in data


async def test_get_me_without_token_returns_401(client):
    resp = await client.get("/api/auth/me")
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED
