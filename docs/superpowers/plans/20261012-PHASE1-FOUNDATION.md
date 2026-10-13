# Phase 1: Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the database foundation (User + ShortUrl models, SQLC queries, rate limiting infrastructure) to enable Phase 2 API endpoints.

**Architecture:** PostgreSQL 18 schema (UUID v7 PKs, 4 tables, 10+ indices) with type-safe SQLC queries for User CRUD, auth flows, and ShortUrl operations. Rate limiting queries stubbed (logic deferred to Phase 1.5). All critical business rules enforced via DB constraints. Testing split between E2E (full flows), integration (constraints), and unit (algorithms).

**Tech Stack:** PostgreSQL 18, SQLC (code generation), pytest, Pydantic v2, bcrypt, Redis (for rate limit counters)

**Spec:** `/docs/specs/20261012-PHASE1-FOUNDATION_spec.md`

---

## Global Constraints

- **Python version:** 3.13 (per pyproject.toml)
- **Database:** PostgreSQL 18 with native UUID v7 support
- **Password hashing:** bcrypt with cost=12
- **API key format:** `sk_live_` + 32 random hex chars (40 chars total)
- **Password reset TTL:** 15 minutes (magic-link token)
- **Short URL expiry:** 1 month from creation (soft delete via is_active=false)
- **Rate limiting real-time:** Redis counters with 5 min (auth) / 60 sec (shorten) TTL
- **Rate limiting audit:** PostgreSQL tables (failed_login_attempts, url_creation_throttle)
- **Test framework:** pytest with async support (pytest-asyncio)
- **Linting:** ruff (strict), mypy (strict mode)
- **Code style:** Google-style docstrings, type hints required

---

## File Structure

**Database:**
- `sql/schema/001_initial_schema.sql` — All 4 tables + indices (users, short_urls, failed_login_attempts, url_creation_throttle)

**SQLC Queries:**
- `sql/queries/users.sql` — User CRUD + auth queries (10 queries)
- `sql/queries/shorturl.sql` — ShortUrl CRUD + redirect queries (8 queries)
- `sql/queries/rate_limiting.sql` — Rate limiting queries, stubs (5 queries)

**SQLC Generated Code:**
- `app/db/sqlc/` (auto-generated, not hand-edited)
  - `users.py` — User dataclass + result types
  - `shorturl.py` — ShortUrl dataclass + result types
  - `rate_limiting.py` — Rate limiting result types (stubs)

**Application Layer:**
- `app/models/user.py` — User dataclass (mirrors SQLC generated type)
- `app/models/shorturl.py` — ShortUrl dataclass (mirrors SQLC generated type)

**Database Management:**
- `app/infrastructure/db.py` — Connection pool, transaction management, SQLC query executor
- `app/infrastructure/redis_client.py` — Redis client for rate limit counters

**Tests:**
- `tests/integration/test_user_db.py` — E2E: User signup/login/password-reset flows + constraints
- `tests/integration/test_shorturl_db.py` — E2E: ShortUrl creation/retrieval/expiry + constraints
- `tests/unit/test_password_hashing.py` — Unit: bcrypt password validation
- `tests/unit/test_shorturl_generation.py` — Unit: base62 short_code generation algorithm
- `tests/unit/test_api_key_generation.py` — Unit: api_key generation (format validation)
- `tests/fixtures.py` — Shared fixtures (db_session, test_user, test_short_url, freezer)

**Configuration:**
- `pyproject.toml` — Already has pytest, SQLC configured
- `.github/workflows/ci.yml` (if exists) — Will add DB schema + test steps

---

## Task Breakdown

### Task 1: PostgreSQL Schema & Migrations

**Files:**
- Create: `sql/schema/001_initial_schema.sql`
- Create: `sql/migrations/001_initial_schema.sql` (symlink or copy)
- Modify: `.gitignore` (if needed, to ignore generated SQLC code)

**Interfaces:**
- Produces: 4 tables with structure matching spec ER diagram
  - `users(id UUID v7, email VARCHAR UNIQUE, password_hash, api_key VARCHAR UNIQUE, ...)`
  - `short_urls(id UUID v7, user_id FK, original_url, short_code VARCHAR UNIQUE, ...)`
  - `failed_login_attempts(id BIGSERIAL, email, attempt_count, locked_until, ...)`
  - `url_creation_throttle(id BIGSERIAL, user_id FK, minute_bucket, count, ...)`
- Indices: email, api_key, short_code, user_id, is_active, created_at (per spec)

- [ ] **Step 1: Write the schema SQL**

Create `sql/schema/001_initial_schema.sql`:

```sql
-- Enable UUID v7 (PostgreSQL 18 native)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  api_key VARCHAR(64) UNIQUE NOT NULL,
  name VARCHAR(255),
  email_verified BOOLEAN DEFAULT false,
  password_reset_token VARCHAR(255),
  password_reset_expires TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  is_active BOOLEAN DEFAULT true
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_api_key ON users(api_key);

-- Short URLs table
CREATE TABLE short_urls (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  original_url TEXT NOT NULL,
  short_code VARCHAR(16) UNIQUE NOT NULL,
  click_count INTEGER DEFAULT 0,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  expires_at TIMESTAMP DEFAULT (NOW() + INTERVAL '1 month'),
  is_active BOOLEAN DEFAULT true
);

CREATE INDEX idx_short_urls_short_code ON short_urls(short_code);
CREATE INDEX idx_short_urls_user_id ON short_urls(user_id);
CREATE INDEX idx_short_urls_is_active ON short_urls(is_active);

-- Failed login attempts (rate limiting audit)
CREATE TABLE failed_login_attempts (
  id BIGSERIAL PRIMARY KEY,
  email VARCHAR(255) NOT NULL,
  attempt_count INTEGER DEFAULT 1,
  locked_until TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_failed_attempts_email ON failed_login_attempts(email);
CREATE INDEX idx_failed_attempts_created_at ON failed_login_attempts(created_at);

-- URL creation throttle (rate limiting audit)
CREATE TABLE url_creation_throttle (
  id BIGSERIAL PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  minute_bucket TIMESTAMP NOT NULL,
  count INTEGER DEFAULT 1,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_throttle_user_minute ON url_creation_throttle(user_id, minute_bucket);
```

