"""Application configuration."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/shortener_url"

    # Application
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_TITLE: str = "URL Shortener API"
    API_VERSION: str = "0.1.0"

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8000"]

    # Redis
    REDIS_URL: str | None = None

    # Secrets
    SECRET_KEY: str = "your-secret-key-here-change-in-production"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
