"""
config.py --> Central Configuration using Pydantic Settings
    - Reads from .env file automatically
    - Type-validates every variable at startup
    - Crashes immediately if a required variable is missing
"""

from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic.v1 import BaseSettings
from pydantic_settings import SettingsConfigDict


class Settings(BaseSettings):
    """
    All environment variables are declared here with types.
    Pydantic will:
        1. Read from .env file
        2. Override with actual environment variables if any
        3. Validate types
        4. Raise clear erros for missing required fields
    """

    # ── App ───────────────────────────────────────────
    APP_NAME: str = Field(default="AI Email Generator")
    APP_VERSION: str = Field(default="1.0.0")
    APP_ENV: str = Field(default="development")
    DEBUG: bool = Field(default=False)
    PORT: int = Field(default=8000)

    # ── Groq LLM ─────────────────────────────────────
    GROQ_API_KEY: str = Field(default="")
    GROQ_MODEL: str = Field(default="llama-3.1-8b-instant")

    # ── PostgreSQL ────────────────────────────────────
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://user:password@localhost:5432/email_generator"
    )

    # ── Redis ──────────────────────────────────────────────
    REDIS_URL: str = Field(default="redis://localhost:6379/0")

    # ── Rate Limiting ──────────────────────────────────────
    RATE_LIMIT_PER_MINUTE: int = Field(default=10)

    model_config = (SettingsConfigDict)(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    """
    Returns a CACHED singleton instance of Settings.

    WHY lru_cache?
        - Settings are read once at startup, not on every request
        - .env file is parsed only once -> faster performance
        - All parts of the app share the same Settings object
    """
    return Settings()


settings = get_settings()