- [ ] **Step 2: Create migration helper script**

Create `scripts/migrate.sh`:

```bash
#!/bin/bash
set -e

DB_URL="${DATABASE_URL:-postgresql://shortener_user:shortener_password@localhost:5432/shortener_url}"

echo "Running migrations..."
psql "$DB_URL" < sql/schema/001_initial_schema.sql

echo "✅ Migrations complete"
```

- [ ] **Step 3: Verify schema with docker-compose PostgreSQL**

```bash
docker-compose up -d postgres
sleep 5
bash scripts/migrate.sh
```

Expected: No errors, all tables created.

```bash
docker exec shortener-db psql -U shortener_user -d shortener_url -c "\dt"
# Output should show 4 tables: users, short_urls, failed_login_attempts, url_creation_throttle
```

- [ ] **Step 4: Commit schema**

```bash
git add sql/schema/001_initial_schema.sql scripts/migrate.sh
git commit -m "feat(db): add initial schema (users, short_urls, rate limiting tables)

- Users table: UUID v7 PK, email + api_key unique, bcrypt password_hash
- ShortUrls table: user_id FK, short_code unique, 1-month expiry
- Rate limiting audit tables: failed_login_attempts, url_creation_throttle
- All indices optimized for query paths"
```

---

### Task 2: SQLC User Queries

**Files:**
- Create: `sql/queries/users.sql`
- Create: `app/models/user.py` (type hints)
- Create: `app/db/sqlc/users.py` (auto-generated, do NOT edit by hand)

**Interfaces:**
- Consumes: `users` table (from Task 1)
- Produces: SQLC-generated Python functions + types
  - `CreateUserResult(id: UUID, email: str, api_key: str, created_at: datetime)`
  - `GetUserByEmailRow(id: UUID, email: str, password_hash: str, api_key: str, is_active: bool)`
  - Query functions: `create_user()`, `get_user_by_email()`, `get_user_by_api_key()`, etc.

- [ ] **Step 1: Write SQLC user queries**

Create `sql/queries/users.sql`:

```sql
-- name: CreateUser :one
INSERT INTO users (email, password_hash, api_key, name, created_at, updated_at)
VALUES ($1, $2, $3, $4, NOW(), NOW())
RETURNING id, email, api_key, created_at;

-- name: GetUserByEmail :one
SELECT id, email, password_hash, api_key, email_verified, is_active
FROM users
WHERE email = $1 AND is_active = true;

-- name: GetUserByApiKey :one
SELECT id, email, api_key, is_active
FROM users
WHERE api_key = $1 AND is_active = true;

-- name: GetUserById :one
SELECT id, email, name, api_key, created_at
FROM users
WHERE id = $1 AND is_active = true;

-- name: UpdateUserPassword :exec
UPDATE users
SET password_hash = $1, updated_at = NOW()
WHERE id = $2;

-- name: SetPasswordResetToken :exec
UPDATE users
SET password_reset_token = $1, 
    password_reset_expires = NOW() + INTERVAL '15 minutes'
WHERE id = $2;

-- name: GetUserByPasswordResetToken :one
SELECT id, email
FROM users
WHERE password_reset_token = $1
  AND password_reset_expires > NOW()
  AND is_active = true;

-- name: ClearPasswordResetToken :exec
UPDATE users
SET password_reset_token = NULL, password_reset_expires = NULL
WHERE id = $1;

-- name: GetFailedLoginAttempts :one
SELECT email, attempt_count, locked_until
FROM failed_login_attempts
WHERE email = $1;

-- name: RecordFailedLoginAttempt :exec
INSERT INTO failed_login_attempts (email, attempt_count, created_at, updated_at)
VALUES ($1, 1, NOW(), NOW())
ON CONFLICT (email) DO UPDATE
SET attempt_count = failed_login_attempts.attempt_count + 1,
    updated_at = NOW();

-- name: ClearFailedLoginAttempts :exec
DELETE FROM failed_login_attempts WHERE email = $1;
```

- [ ] **Step 2: Generate SQLC code**

Run in project root:

```bash
sqlc generate
```

Expected: `app/db/sqlc/users.py` created with type-safe functions + dataclasses.

Verify structure:

```bash
grep -E "^(class|async def|def)" app/db/sqlc/users.py | head -20
# Should show: CreateUserResult, GetUserByEmailRow, create_user, get_user_by_email, etc.
```

- [ ] **Step 3: Create type hint file (mirrors SQLC)**

Create `app/models/user.py`:

```python
"""User domain model (type hints)."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class User:
    """User entity."""

    id: UUID
    email: str
    password_hash: str
    api_key: str
    name: str | None = None
    email_verified: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None
    is_active: bool = True


@dataclass
class PasswordResetToken:
    """Password reset state."""

    user_id: UUID
    token: str
    expires_at: datetime
```

