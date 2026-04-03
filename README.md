# LeftToRight Backend

FastAPI backend for a tournament bracket voting system. Users create tournaments, add participants (entities), and run elimination-style bracket sessions where votes determine winners round by round. Supports real-time multiplayer sessions via WebSockets.

## Tech Stack

- **Python 3.12** / **FastAPI**
- **SQLAlchemy** (async) + **Alembic** migrations
- **PostgreSQL 16** (production) / **SQLite** (testing)
- **Redis** — caching & real-time pub/sub
- **JWT** authentication (access + refresh tokens)
- **Docker** & **Docker Compose**
- **structlog** for structured logging
- **slowapi** for rate limiting

## Project Structure

```
app/
├── main.py                  # FastAPI app, middleware, exception handlers
├── router.py                # Top-level API router (/api prefix)
├── middleware.py             # Request logging middleware
├── auth/                    # Auth utilities (context, token helpers)
├── di/                      # Dependency injection (auth, exceptions, limiter, redis)
├── constants/               # Validation constants
├── models/                  # SQLAlchemy base model
├── features/
│   ├── auth/                # Registration, login, token refresh
│   ├── user/                # User CRUD
│   ├── tournament/          # Tournament CRUD
│   ├── entity/              # Tournament participants
│   ├── session/             # Bracket sessions, voting, WebSocket handler
│   ├── match/               # Match model, bracket logic
│   └── healthcheck/         # Health endpoint
configs/                     # pydantic-settings configs (DB, JWT, Redis, CORS)
migrations/                  # Alembic migration versions
tests/                       # pytest test suite
deploy/                      # Deployment scripts & configs (EC2/RDS/ElastiCache)
```

Each feature module follows the same pattern:

| File           | Purpose                                       |
|----------------|-----------------------------------------------|
| `model.py`     | SQLAlchemy ORM model                          |
| `repo.py`      | Database access layer (no business logic)     |
| `service.py`   | Business logic, calls repos                   |
| `api.py`       | FastAPI router, injects service via `Depends` |
| `schemas.py`   | Pydantic request/response models              |

## Domain Flow

1. **Create a Tournament** — gives you a container for participants
2. **Add Entities** — participants in the bracket (songs, movies, players, etc.)
3. **Start a Session** — generates a full single-elimination bracket (power-of-2 sized, padded with byes) and pre-builds all rounds linking each match to its `next_match_id`
4. **Vote** — match-by-match; the winner propagates up to the parent match
5. **Session completes** — when no more votable matches remain, a winner is crowned

Bracket sessions also support real-time multiplayer via WebSockets (`/api/sessions/{id}/ws`).

## Prerequisites

- **Docker** & **Docker Compose** (recommended), or
- **Python 3.12+**, **PostgreSQL**, **Redis** installed locally

## Getting Started

### 1. Clone & configure environment

```bash
git clone <repository-url>
cd leftoright_backend
cp .env.example .env   # fill in your values
```

Required environment variables:

| Variable                 | Description                          |
|--------------------------|--------------------------------------|
| `DB_USER`                | PostgreSQL username                  |
| `DB_PASSWORD`            | PostgreSQL password                  |
| `DB_HOST`                | Database host (e.g. `postgres`)      |
| `DB_PORT`                | Database port (e.g. `5432`)          |
| `DB_NAME`                | Database name                        |
| `APP_PORT`               | Port to expose the API               |
| `JWT_SECRET_KEY`         | Secret key for JWT signing           |
| `REDIS_HOST`             | Redis host (e.g. `redis`)            |
| `REDIS_PORT`             | Redis port (e.g. `6379`)             |
| `CORS_ALLOW_ORIGINS`     | Comma-separated allowed origins      |
| `CORS_ALLOW_METHODS`     | Comma-separated allowed HTTP methods |
| `CORS_ALLOW_HEADERS`     | Comma-separated allowed headers      |

### 2. Run with Docker Compose

```bash
docker compose up api
```

This starts the API server, PostgreSQL, and Redis. The API is available at `http://localhost:<APP_PORT>/api`.

### 3. Run migrations

```bash
# Inside the running container
docker compose exec api alembic upgrade head

# Or locally (with DATABASE_URL configured)
alembic upgrade head
```

## API Routes

All routes are prefixed with `/api`.

| Prefix                                          | Tag            | Description              |
|-------------------------------------------------|----------------|--------------------------|
| `/api/healthcheck`                              | Healthcheck    | Health check endpoint    |
| `/api/auth`                                     | Authentication | Register, login, refresh |
| `/api/users`                                    | Users          | User CRUD                |
| `/api/tournaments`                              | Tournaments    | Tournament CRUD          |
| `/api/tournaments/{id}/entities`                | Entities       | Manage participants      |
| `/api/tournaments/{id}/sessions`                | Sessions       | Create/start sessions    |
| `/api/sessions`                                 | Sessions       | Session operations       |

Interactive API docs are available at `/docs` (Swagger UI) and `/redoc` (ReDoc).

## Database Migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Create a new migration after model changes
alembic revision --autogenerate -m "description of change"

# Roll back the last migration
alembic downgrade -1
```

## Testing

### Local (SQLite in-memory — fast)

```bash
pytest -v
```

```bash
# Single test file
pytest tests/test_sessions.py -v

# Single test by name
pytest tests/test_tournaments.py::test_create_tournament -v
```

### Docker (PostgreSQL)

```bash
docker compose --profile test up test
```

Tests use SQLite in-memory by default. Set `TEST_DATABASE_URL=postgresql+psycopg://...` to run against PostgreSQL instead.

### Test fixtures (`tests/conftest.py`)

| Fixture       | Description                                                  |
|---------------|--------------------------------------------------------------|
| `client`      | Async HTTP client with a fresh schema per test               |
| `db`          | Raw async SQLAlchemy session                                 |
| `auth_client` | Pre-authenticated client (`test@example.com` / `testuser`)   |

> **Note:** `conftest.py` sets environment variables before any app imports because pydantic-settings validates config at import time.

## WebSocket

Sessions support real-time multiplayer via WebSocket at:

```
ws://localhost:<APP_PORT>/api/sessions/{sessionId}/ws
```

The first message must be `JOIN_SESSION` or `RECONNECT_SESSION`. See [docs/websocket-frontend-guide.md](docs/websocket-frontend-guide.md) for full protocol documentation and TypeScript types.

## Deployment

Production deployment targets **AWS** (EC2 + RDS + ElastiCache). See [deploy/DEPLOY.md](deploy/DEPLOY.md) for the full guide.

## License

All rights reserved.
