import os

# Set required env vars before any app imports (pydantic-settings validates at import time)
os.environ.setdefault("DB_USER", "test")
os.environ.setdefault("DB_PASSWORD", "test")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_PORT", "5432")
os.environ.setdefault("DB_NAME", "test")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-testing-only")
os.environ.setdefault("CORS_ALLOW_ORIGINS", '["*"]')
os.environ.setdefault("CORS_ALLOW_METHODS", '["*"]')
os.environ.setdefault("CORS_ALLOW_HEADERS", '["*"]')

import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

# Import all models so SQLAlchemy registers them with Model.metadata
import app.features.user.model  # noqa: F401
import app.features.tournament.model  # noqa: F401
import app.features.entity.model  # noqa: F401
import app.features.session.model  # noqa: F401
import app.features.match.model  # noqa: F401

from app.models.base import Model
from configs.session import get_session
from app.main import app

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite+aiosqlite:///:memory:")
_is_sqlite = TEST_DATABASE_URL.startswith("sqlite")

engine = create_async_engine(
    TEST_DATABASE_URL,
    **(
        {"connect_args": {"check_same_thread": False}, "poolclass": StaticPool}
        if _is_sqlite
        else {}
    ),
)
TestingSessionFactory = async_sessionmaker(engine, expire_on_commit=False)


@pytest_asyncio.fixture
async def client():
    async with engine.begin() as conn:
        await conn.run_sync(Model.metadata.create_all)

    async def override_get_session():
        async with TestingSessionFactory() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c

    app.dependency_overrides.clear()
    async with engine.begin() as conn:
        await conn.run_sync(Model.metadata.drop_all)


@pytest_asyncio.fixture
async def db(client):
    async with TestingSessionFactory() as session:
        yield session


@pytest_asyncio.fixture
async def auth_client(client):
    """AsyncClient pre-authenticated as a registered user. Also yields the token."""
    resp = await client.post(
        "/api/auth/register",
        json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "testpassword123",
        },
    )
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"
    yield client