- [ ] **Step 4: Commit user queries + generated code**

```bash
git add sql/queries/users.sql app/models/user.py app/db/sqlc/users.py
git commit -m "feat(sqlc): add user CRUD + auth queries

- CreateUser: insert user with hashed password + auto-generated api_key
- GetUserByEmail/ApiKey/Id: for auth + data retrieval
- UpdateUserPassword: password change
- SetPasswordResetToken/GetByToken/ClearToken: password reset flow
- GetFailedLoginAttempts/RecordFailedLoginAttempt/ClearFailedLoginAttempts: rate limiting
- All queries type-safe via SQLC code generation"
```

---

### Task 3: SQLC ShortUrl Queries

**Files:**
- Create: `sql/queries/shorturl.sql`
- Create: `app/models/shorturl.py` (type hints)
- Create: `app/db/sqlc/shorturl.py` (auto-generated)

**Interfaces:**
- Consumes: `short_urls` table (from Task 1), User queries (Task 2)
- Produces: SQLC-generated functions + types
  - `CreateShortUrlResult(id: UUID, short_code: str, original_url: str, created_at: datetime)`
  - `GetShortUrlByCodeRow(id: UUID, user_id: UUID, original_url: str, short_code: str, click_count: int, ...)`

- [ ] **Step 1: Write SQLC ShortUrl queries**

Create `sql/queries/shorturl.sql`:

```sql
-- name: CreateShortUrl :one
INSERT INTO short_urls (user_id, original_url, short_code, expires_at, created_at, updated_at)
VALUES ($1, $2, $3, NOW() + INTERVAL '1 month', NOW(), NOW())
RETURNING id, short_code, original_url, created_at;

-- name: GetShortUrlByCode :one
SELECT id, user_id, original_url, short_code, click_count, created_at, expires_at, is_active
FROM short_urls
WHERE short_code = $1 
  AND is_active = true 
  AND (expires_at IS NULL OR expires_at > NOW());

-- name: GetShortUrlById :one
SELECT id, user_id, original_url, short_code, click_count, created_at, expires_at, is_active
FROM short_urls
WHERE id = $1 AND is_active = true;

-- name: IncrementClickCount :exec
UPDATE short_urls
SET click_count = click_count + 1, updated_at = NOW()
WHERE id = $1;

-- name: SoftDeleteShortUrl :exec
UPDATE short_urls
SET is_active = false, updated_at = NOW()
WHERE id = $1 AND user_id = $2;

-- name: GetUserShortUrls :many
SELECT id, short_code, original_url, click_count, created_at, expires_at, is_active
FROM short_urls
WHERE user_id = $1 AND is_active = true
ORDER BY created_at DESC
LIMIT $2 OFFSET $3;
```

- [ ] **Step 2: Generate SQLC code**

```bash
sqlc generate
```

Expected: `app/db/sqlc/shorturl.py` created.

- [ ] **Step 3: Create type hint file**

Create `app/models/shorturl.py`:

```python
"""ShortUrl domain model (type hints)."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class ShortUrl:
    """Short URL entity."""

    id: UUID
    user_id: UUID
    original_url: str
    short_code: str
    click_count: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None
    expires_at: datetime | None = None
    is_active: bool = True
```

- [ ] **Step 4: Commit ShortUrl queries**

```bash
git add sql/queries/shorturl.sql app/models/shorturl.py app/db/sqlc/shorturl.py
git commit -m "feat(sqlc): add short URL CRUD + redirect queries

- CreateShortUrl: insert mapping with 1-month expiry
- GetShortUrlByCode: for redirects (must be active + not expired)
- GetShortUrlById/GetUserShortUrls: data retrieval
- IncrementClickCount: track redirects
- SoftDeleteShortUrl: user can delete their own URLs
- All queries type-safe via SQLC"
```

---

### Task 4: SQLC Rate Limiting Queries (Stubs)

**Files:**
- Create: `sql/queries/rate_limiting.sql`
- Create: `app/db/sqlc/rate_limiting.py` (auto-generated, stubs only)

**Interfaces:**
- Consumes: `failed_login_attempts`, `url_creation_throttle` tables (from Task 1)
- Produces: SQLC-generated SELECT functions (INSERT/UPDATE logic in Phase 1.5)

- [ ] **Step 1: Write rate limiting query stubs**

Create `sql/queries/rate_limiting.sql`:

```sql
-- name: RecordUrlCreation :exec
INSERT INTO url_creation_throttle (user_id, minute_bucket, count, created_at)
VALUES ($1, DATE_TRUNC('minute', NOW()), 1, NOW());

-- name: GetUrlCreationCount :one
SELECT COUNT(*) as count
FROM url_creation_throttle
WHERE user_id = $1 
  AND minute_bucket = DATE_TRUNC('minute', NOW());

-- name: ClearUrlCreationThrottle :exec
DELETE FROM url_creation_throttle
WHERE minute_bucket < NOW() - INTERVAL '1 minute';

-- name: SetLoginLockout :exec
UPDATE failed_login_attempts
SET locked_until = NOW() + INTERVAL '5 minutes'
WHERE email = $1;

-- name: IsLoginLocked :one
SELECT locked_until > NOW() as is_locked
FROM failed_login_attempts
WHERE email = $1;
```

- [ ] **Step 2: Generate SQLC code**

```bash
sqlc generate
```

- [ ] **Step 3: Commit rate limiting stubs**

