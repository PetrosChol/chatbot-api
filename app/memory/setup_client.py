import redis.asyncio as redis
import logging
from urllib.parse import urlparse, urlunparse
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


def _mask_redis_url_password(redis_url_str: Optional[str]) -> str:
    """Masks the password in a Redis URL string."""
    if not redis_url_str:
        return "URL not provided"
    try:
        parsed_url = urlparse(redis_url_str)
        if parsed_url.password:
            netloc_parts = parsed_url.netloc.split("@", 1)
            if ":" in netloc_parts[0]:
                user_part = netloc_parts[0].split(":", 1)[0]
                new_netloc = f"{user_part}:********"
                if len(netloc_parts) > 1:
                    new_netloc += f"@{netloc_parts[1]}"
                parsed_url = parsed_url._replace(netloc=new_netloc)
        return urlunparse(parsed_url)
    except Exception:
        return "Error parsing URL for masking"


async def setup_redis_client() -> redis.Redis | None:
    """
    Creates and returns an async Redis client instance, checking the connection.
    Returns None if REDIS_URL is not configured or connection fails.
    Called during application startup (lifespan).
    """
    if not settings.REDIS_URL:
        logger.warning("REDIS_URL not configured. Skipping Redis client creation.")
        return None

    masked_redis_url = _mask_redis_url_password(str(settings.REDIS_URL))
    logger.debug(
        f"Creating Redis client for REDIS URL (details masked): {masked_redis_url}"
    )
    try:
        client = redis.Redis.from_url(
            str(settings.REDIS_URL), encoding="utf-8", decode_responses=True
        )
        await client.ping()
        logger.info("Successfully connected to Redis and ping successful.")
        return client
    except Exception as e:
        logger.error(
            f"Error connecting to Redis or ping failed: {e}",
            exc_info=True,
        )
        return None
