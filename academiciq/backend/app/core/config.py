"""Application configuration via environment variables."""
from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import PostgresDsn, RedisDsn, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # App
    APP_NAME: str = "AcademicIQ"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = False
    SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION_USE_OPENSSL_RAND_HEX_64"
    ALLOWED_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Auth
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_MINUTES: int = 30

    # Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "academiciq"
    POSTGRES_PASSWORD: str = "academiciq_dev"
    POSTGRES_DB: str = "academiciq"
    DATABASE_URL: str | None = None

    @model_validator(mode="after")
    def assemble_db_url(self) -> "Settings":
        if not self.DATABASE_URL:
            self.DATABASE_URL = (
                f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
                f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            )
        return self

    DATABASE_URL_SYNC: str | None = None

    @model_validator(mode="after")
    def assemble_sync_db_url(self) -> "Settings":
        if not self.DATABASE_URL_SYNC:
            self.DATABASE_URL_SYNC = (
                f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
                f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            )
        return self

    # Redis / Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # File storage
    UPLOAD_DIR: str = "/app/uploads"
    MAX_UPLOAD_SIZE_MB: int = 50
    ALLOWED_EXTENSIONS: list[str] = [".pdf"]

    # Rate limiting
    AUTH_RATE_LIMIT: str = "10/minute"
    UPLOAD_RATE_LIMIT: str = "5/minute"
    AI_RATE_LIMIT: str = "20/minute"

    # AI / LLM
    LLM_PROVIDER: Literal["local", "openai", "anthropic"] = "local"
    LLM_BASE_URL: str = "http://localhost:11434"  # Ollama default
    LLM_MODEL: str = "llama3"
    OPENAI_API_KEY: str | None = None
    ANTHROPIC_API_KEY: str | None = None

    # Privacy
    PRIVACY_REGULATION: Literal["DPDP", "FERPA", "GDPR"] = "DPDP"
    DATA_RETENTION_YEARS: int = 7


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