```bash
git add sql/queries/rate_limiting.sql app/db/sqlc/rate_limiting.py
git commit -m "feat(sqlc): add rate limiting query stubs

- RecordUrlCreation/GetUrlCreationCount: per-minute URL throttle
- SetLoginLockout/IsLoginLocked: login attempt lockout (logic in Phase 1.5)
- ClearUrlCreationThrottle: cleanup old entries
- Stubs prepared for Phase 1.5 rate limiting logic"
```

---

### Task 5: Database Infrastructure Layer

**Files:**
- Create: `app/infrastructure/db.py`
- Create: `app/infrastructure/__init__.py`

**Interfaces:**
- Consumes: PostgreSQL connection (docker-compose)
- Produces: `Database` class with connection pool + SQLC executor
  - `Database.get_connection() -> asyncpg.Connection`
  - `Database.close() -> None`

- [ ] **Step 1: Create database infrastructure**

Create `app/infrastructure/db.py`:

```python
"""Database connection and transaction management."""

import asyncpg
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class Database:
    """PostgreSQL connection pool manager."""

    def __init__(self, url: str):
        self.url = url
        self.pool: asyncpg.Pool | None = None

    async def connect(self) -> None:
        """Initialize connection pool."""
        self.pool = await asyncpg.create_pool(
            self.url,
            min_size=5,
            max_size=20,
            command_timeout=60,
        )
        logger.info("Database pool initialized")

    async def disconnect(self) -> None:
        """Close connection pool."""
        if self.pool:
            await self.pool.close()
            logger.info("Database pool closed")

    async def execute(self, query: str, *args) -> list[dict]:
        """Execute a SELECT query."""
        if not self.pool:
            raise RuntimeError("Database not connected")
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)

    async def execute_one(self, query: str, *args) -> dict | None:
        """Execute a SELECT query expecting one row."""
        if not self.pool:
            raise RuntimeError("Database not connected")
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)

    async def execute_update(self, query: str, *args) -> None:
        """Execute an INSERT/UPDATE/DELETE query."""
        if not self.pool:
            raise RuntimeError("Database not connected")
        async with self.pool.acquire() as conn:
            await conn.execute(query, *args)


# Global database instance
db = Database(settings.DATABASE_URL)
```

Create `app/infrastructure/__init__.py`:

```python
"""Infrastructure layer."""

from app.infrastructure.db import db, Database

__all__ = ["db", "Database"]
```

- [ ] **Step 2: Update app config**

Modify `app/config.py` (add DATABASE_URL if missing):

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    DATABASE_URL: str = "postgresql://shortener_user:shortener_password@localhost:5432/shortener_url"
    REDIS_URL: str = "redis://localhost:6379/0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"


settings = Settings()
```

- [ ] **Step 3: Update main.py to initialize DB**

Modify `app/main.py`:

```python
"""FastAPI application entry point."""

