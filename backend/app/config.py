from __future__ import annotations

from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database
    database_url: str = Field(
        ...,
        description="PostgreSQL database URL (format: postgresql+asyncpg://user:pass@host:port/dbname)",
    )
    test_database_url: Optional[str] = Field(
        default=None,
        description=(
            "Optional dedicated PostgreSQL URL for pytest "
            "(format: postgresql+asyncpg://user:pass@host:port/test_db)"
        ),
    )

    # External APIs
    rentcast_api_key: Optional[str] = Field(
        default=None,
        description="RentCast API key for property data lookup",
    )
    mashvisor_api_key: Optional[str] = Field(
        default=None,
        description="Mashvisor API key for market analytics (Phase 3)",
    )
    anthropic_api_key: Optional[str] = Field(
        default=None,
        description="Anthropic Claude API key for chatbot (Phase 2)",
    )

    # Authentication
    jwt_secret_key: str = Field(
        ...,
        description="Secret key for JWT token signing (generate with: openssl rand -hex 32)",
    )
    jwt_algorithm: str = Field(
        default="HS256",
        description="JWT signing algorithm",
    )
    jwt_access_token_expire_minutes: int = Field(
        default=30,
        description="Access token expiration time in minutes",
    )
    jwt_refresh_token_expire_days: int = Field(
        default=7,
        description="Refresh token expiration time in days",
    )

    # Caching
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL",
    )

    # Monitoring
    sentry_dsn_backend: Optional[str] = Field(
        default=None,
        description="Sentry DSN for backend error tracking",
    )
    sentry_dsn_frontend: Optional[str] = Field(
        default=None,
        description="Sentry DSN for frontend error tracking",
    )

    # Application
    environment: str = Field(
        default="development",
        description="Application environment (development, staging, production)",
    )
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:5173",
        description="Comma-separated list of allowed CORS origins",
    )

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins string into a list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == "development"


settings = Settings()
