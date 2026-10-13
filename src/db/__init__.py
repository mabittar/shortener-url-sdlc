"""Database layer initialization and connection management."""

import asyncpg
from src.db.user_repo import UserRepository
from src.db.shorturl_repo import ShortUrlRepository
from src.db.ratelimit_repo import RateLimitRepository


class DatabaseManager:
    """Manages database connection pool and repositories."""

    def __init__(self, database_url: str):
        self.database_url = database_url
        self.pool: asyncpg.Pool | None = None
        self.users: UserRepository | None = None
        self.shorturls: ShortUrlRepository | None = None
        self.ratelimit: RateLimitRepository | None = None

    async def connect(self) -> None:
        """Initialize connection pool and repositories."""
        self.pool = await asyncpg.create_pool(
            self.database_url,
            min_size=5,
            max_size=20,
            command_timeout=60,
        )
        self.users = UserRepository(self.pool)
        self.shorturls = ShortUrlRepository(self.pool)
        self.ratelimit = RateLimitRepository(self.pool)

    async def disconnect(self) -> None:
        """Close connection pool."""
        if self.pool:
            await self.pool.close()
            self.pool = None

    async def health_check(self) -> bool:
        """Check database connectivity."""
        if not self.pool:
            return False
        try:
            async with self.pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            return True
        except Exception:
            return False


# Global database instance
_db: DatabaseManager | None = None


def get_db() -> DatabaseManager:
    """Get global database manager instance."""
    if _db is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _db


async def init_db(database_url: str) -> DatabaseManager:
    """Initialize global database manager."""
    global _db
    _db = DatabaseManager(database_url)
    await _db.connect()
    return _db


async def close_db() -> None:
    """Close global database manager."""
    global _db
    if _db:
        await _db.disconnect()
        _db = None