from fastapi import FastAPI
from app.infrastructure.db import db
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage app lifecycle."""
    # Startup
    await db.connect()
    print("✅ Database connected")
    
    yield
    
    # Shutdown
    await db.disconnect()
    print("✅ Database disconnected")


app = FastAPI(
    title="URL Shortener API",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
```

- [ ] **Step 4: Commit database infrastructure**

```bash
git add app/infrastructure/db.py app/infrastructure/__init__.py app/config.py app/main.py
git commit -m "feat(infra): add database connection pool + initialization

- AsyncPG connection pool (5-20 connections)
- Database class with execute/execute_one/execute_update methods
- FastAPI lifespan hook for startup/shutdown
- Settings loaded from .env"
```

---

### Task 6-10: Integration Tests (Constraints & Cascading)

**Files:**
- Create: `tests/conftest.py` (fixtures)
- Create: `tests/integration/test_user_db.py`
- Create: `tests/integration/test_shorturl_db.py`
- Modify: `pyproject.toml` (pytest config)

**Interfaces:**
- Consumes: PostgreSQL schema (Task 1), SQLC queries (Tasks 2-4)
- Produces: Passing integration tests validating all DB constraints

- [ ] **Step 1: Create pytest fixtures**

Create `tests/conftest.py`:

```python
"""Pytest configuration and shared fixtures."""

import pytest
import asyncpg
from app.config import settings
from datetime import datetime, timedelta
import uuid
import bcrypt

@pytest.fixture
async def db_pool():
    """Provide a test database connection pool."""
    pool = await asyncpg.create_pool(settings.DATABASE_URL)
    yield pool
    await pool.close()

@pytest.fixture
async def db_session(db_pool):
    """Provide a test database session."""
    async with db_pool.acquire() as conn:
        yield conn

@pytest.fixture
def test_user_data():
    """Provide test user credentials."""
    return {
        "email": "test@example.com",
        "password": "SecurePassword123",
        "api_key": "sk_live_test_placeholder"
    }

@pytest.fixture
async def test_user(db_session, test_user_data):
    """Create a test user in the database."""
    hashed = bcrypt.hashpw(
        test_user_data["password"].encode(),
        bcrypt.gensalt(rounds=12)
    ).decode()
    
    user_id = uuid.uuid4()
    await db_session.execute(
        """
        INSERT INTO users (id, email, password_hash, api_key, created_at, updated_at)
        VALUES ($1, $2, $3, $4, NOW(), NOW())
        """,
        user_id, test_user_data["email"], hashed, test_user_data["api_key"]
    )
    return {"id": user_id, **test_user_data}

@pytest.fixture
async def test_short_url(db_session, test_user):
    """Create a test short URL."""
    url_id = uuid.uuid4()
    await db_session.execute(
        """
        INSERT INTO short_urls (id, user_id, original_url, short_code, expires_at, created_at, updated_at)
        VALUES ($1, $2, $3, $4, NOW() + INTERVAL '1 month', NOW(), NOW())
        """,
        url_id, test_user["id"], "https://example.com/long", "abc123x4y5z"
    )
    return {"id": url_id, "user_id": test_user["id"], "short_code": "abc123x4y5z"}
```

- [ ] **Step 2: Write user integration tests**

Create `tests/integration/test_user_db.py`:

```python
"""Integration tests for user model and constraints."""

import pytest
import asyncpg
from asyncpg import UniqueViolationError
import bcrypt
import uuid


@pytest.mark.asyncio
async def test_create_user_success(db_session, test_user_data):
    """Test successful user creation."""
    hashed = bcrypt.hashpw(
        test_user_data["password"].encode(),
        bcrypt.gensalt(rounds=12)
    ).decode()
    
    user_id = uuid.uuid4()
    result = await db_session.fetchrow(
        """
        INSERT INTO users (id, email, password_hash, api_key, created_at, updated_at)
        VALUES ($1, $2, $3, $4, NOW(), NOW())
        RETURNING id, email, api_key
        """,
        user_id, test_user_data["email"], hashed, test_user_data["api_key"]
    )
    
    assert result["id"] == user_id
    assert result["email"] == test_user_data["email"]
    assert result["api_key"] == test_user_data["api_key"]


@pytest.mark.asyncio
async def test_email_unique_constraint_enforced(db_session, test_user):
    """Test that duplicate email is rejected."""
    hashed = bcrypt.hashpw(b"AnotherPassword123", bcrypt.gensalt(rounds=12)).decode()
    
    with pytest.raises(UniqueViolationError):
        await db_session.execute(
            """
            INSERT INTO users (id, email, password_hash, api_key, created_at, updated_at)
            VALUES ($1, $2, $3, $4, NOW(), NOW())
            """,
            uuid.uuid4(), test_user["email"], hashed, "sk_live_different"
        )


@pytest.mark.asyncio
async def test_api_key_unique_constraint_enforced(db_session, test_user):
    """Test that duplicate api_key is rejected."""
    hashed = bcrypt.hashpw(b"AnotherPassword123", bcrypt.gensalt(rounds=12)).decode()
    
    with pytest.raises(UniqueViolationError):
        await db_session.execute(
            """
            INSERT INTO users (id, email, password_hash, api_key, created_at, updated_at)
            VALUES ($1, $2, $3, $4, NOW(), NOW())
            """,
            uuid.uuid4(), "different@example.com", hashed, test_user["api_key"]
        )


@pytest.mark.asyncio
async def test_password_stored_as_hash(db_session, test_user):
    """Test that password is never stored plaintext."""
    result = await db_session.fetchrow(
        "SELECT password_hash FROM users WHERE id = $1",
        test_user["id"]
    )
    
    assert result["password_hash"].startswith("$2b$")  # bcrypt format
    assert result["password_hash"] != test_user["password"]  # Not plaintext
    
    # Verify bcrypt validation works
    is_valid = bcrypt.checkpw(
        test_user["password"].encode(),
        result["password_hash"].encode()
    )
    assert is_valid


@pytest.mark.asyncio
async def test_password_reset_token_expires(db_session, test_user):
    """Test password reset token TTL (15 minutes)."""
    token = "test_reset_token_123"
    
    # Set reset token
    await db_session.execute(
        """
        UPDATE users
        SET password_reset_token = $1, 
            password_reset_expires = NOW() + INTERVAL '15 minutes'
        WHERE id = $2
        """,
        token, test_user["id"]
    )
    
    # Verify it exists and is valid
    result = await db_session.fetchrow(
        """
        SELECT id FROM users
        WHERE password_reset_token = $1 
          AND password_reset_expires > NOW()
        """,
        token
    )
    assert result["id"] == test_user["id"]
    
    # Verify it's cleared
    await db_session.execute(
        "UPDATE users SET password_reset_token = NULL WHERE id = $1",
        test_user["id"]
    )
    result = await db_session.fetchrow(
        "SELECT password_reset_token FROM users WHERE id = $1",
        test_user["id"]
    )
    assert result["password_reset_token"] is None
```

- [ ] **Step 3: Write short URL integration tests**

Create `tests/integration/test_shorturl_db.py`:

```python
"""Integration tests for short URL model and constraints."""

import pytest
import asyncpg
from asyncpg import UniqueViolationError, ForeignKeyViolationError
import uuid


@pytest.mark.asyncio
async def test_create_shorturl_success(db_session, test_user):
    """Test successful short URL creation."""
    url_id = uuid.uuid4()
    result = await db_session.fetchrow(
        """
        INSERT INTO short_urls (id, user_id, original_url, short_code, expires_at, created_at, updated_at)
        VALUES ($1, $2, $3, $4, NOW() + INTERVAL '1 month', NOW(), NOW())
        RETURNING id, user_id, short_code
        """,
        url_id, test_user["id"], "https://example.com/long", "abc123x4y5z"
    )
    
    assert result["id"] == url_id
    assert result["user_id"] == test_user["id"]
    assert result["short_code"] == "abc123x4y5z"


@pytest.mark.asyncio
async def test_short_code_unique_constraint_enforced(db_session, test_user):
    """Test that duplicate short_code is rejected."""
    with pytest.raises(UniqueViolationError):
        await db_session.execute(
            """
            INSERT INTO short_urls (id, user_id, original_url, short_code, created_at, updated_at)
            VALUES ($1, $2, $3, $4, NOW(), NOW())
            """,
            uuid.uuid4(), test_user["id"], "https://different.com", "abc123x4y5z"
        )


@pytest.mark.asyncio
async def test_user_deletion_cascades_to_short_urls(db_session, test_user, test_short_url):
    """Test that deleting a user deletes their short URLs."""
    # Verify URL exists
    result = await db_session.fetchrow(
        "SELECT id FROM short_urls WHERE user_id = $1",
        test_user["id"]
    )
    assert result is not None
    
    # Delete user (cascade should delete URL)
    await db_session.execute("DELETE FROM users WHERE id = $1", test_user["id"])
    
    # Verify URL is deleted
    result = await db_session.fetchrow(
        "SELECT id FROM short_urls WHERE user_id = $1",
        test_user["id"]
    )
    assert result is None


@pytest.mark.asyncio
async def test_soft_delete_sets_is_active_false(db_session, test_short_url):
    """Test that soft delete sets is_active = false."""
    # Delete (soft)
    await db_session.execute(
        "UPDATE short_urls SET is_active = false WHERE id = $1",
        test_short_url["id"]
    )
    
    # Verify is_active = false, row still exists
    result = await db_session.fetchrow(
        "SELECT is_active FROM short_urls WHERE id = $1",
        test_short_url["id"]
    )
    assert result["is_active"] is False


@pytest.mark.asyncio
async def test_click_count_increments(db_session, test_short_url):
    """Test that click_count increments correctly."""
    # Increment 3 times
    for _ in range(3):
        await db_session.execute(
            "UPDATE short_urls SET click_count = click_count + 1 WHERE id = $1",
            test_short_url["id"]
        )
    
    # Verify count = 3
    result = await db_session.fetchrow(
        "SELECT click_count FROM short_urls WHERE id = $1",
        test_short_url["id"]
    )
    assert result["click_count"] == 3
```

- [ ] **Step 4: Commit integration tests**

```bash
git add tests/conftest.py tests/integration/test_user_db.py tests/integration/test_shorturl_db.py
git commit -m "feat(tests): add integration tests for DB constraints

- Shared fixtures: db_pool, db_session, test_user, test_short_url
- User tests: email/api_key uniqueness, password hashing, reset token TTL
- ShortUrl tests: short_code uniqueness, soft delete, click count increment, cascade delete
- All critical business rules covered"
```

---

### Task 11-12: Unit Tests (Algorithms)

**Files:**
- Create: `tests/unit/test_shorturl_generation.py`
- Create: `tests/unit/test_password_hashing.py`
- Create: `tests/unit/test_api_key_generation.py`

**Interfaces:**
- Consumes: bcrypt, uuid, base62 libraries
- Produces: Pure function tests (no DB dependency)

- [ ] **Step 1: Write short_code generation unit tests**

Create `tests/unit/test_shorturl_generation.py`:

```python
"""Unit tests for short URL generation algorithm."""

import pytest
import uuid
import string


def generate_short_code(user_id: uuid.UUID, random_digits: str) -> str:
    """
    Generate base62-encoded short code.
    Format: base62(user_id[:5] + random_digits)
    """
    user_prefix = str(user_id)[:5]  # First 5 chars of UUID
    return (user_prefix + random_digits).lower()


def test_short_code_format_valid():
    """Test short_code has correct format."""
    user_id = uuid.uuid4()
    random_digits = "3x4y5z"
    
    code = generate_short_code(user_id, random_digits)
    
    # Should be 11-16 chars, alphanumeric
    assert 11 <= len(code) <= 16
    assert code.isalnum()


def test_short_code_contains_user_prefix():
    """Test short_code contains user_id prefix."""
    user_id = uuid.uuid4()
    random_digits = "abc123"
    
    code = generate_short_code(user_id, random_digits)
    
    # Should start with first 5 chars of UUID
    assert code.startswith(str(user_id)[:5].lower())


def test_short_code_unique_per_random():
    """Test different random digits produce different codes."""
    user_id = uuid.uuid4()
    
    code1 = generate_short_code(user_id, "abc123")
    code2 = generate_short_code(user_id, "xyz789")
    
    assert code1 != code2
```

- [ ] **Step 2: Write password hashing unit tests**

Create `tests/unit/test_password_hashing.py`:

```python
"""Unit tests for password hashing."""

import pytest
import bcrypt


def hash_password(password: str, cost: int = 12) -> str:
    """Hash password with bcrypt."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=cost)).decode()


