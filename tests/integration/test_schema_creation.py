"""Integration tests for PostgreSQL schema creation and constraints."""

import pytest
import asyncpg
from src.shortener_url.config import settings


@pytest.mark.asyncio
async def test_users_table_exists_with_uuid_v7_pk():
    """Test users table created with UUID v7 primary key."""
    pool = await asyncpg.create_pool(settings.DATABASE_URL)
    async with pool.acquire() as conn:
        # Check table exists
        result = await conn.fetchval(
            "SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name='users')"
        )
        assert result is True

        # Check UUID v7 PK column
        result = await conn.fetchval(
            "SELECT data_type FROM information_schema.columns WHERE table_name='users' AND column_name='id'"
        )
        assert result == "uuid"


@pytest.mark.asyncio
async def test_users_email_unique_constraint():
    """Test email uniqueness constraint on users table."""
    pool = await asyncpg.create_pool(settings.DATABASE_URL)
    async with pool.acquire() as conn:
        result = await conn.fetchval(
            """
            SELECT EXISTS(
                SELECT 1 FROM information_schema.table_constraints
                WHERE table_name='users' AND constraint_type='UNIQUE'
                AND constraint_name LIKE '%email%'
            )
            """
        )
        assert result is True


@pytest.mark.asyncio
async def test_users_api_key_unique_constraint():
    """Test api_key uniqueness constraint on users table."""
    pool = await asyncpg.create_pool(settings.DATABASE_URL)
    async with pool.acquire() as conn:
        result = await conn.fetchval(
            """
            SELECT EXISTS(
                SELECT 1 FROM information_schema.table_constraints
                WHERE table_name='users' AND constraint_type='UNIQUE'
                AND constraint_name LIKE '%api_key%'
            )
            """
        )
        assert result is True


@pytest.mark.asyncio
async def test_short_urls_table_exists():
    """Test short_urls table created with required columns."""
    pool = await asyncpg.create_pool(settings.DATABASE_URL)
    async with pool.acquire() as conn:
        result = await conn.fetchval(
            "SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name='short_urls')"
        )
        assert result is True


@pytest.mark.asyncio
async def test_short_urls_short_code_unique_constraint():
    """Test short_code uniqueness constraint on short_urls table."""
    pool = await asyncpg.create_pool(settings.DATABASE_URL)
    async with pool.acquire() as conn:
        result = await conn.fetchval(
            """
            SELECT EXISTS(
                SELECT 1 FROM information_schema.table_constraints
                WHERE table_name='short_urls' AND constraint_type='UNIQUE'
                AND constraint_name LIKE '%short_code%'
            )
            """
        )
        assert result is True


@pytest.mark.asyncio
async def test_short_urls_user_id_fk_cascade():
    """Test user_id foreign key with CASCADE delete."""
    pool = await asyncpg.create_pool(settings.DATABASE_URL)
    async with pool.acquire() as conn:
        result = await conn.fetchval(
            """
            SELECT EXISTS(
                SELECT 1 FROM information_schema.referential_constraints
                WHERE table_name='short_urls'
                AND constraint_name LIKE '%user_id%'
                AND delete_rule='CASCADE'
            )
            """
        )
        assert result is True


@pytest.mark.asyncio
async def test_failed_login_attempts_table_exists():
    """Test failed_login_attempts table created."""
    pool = await asyncpg.create_pool(settings.DATABASE_URL)
    async with pool.acquire() as conn:
        result = await conn.fetchval(
            "SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name='failed_login_attempts')"
        )
        assert result is True


@pytest.mark.asyncio
async def test_url_creation_throttle_table_exists():
    """Test url_creation_throttle table created."""
    pool = await asyncpg.create_pool(settings.DATABASE_URL)
    async with pool.acquire() as conn:
        result = await conn.fetchval(
            "SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name='url_creation_throttle')"
        )
        assert result is True


@pytest.mark.asyncio
async def test_all_required_indices_created():
    """Test all performance-critical indices created."""
    pool = await asyncpg.create_pool(settings.DATABASE_URL)
    async with pool.acquire() as conn:
        required_indices = [
            "idx_users_email",
            "idx_users_api_key",
            "idx_short_urls_short_code",
            "idx_short_urls_user_id",
            "idx_short_urls_is_active",
            "idx_failed_attempts_email",
            "idx_failed_attempts_created_at",
            "idx_throttle_user_minute",
        ]

        for idx_name in required_indices:
            result = await conn.fetchval(
                f"SELECT EXISTS(SELECT 1 FROM pg_indexes WHERE indexname='{idx_name}')"
            )
            assert result is True, f"Index {idx_name} not found"
