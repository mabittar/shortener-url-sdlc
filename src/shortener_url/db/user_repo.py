"""User repository (SQLC queries executed)."""

from uuid import UUID
import asyncpg
from datetime import datetime

from src.shortener_url.models.user import (
    User,
    UserCreated,
    UserAuthLookup,
    UserApiKeyLookup,
    UserProfile,
)


class UserRepository:
    """Data access layer for users."""

    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def create_user(
        self, email: str, password_hash: str, api_key: str, name: str | None = None
    ) -> UserCreated:
        """Create a new user. Returns id, email, api_key, created_at."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO users (email, password_hash, api_key, name, created_at, updated_at)
                VALUES ($1, $2, $3, $4, NOW(), NOW())
                RETURNING id, email, api_key, created_at
                """,
                email,
                password_hash,
                api_key,
                name,
            )
            return UserCreated(
                id=row["id"],
                email=row["email"],
                api_key=row["api_key"],
                created_at=row["created_at"],
            )

    async def get_user_by_email(self, email: str) -> UserAuthLookup | None:
        """Get user by email (for login). Returns auth-relevant fields."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, email, password_hash, api_key, email_verified, is_active
                FROM users
                WHERE email = $1 AND is_active = true
                """,
                email,
            )
            if not row:
                return None
            return UserAuthLookup(
                id=row["id"],
                email=row["email"],
                password_hash=row["password_hash"],
                api_key=row["api_key"],
                email_verified=row["email_verified"],
                is_active=row["is_active"],
            )

    async def get_user_by_api_key(self, api_key: str) -> UserApiKeyLookup | None:
        """Get user by API key. Returns minimal auth fields."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, email, api_key, is_active
                FROM users
                WHERE api_key = $1 AND is_active = true
                """,
                api_key,
            )
            if not row:
                return None
            return UserApiKeyLookup(
                id=row["id"],
                email=row["email"],
                api_key=row["api_key"],
                is_active=row["is_active"],
            )

    async def get_user_by_id(self, user_id: UUID) -> UserProfile | None:
        """Get user by ID. Returns profile data."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, email, name, api_key, created_at
                FROM users
                WHERE id = $1 AND is_active = true
                """,
                user_id,
            )
            if not row:
                return None
            return UserProfile(
                id=row["id"],
                email=row["email"],
                name=row["name"],
                api_key=row["api_key"],
                created_at=row["created_at"],
            )

    async def update_user_password(self, user_id: UUID, password_hash: str) -> None:
        """Update user password hash."""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE users
                SET password_hash = $1, updated_at = NOW()
                WHERE id = $2
                """,
                password_hash,
                user_id,
            )

    async def set_password_reset_token(
        self, user_id: UUID, token: str
    ) -> None:
        """Set password reset token with 15-min TTL."""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE users
                SET password_reset_token = $1,
                    password_reset_expires = NOW() + INTERVAL '15 minutes'
                WHERE id = $2
                """,
                token,
                user_id,
            )

    async def get_user_by_password_reset_token(
        self, token: str
    ) -> tuple[UUID, str] | None:
        """Get user by password reset token (if not expired). Returns (id, email)."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, email
                FROM users
                WHERE password_reset_token = $1
                  AND password_reset_expires > NOW()
                  AND is_active = true
                """,
                token,
            )
            if not row:
                return None
            return (row["id"], row["email"])

    async def clear_password_reset_token(self, user_id: UUID) -> None:
        """Clear password reset token after successful reset."""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE users
                SET password_reset_token = NULL, password_reset_expires = NULL
                WHERE id = $1
                """,
                user_id,
            )

    async def record_failed_login(self, email: str) -> None:
        """Record a failed login attempt for rate limiting."""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO failed_login_attempts (email, attempt_count, created_at, updated_at)
                VALUES ($1, 1, NOW(), NOW())
                ON CONFLICT (email) DO UPDATE
                SET attempt_count = failed_login_attempts.attempt_count + 1,
                    updated_at = NOW()
                """,
                email,
            )

    async def get_failed_login_count(
        self, email: str
    ) -> tuple[int, datetime | None] | None:
        """Get failed login count and lockout time. Returns (count, locked_until)."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT attempt_count, locked_until
                FROM failed_login_attempts
                WHERE email = $1
                """,
                email,
            )
            if not row:
                return None
            return (row["attempt_count"], row["locked_until"])

    async def clear_failed_logins(self, email: str) -> None:
        """Clear failed login attempts after successful login."""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                DELETE FROM failed_login_attempts
                WHERE email = $1
                """,
                email,
            )
