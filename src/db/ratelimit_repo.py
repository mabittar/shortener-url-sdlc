"""Rate limiting repository (Redis counter + PostgreSQL audit)."""

from uuid import UUID
import asyncpg
from datetime import datetime


class RateLimitRepository:
    """Data access layer for rate limiting audit logs."""

    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    # ========================================================================
    # URL Creation Throttle (1 URL per minute per user)
    # ========================================================================

    async def record_url_creation(self, user_id: UUID) -> None:
        """Record a URL creation for throttle audit (per-minute bucket)."""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO url_creation_throttle (user_id, minute_bucket, count, created_at)
                VALUES ($1, DATE_TRUNC('minute', NOW()), 1, NOW())
                """,
                user_id,
            )

    async def get_url_creation_count_this_minute(self, user_id: UUID) -> int:
        """Get URLs created by user this minute (for audit/analytics)."""
        async with self.pool.acquire() as conn:
            count = await conn.fetchval(
                """
                SELECT COUNT(*) as count
                FROM url_creation_throttle
                WHERE user_id = $1
                  AND minute_bucket = DATE_TRUNC('minute', NOW())
                """,
                user_id,
            )
            return count or 0

    async def cleanup_url_creation_throttle(self) -> int:
        """Delete old throttle records (older than 1 minute). Returns rows deleted."""
        async with self.pool.acquire() as conn:
            result = await conn.execute(
                """
                DELETE FROM url_creation_throttle
                WHERE minute_bucket < NOW() - INTERVAL '1 minute'
                """
            )
            # Returns "DELETE N" where N is rows deleted
            return int(result.split()[-1])

    # ========================================================================
    # Login Rate Limiting (3 failed attempts → 5 min lockout)
    # ========================================================================

    async def set_login_lockout(self, email: str) -> None:
        """Set 5-minute lockout on email after failed attempts."""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE failed_login_attempts
                SET locked_until = NOW() + INTERVAL '5 minutes'
                WHERE email = $1
                """,
                email,
            )

    async def is_login_locked(self, email: str) -> bool:
        """Check if email is currently locked out."""
        async with self.pool.acquire() as conn:
            is_locked = await conn.fetchval(
                """
                SELECT locked_until > NOW() as is_locked
                FROM failed_login_attempts
                WHERE email = $1
                """,
                email,
            )
            return is_locked or False

    async def reset_login_attempts(self, email: str) -> None:
        """Clear failed attempts after successful login."""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE failed_login_attempts
                SET attempt_count = 0, locked_until = NULL, updated_at = NOW()
                WHERE email = $1
                """,
                email,
            )

    async def get_login_attempts_info(
        self, email: str
    ) -> tuple[int, datetime | None] | None:
        """Get current attempt count and lockout time. Returns (count, locked_until)."""
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
