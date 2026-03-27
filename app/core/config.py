"""Application settings loaded from environment variables via pydantic-settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralised configuration for the Cached Data API.

    All fields are populated from environment variables (or a ``.env`` file).
    Values are validated and type-coerced automatically by pydantic-settings.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )

    # ── Application ───────────────────────────────────────────────────────────
    APP_NAME: str = "Cached Data API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # ── PostgreSQL ────────────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/financial_db"
    DATABASE_URL_SYNC: str = "postgresql://postgres:postgres@localhost:5432/financial_db"

    # ── Redis ─────────────────────────────────────────────────────────────────
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""
    REDIS_TTL_DEFAULT: int = 300

    # ── Cache ─────────────────────────────────────────────────────────────────
    CACHE_KEY_PREFIX: str = "cached_data_api"


@lru_cache()
def get_settings() -> Settings:
    """Return the singleton Settings instance, loaded once and cached.

    Returns:
        Application-wide settings object.
    """
    return Settings()


settings = get_settings()
