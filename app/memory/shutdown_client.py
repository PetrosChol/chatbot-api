import redis.asyncio as redis
import logging


logger = logging.getLogger(__name__)


async def shutdown_redis_client(client: redis.Redis | None):
    """
    Closes the Redis client's connection pool gracefully.
    Called during application shutdown (lifespan).
    """
    if client:
        logger.info("Closing Redis client connection pool...")
        try:
            await client.aclose()
            logger.info("Redis client connection pool closed.")
        except Exception as e:
            logger.error(f"Error closing Redis client: {e}", exc_info=True)
    else:
        logger.info("No Redis client instance found to close.")
