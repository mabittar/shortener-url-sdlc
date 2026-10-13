"""ShortUrl repository (SQLC queries executed)."""

from uuid import UUID
import asyncpg
from datetime import datetime

from src.models.shorturl import (
    ShortUrl,
    ShortUrlCreated,
    ShortUrlRedirect,
    ShortUrlProfile,
)


class ShortUrlRepository:
    """Data access layer for short URLs."""

    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def create_shorturl(
        self, user_id: UUID, original_url: str, short_code: str
    ) -> ShortUrlCreated:
        """Create a new short URL. Returns id, short_code, original_url, created_at."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO short_urls (user_id, original_url, short_code, expires_at, created_at, updated_at)
                VALUES ($1, $2, $3, NOW() + INTERVAL '1 month', NOW(), NOW())
                RETURNING id, short_code, original_url, created_at
                """,
                user_id,
                original_url,
                short_code,
            )
            return ShortUrlCreated(
                id=row["id"],
                short_code=row["short_code"],
                original_url=row["original_url"],
                created_at=row["created_at"],
            )

    async def get_shorturl_by_code(self, short_code: str) -> ShortUrlRedirect | None:
        """Get short URL by code (for redirects). Returns full data if active & not expired."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, user_id, original_url, short_code, click_count, created_at, expires_at, is_active
                FROM short_urls
                WHERE short_code = $1
                  AND is_active = true
                  AND (expires_at IS NULL OR expires_at > NOW())
                """,
                short_code,
            )
            if not row:
                return None
            return ShortUrlRedirect(
                id=row["id"],
                user_id=row["user_id"],
                original_url=row["original_url"],
                short_code=row["short_code"],
                click_count=row["click_count"],
                created_at=row["created_at"],
                expires_at=row["expires_at"],
                is_active=row["is_active"],
            )

    async def get_shorturl_by_id(self, shorturl_id: UUID) -> ShortUrl | None:
        """Get short URL by ID. Returns full entity."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, user_id, original_url, short_code, click_count, created_at, expires_at, is_active
                FROM short_urls
                WHERE id = $1 AND is_active = true
                """,
                shorturl_id,
            )
            if not row:
                return None
            return ShortUrl(
                id=row["id"],
                user_id=row["user_id"],
                original_url=row["original_url"],
                short_code=row["short_code"],
                click_count=row["click_count"],
                created_at=row["created_at"],
                expires_at=row["expires_at"],
                is_active=row["is_active"],
            )

    async def increment_click_count(self, shorturl_id: UUID) -> None:
        """Increment click count for a short URL."""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE short_urls
                SET click_count = click_count + 1, updated_at = NOW()
                WHERE id = $1
                """,
                shorturl_id,
            )

    async def soft_delete_shorturl(self, shorturl_id: UUID, user_id: UUID) -> bool:
        """Soft delete a short URL (user must own it). Returns True if deleted."""
        async with self.pool.acquire() as conn:
            result = await conn.execute(
                """
                UPDATE short_urls
                SET is_active = false, updated_at = NOW()
                WHERE id = $1 AND user_id = $2
                """,
                shorturl_id,
                user_id,
            )
            # Returns "UPDATE N" where N is rows affected
            return result != "UPDATE 0"

    async def get_user_shorturls(
        self, user_id: UUID, limit: int = 50, offset: int = 0
    ) -> list[ShortUrlProfile]:
        """Get user's short URLs with pagination."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, short_code, original_url, click_count, created_at, expires_at, is_active
                FROM short_urls
                WHERE user_id = $1 AND is_active = true
                ORDER BY created_at DESC
                LIMIT $2 OFFSET $3
                """,
                user_id,
                limit,
                offset,
            )
            return [
                ShortUrlProfile(
                    id=row["id"],
                    short_code=row["short_code"],
                    original_url=row["original_url"],
                    click_count=row["click_count"],
                    created_at=row["created_at"],
                    expires_at=row["expires_at"],
                    is_active=row["is_active"],
                )
                for row in rows
            ]

    async def get_all_user_shorturls(self, user_id: UUID) -> list[ShortUrlProfile]:
        """Get all user's short URLs (no pagination)."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, short_code, original_url, click_count, created_at, expires_at, is_active
                FROM short_urls
                WHERE user_id = $1 AND is_active = true
                ORDER BY created_at DESC
                """,
                user_id,
            )
            return [
                ShortUrlProfile(
                    id=row["id"],
                    short_code=row["short_code"],
                    original_url=row["original_url"],
                    click_count=row["click_count"],
                    created_at=row["created_at"],
                    expires_at=row["expires_at"],
                    is_active=row["is_active"],
                )
                for row in rows
            ]

    async def count_user_shorturls(self, user_id: UUID) -> int:
        """Count user's active short URLs."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchval(
                """
                SELECT COUNT(*) as count
                FROM short_urls
                WHERE user_id = $1 AND is_active = true
                """,
                user_id,
            )
            return row or 0
