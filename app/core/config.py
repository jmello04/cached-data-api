from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )

    APP_NAME: str = "Cached Data API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@db:5432/financial_db"
    DATABASE_URL_SYNC: str = "postgresql://postgres:postgres@db:5432/financial_db"

    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""
    REDIS_TTL_DEFAULT: int = 300

    CACHE_KEY_PREFIX: str = "cached_data_api"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
