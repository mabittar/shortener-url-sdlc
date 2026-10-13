"""User domain model (type-safe dataclasses)."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class User:
    """User entity with credentials and authentication metadata."""

    id: UUID
    email: str
    password_hash: str
    api_key: str
    name: str | None = None
    email_verified: bool = False
    password_reset_token: str | None = None
    password_reset_expires: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    is_active: bool = True


@dataclass
class UserCreated:
    """Result of user creation."""

    id: UUID
    email: str
    api_key: str
    created_at: datetime


@dataclass
class UserAuthLookup:
    """User data for authentication (login)."""

    id: UUID
    email: str
    password_hash: str
    api_key: str
    email_verified: bool
    is_active: bool


@dataclass
class UserApiKeyLookup:
    """User data for API key validation."""

    id: UUID
    email: str
    api_key: str
    is_active: bool


@dataclass
class UserProfile:
    """Public user profile."""

    id: UUID
    email: str
    name: str | None
    api_key: str
    created_at: datetime


@dataclass
class PasswordResetToken:
    """Password reset state."""

    user_id: UUID
    token: str
    expires_at: datetime
