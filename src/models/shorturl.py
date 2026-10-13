"""ShortUrl domain model (type-safe dataclasses)."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class ShortUrl:
    """Short URL entity with ownership and click tracking."""

    id: UUID
    user_id: UUID
    original_url: str
    short_code: str
    click_count: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None
    expires_at: datetime | None = None
    is_active: bool = True


@dataclass
class ShortUrlCreated:
    """Result of short URL creation."""

    id: UUID
    short_code: str
    original_url: str
    created_at: datetime


@dataclass
class ShortUrlRedirect:
    """Short URL for redirect (GET /{short_code})."""

    id: UUID
    user_id: UUID
    original_url: str
    short_code: str
    click_count: int
    created_at: datetime
    expires_at: datetime | None
    is_active: bool


@dataclass
class ShortUrlProfile:
    """Short URL profile for user listing."""

    id: UUID
    short_code: str
    original_url: str
    click_count: int
    created_at: datetime
    expires_at: datetime | None
    is_active: bool