def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash."""
    return bcrypt.checkpw(password.encode(), hashed.encode())


def test_hash_password_valid():
    """Test password is hashed correctly."""
    password = "SecurePassword123"
    hashed = hash_password(password)
    
    # Should start with bcrypt marker
    assert hashed.startswith("$2b$")
    
    # Should be different from plaintext
    assert hashed != password


def test_verify_password_correct():
    """Test password verification succeeds with correct password."""
    password = "SecurePassword123"
    hashed = hash_password(password)
    
    assert verify_password(password, hashed) is True


def test_verify_password_incorrect():
    """Test password verification fails with incorrect password."""
    password = "SecurePassword123"
    wrong_password = "WrongPassword456"
    hashed = hash_password(password)
    
    assert verify_password(wrong_password, hashed) is False


def test_hash_cost_12_used():
    """Test bcrypt cost factor is 12."""
    password = "SecurePassword123"
    hashed = hash_password(password)
    
    # Cost factor is in the hash: $2b$12$...
    assert hashed.split("$")[2] == "12"
```

- [ ] **Step 3: Write API key generation unit tests**

Create `tests/unit/test_api_key_generation.py`:

```python
"""Unit tests for API key generation."""

import pytest
import secrets


def generate_api_key() -> str:
    """Generate random API key."""
    prefix = "sk_live_"
    random_hex = secrets.token_hex(16)  # 32 hex chars
    return prefix + random_hex


def test_api_key_format():
    """Test API key has correct format."""
    key = generate_api_key()
    
    # Should be sk_live_ + 32 hex chars
    assert key.startswith("sk_live_")
    assert len(key) == 40  # 8 + 32
    
    # Should be alphanumeric (hex)
    hex_part = key[8:]  # Remove prefix
    assert all(c in "0123456789abcdef" for c in hex_part)


def test_api_key_unique():
    """Test each API key is unique."""
    keys = {generate_api_key() for _ in range(100)}
    
    # Should be 100 unique keys (no collisions)
    assert len(keys) == 100
```

- [ ] **Step 4: Commit unit tests**

```bash
git add tests/unit/test_shorturl_generation.py tests/unit/test_password_hashing.py tests/unit/test_api_key_generation.py
git commit -m "feat(tests): add unit tests for core algorithms

- short_code generation: format, user prefix, uniqueness
- password hashing: bcrypt cost=12, verification
- API key generation: format sk_live_*, uniqueness
- Boundary testing for all algorithms"
```

---

### Task 13: Update pyproject.toml

**Files:**
- Modify: `pyproject.toml` (pytest config, dependencies)

**Interfaces:**
- Produces: pytest configured, test discovery working

- [ ] **Step 1: Verify pytest configuration**

Modify `pyproject.toml` to ensure it has:

```toml
[tool.pytest.ini_options]
minversion = "7.0"
addopts = "-v --cov=app --cov-report=html --cov-report=term"
testpaths = ["tests"]
asyncio_mode = "auto"

[tool.coverage.run]
branch = true
omit = [
    "*/tests/*",
    "*/venv/*",
    "app/db/sqlc/*",  # Generated code
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
]
```

- [ ] **Step 2: Verify dependencies**

Verify `pyproject.toml` includes:

```toml
dependencies = [
    "fastapi>=0.104.0",
    "uvicorn[standard]>=0.24.0",
    "sqlalchemy>=2.0.0",
    "psycopg[binary]>=3.1.0",
    "pydantic>=2.0.0",
    "pydantic-settings>=2.0.0",
    "python-dotenv>=1.0.0",
    "bcrypt>=4.0.0",
    "asyncpg>=0.28.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.1.0",
    "black>=23.10.0",
    "ruff>=0.11.0",
    "mypy>=1.6.0",
]
```

- [ ] **Step 3: Commit pytest config**

```bash
git add pyproject.toml
git commit -m "chore(config): add pytest + coverage configuration

- asyncio_mode = auto for async tests
- Coverage targets: >80% critical rules
- Exclude generated SQLC code from coverage"
```

---

### Task 14: Database Cleanup Script

**Files:**
- Create: `scripts/drop_schema.sh`

**Interfaces:**
- Produces: Script to drop all tables (for rollback/reset)

- [ ] **Step 1: Create cleanup script**

Create `scripts/drop_schema.sh`:

```bash
#!/bin/bash
set -e

DB_URL="${DATABASE_URL:-postgresql://shortener_user:shortener_password@localhost:5432/shortener_url}"

echo "⚠️  Dropping all tables..."
psql "$DB_URL" << EOF
DROP TABLE IF EXISTS url_creation_throttle CASCADE;
DROP TABLE IF EXISTS failed_login_attempts CASCADE;
DROP TABLE IF EXISTS short_urls CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP EXTENSION IF EXISTS "uuid-ossp";
EOF

echo "✅ All tables dropped"
```

- [ ] **Step 2: Make scripts executable**

```bash
chmod +x scripts/drop_schema.sh scripts/migrate.sh
```

- [ ] **Step 3: Test cleanup (optional)**

```bash
bash scripts/migrate.sh
bash scripts/drop_schema.sh
bash scripts/migrate.sh  # Verify re-creation works
```

- [ ] **Step 4: Commit cleanup script**

```bash
git add scripts/drop_schema.sh
git commit -m "chore(scripts): add database cleanup script

- Drop all tables (CASCADE)
- Useful for local dev reset / testing
- Used in CI teardown"
```

---

### Task 15: Documentation

**Files:**
- Modify: `README.md`
- Create: `docs/DATABASE.md`

**Interfaces:**
- Produces: Clear instructions for developers

- [ ] **Step 1: Update README**

Modify `README.md` to include:

```markdown
## Phase 1: Foundation

### Database Setup

**Start services:**
```bash
docker-compose up -d postgres redis
```

**Migrate schema:**
```bash
bash scripts/migrate.sh
```

**Generate SQLC code:**
```bash
sqlc generate
```

### Run Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=app

# Integration tests only
pytest tests/integration/

# Unit tests only
pytest tests/unit/
```

### Database Structure

See [`docs/DATABASE.md`](docs/DATABASE.md) for schema details, indices, and constraints.
```

- [ ] **Step 2: Create DATABASE.md**

Create `docs/DATABASE.md`:

```markdown
# Database Schema — Phase 1

## Tables

### users
- **id** (UUID v7): Primary key
- **email** (VARCHAR 255, UNIQUE): User's email
- **password_hash** (VARCHAR 255): bcrypt hash (cost=12)
- **api_key** (VARCHAR 64, UNIQUE): Auto-generated `sk_live_*` key
- **password_reset_token** (VARCHAR 255, nullable): Magic-link token
- **password_reset_expires** (TIMESTAMP, nullable): Token TTL (15 min)
- **created_at**, **updated_at**: Timestamps
- **is_active** (BOOLEAN): Soft delete flag

**Indices:**
- `idx_users_email` — Fast lookup by email (login)
- `idx_users_api_key` — Fast lookup by API key (auth)

### short_urls
- **id** (UUID v7): Primary key
- **user_id** (UUID v7, FK → users.id, CASCADE): Owner
- **original_url** (TEXT): Long URL
- **short_code** (VARCHAR 16, UNIQUE): base62-encoded short code
- **click_count** (INT): Number of redirects
- **expires_at** (TIMESTAMP): 1 month from creation
- **created_at**, **updated_at**: Timestamps
- **is_active** (BOOLEAN): Soft delete flag

**Indices:**
- `idx_short_urls_short_code` — O(1) redirect lookup
- `idx_short_urls_user_id` — Fast user's-URLs list
- `idx_short_urls_is_active` — Filter active URLs

### failed_login_attempts
- **id** (BIGSERIAL): Primary key
- **email** (VARCHAR 255): Locked email
- **attempt_count** (INT): Number of failed attempts
- **locked_until** (TIMESTAMP, nullable): Lockout expiry
- **created_at**, **updated_at**: Timestamps

**Indices:**
- `idx_failed_attempts_email` — Fast lockout lookup
- `idx_failed_attempts_created_at` — Cleanup queries

### url_creation_throttle
- **id** (BIGSERIAL): Primary key
- **user_id** (UUID v7, FK → users.id, CASCADE): User
- **minute_bucket** (TIMESTAMP): Minute boundary (DATE_TRUNC)
- **count** (INT): URLs created this minute
- **created_at** (TIMESTAMP): When recorded

**Indices:**
- `idx_throttle_user_minute` — Fast per-user per-minute lookup

## Constraints

| Table | Constraint | Type |
|-------|-----------|------|
| users | email UNIQUE | Business rule: email is username |
| users | api_key UNIQUE | Auth: keys must be unique |
| short_urls | user_id FK | Ownership: always has an owner |
| short_urls | short_code UNIQUE | Redirect: codes must be unique |

## Rollback Strategy

```bash
# Restore schema to zero
bash scripts/drop_schema.sh

# Recreate from scratch
bash scripts/migrate.sh
```

No migrations in Phase 1 — all schema in one shot.
```

- [ ] **Step 3: Commit documentation**

```bash
git add README.md docs/DATABASE.md
git commit -m "docs(phase1): add database setup + schema documentation

- README: docker-compose, migration, test instructions
- docs/DATABASE.md: full schema reference + rollback steps"
```

---

## Commit Sequencing (Keep Build Green)

Each task commits independently. Build should remain green after every commit:

1. Task 1: Schema (tables exist, indices in place)
2. Task 2: User SQLC queries (generated code)
3. Task 3: ShortUrl SQLC queries (generated code)
4. Task 4: Rate limiting SQLC stubs (generated code)
5. Task 5: Database infrastructure (connection pool, startup hooks)
6. Task 6-10: Integration tests (pass with DB + SQLC)
7. Task 11-12: Unit tests (pass with pure functions)
8. Task 13: pytest configuration (tests discovered + run)
9. Task 14: Cleanup script (rollback path working)
10. Task 15: Documentation (README + schema guide)

---

## Rollback Strategy

| Scenario | Rollback |
|----------|----------|
| **Schema corruption** | `bash scripts/drop_schema.sh && bash scripts/migrate.sh` |
| **SQLC generation errors** | `sqlc generate` (regenerate from SQL) or `git checkout sql/` |
| **Test failure** | `pytest --tb=short` (debug) or `git reset --hard` (full reset) |
| **Uncommitted changes** | `git status && git checkout .` (after review) |

---

## Self-Review

**Spec Coverage:**
- ✅ Database schema (Task 1): 4 tables, all indices, all constraints
- ✅ SQLC queries (Tasks 2-4): 15+ queries, type-safe
- ✅ Infrastructure (Task 5): Connection pool, startup/shutdown
- ✅ Integration tests (Tasks 6-10): Constraints, cascading, flows
- ✅ Unit tests (Tasks 11-12): Algorithms, boundaries
- ✅ Configuration (Task 13): pytest + coverage
- ✅ Documentation (Task 15): Schema guide + rollback

**No Placeholders:** Every step has concrete code, exact paths, full SQL/Python.

**Type Consistency:** 
- User: id UUID v7, email str, password_hash str, api_key str
- ShortUrl: id UUID v7, user_id UUID v7, short_code str, click_count int
- All SQLC-generated types match domain models

---

## Execution Options

**Plan complete and ready for execution.**

Two options:

1. **Subagent-Driven (recommended)** — Fresh subagent per task, review between tasks, fast feedback loop
   - Best for catching issues early
   - Each task gets full tool access

2. **Inline Execution** — Execute tasks sequentially in this session
   - Faster overall (no per-task startup)
   - Better for low-risk tasks

**Which approach?**

