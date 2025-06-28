from typing import List, Optional
from functools import lru_cache
from pydantic import PostgresDsn, RedisDsn, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
import logging 

logger = logging.getLogger(__name__) 


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    # --- Core Application Settings ---
    APP_NAME: str = "ThessalonikiGuide.gr Chat App"
    APP_VERSION: str = "0.1.0"
    DESCRIPTION: str = "API for processing chat messages."
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"  # Default log level

    # --- API Settings ---
    API_V1_STR: str = "/api/v1"

    # --- Model Name ---
    MODEL_NAME: str = "models/gemini-2.0-flash"

    # --- Database Settings ---
    DATABASE_URL: PostgresDsn | str = None
    DO_DB_SSL_CERT_PATH: Optional[str] = None
    DO_DB_SSL_CERT_CONTENT: Optional[str] = None

    # --- Pool Settings ---
    SQLALCHEMY_POOL_SIZE: Optional[int] = 5
    SQLALCHEMY_MAX_OVERFLOW: Optional[int] = 2
    SQLALCHEMY_POOL_RECYCLE: Optional[int] = 1800

    # --- Redis Settings ---
    REDIS_URL: RedisDsn = "redis://localhost:6379/0"
    REDIS_HISTORY_KEY_PREFIX: str = (
        "chat_history:"  # Prefix for Redis keys storing chat history
    )
    REDIS_HISTORY_TTL: int = (
        60 * 60 * 24
    )  # 24 hours in seconds for chat history expiration
    REDIS_MAX_HISTORY_LENGTH: int = (
        50  # Max number of conversation *turns* (user + assistant) to store
    )
    MAX_MESSAGES_PER_MINUTE: int = 5  # Rate limit for chat messages per minute per IP

    # --- CORS Settings ---
    ALLOWED_CORS_ORIGINS: List[str] = ["http://localhost:8000"]

    # --- Health Check Settings ---
    HEALTH_CHECK_TIMEOUT_S: float = 1.0  # Timeout in seconds for health checks

    # --- Search Settings ---
    FUZZY_THRESHOLD: float = (
        0.1  # Default threshold for fuzzy string matching (e.g., pg_trgm similarity)
    )

    # --- Security Settings ---
    GEMINI_API_KEY: SecretStr | None = None

    # --- Pydantic Settings Configuration ---
    model_config = SettingsConfigDict(
        env_file=".env",  # Load .env file from the calculated path
        env_file_encoding="utf-8",  # Specify encoding
        case_sensitive=False,  # Environment variable names are case-insensitive
        extra="ignore",  # Ignore extra fields from env variables ('forbid' to raise error)
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
if settings.DO_DB_SSL_CERT_PATH:
    logger.info(f"DO_DB_SSL_CERT_PATH is configured: '{settings.DO_DB_SSL_CERT_PATH}'")
else:
    logger.info("DO_DB_SSL_CERT_PATH is not configured.")
