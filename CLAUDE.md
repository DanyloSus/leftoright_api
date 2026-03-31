# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

**Run API (development):**
```bash
docker-compose up api
```

**Run tests (Docker, against PostgreSQL):**
```bash
docker-compose --profile test up test
```

**Run tests locally (SQLite in-memory, faster):**
```bash
pytest -v
# Single test file:
pytest tests/test_sessions.py -v
# Single test by name:
pytest tests/test_sessions.py::test_start_session -v
```

**Database migrations:**
```bash
alembic upgrade head
alembic revision --autogenerate -m "description"
alembic downgrade -1
```

## Architecture

FastAPI backend for a tournament bracket system. All routes are prefixed `/api`.

**Feature modules** live under `app/features/` — each has the same structure:
- `model.py` — SQLAlchemy ORM model
- `repo.py` — database access (no business logic)
- `service.py` — business logic, calls repos
- `api.py` — FastAPI router, injects service via `Depends`
- `schemas.py` — Pydantic request/response models

**Domain flow:**
1. User creates a **Tournament**
2. **Entities** (participants) are added to the tournament
3. A **Session** is started — generates a full bracket (power-of-2 sized, padded with byes) and pre-builds all rounds upfront, linking each match to its `next_match_id` (parent in the bracket)
4. User **votes** match-by-match; winner propagates to the parent match's `entity_1_id` or `entity_2_id` based on position parity
5. Session completes when no more votable matches remain

**Bracket logic** (`app/features/match/service.py`, `app/features/session/service.py`):
- Bracket size is rounded up to the nearest power of 2; extra slots get `None` (bye)
- All rounds are created at session start (not lazily)
- Cascading byes are propagated immediately so the cursor skips to the first real vote
- Current position tracked via `session.current_round` + `session.current_match_position`

**Authentication:** JWT bearer tokens. `app/di/auth.py` provides `get_current_user` and `get_optional_user` dependencies. Sessions can be anonymous (no user) or owned.

**Error handling:** Raise `ErrNotFound`, `ErrAlreadyExists`, or `ErrPermissionDenied` from `app/di/exceptions.py` — these map to 404/409/403 in `app/main.py`. Services also raise `HTTPException` directly for domain validation errors (400s).

## Testing

Tests default to SQLite in-memory (`sqlite+aiosqlite:///:memory:`). Set `TEST_DATABASE_URL=postgresql+psycopg://...` to test against PostgreSQL (required in Docker via `docker-compose --profile test up test`).

Fixtures in `tests/conftest.py`:
- `client` — async HTTP client, fresh schema per test
- `db` — raw async SQLAlchemy session
- `auth_client` — `client` pre-authenticated (registers `test@example.com` / `testuser`)

`pytest.ini` sets `asyncio_mode = auto` so all async tests run without extra decorators.

**Important:** `conftest.py` must set env vars before any app imports because pydantic-settings validates config at import time.
