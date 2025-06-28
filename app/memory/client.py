import redis.asyncio as redis
from fastapi import Request, HTTPException, status
import logging


logger = logging.getLogger(__name__)


async def get_redis(request: Request) -> redis.Redis:
    """
    FastAPI dependency function to get the Redis client instance
    stored in app.state by the lifespan manager.
    Raises 503 Service Unavailable if Redis is not configured/available.
    """
    redis_client = getattr(request.app.state, "redis_client", None)
    if redis_client is None:
        logger.error("Redis client not found in app.state.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Redis service not available or not configured correctly.",
        )
    return redis_client
