import redis.asyncio as redis
import json
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


async def add_chat_turn(
    session_id: str, user_message: str, bot_message: str, redis_client: redis.Redis
):
    """
    Adds a user message and bot reply turn to the chat history in Redis.
    Also trims the history based on settings.REDIS_MAX_HISTORY_LENGTH (number of turns)
    and sets an expiration time based on settings.REDIS_HISTORY_TTL.
    """

    history_key = f"{settings.REDIS_HISTORY_KEY_PREFIX}{session_id}"
    try:
        user_entry = json.dumps({"type": "user", "message": user_message})
        bot_entry = json.dumps({"type": "assistant", "message": bot_message})

        async with redis_client.pipeline(transaction=True) as pipe:
            # Push user message first, then assistant message to the right (end) of the list
            await pipe.rpush(history_key, user_entry)
            await pipe.rpush(history_key, bot_entry)

            # Trim the list to keep only the latest settings.REDIS_MAX_HISTORY_LENGTH * 2 entries
            # (keep the items from index -N to -1, where N is the total number of items to keep)
            await pipe.ltrim(history_key, -settings.REDIS_MAX_HISTORY_LENGTH * 2, -1)

            # Set expiration time for the history key
            await pipe.expire(history_key, settings.REDIS_HISTORY_TTL)

            await pipe.execute()

        logger.info(f"Stored history turn for session {session_id}")

    except redis.RedisError as e:
        logger.error(
            f"Redis error storing chat history for session {session_id}: {e}",
            exc_info=True,
        ) 

    except Exception as e:
        logger.error(
            f"Unexpected error during Redis history storage for session {session_id}: {e}",
            exc_info=True,
        )


async def get_chat_history(
    session_id: str,
    redis_client: redis.Redis,
    limit: int = 10,  # Default number of *messages* (not turns) to retrieve
):
    """
    Loads the most recent chat history messages from Redis for a given session.
    Returns messages newest-first.

    Args:
        session_id: The unique identifier for the session.
        redis_client: The asynchronous Redis client instance.
        limit: The maximum number of individual messages to retrieve.

    Returns:
        A list of message dictionaries, ordered newest to oldest, or an empty list on error.
    """

    history_key = f"{settings.REDIS_HISTORY_KEY_PREFIX}{session_id}"
    try:
        # Retrieve the latest 'limit' messages (newest are at the end due to rpush)
        # lrange(key, -limit, -1) gets the last 'limit' elements (newest first)
        raw_history = await redis_client.lrange(history_key, -limit, -1)
        # The result from lrange with negative indices is newest-to-oldest,
        # matching the desired "newest-first" order.
        history = [json.loads(entry) for entry in raw_history]

        return history

    except redis.RedisError as e:
        logger.error(
            f"Redis error loading chat history for session {session_id}: {e}",
            exc_info=True,
        )
        return []
    except json.JSONDecodeError as e:
        logger.error(
            f"Error decoding history entry from Redis for session {session_id}: {e}",
            exc_info=True,
        )
        return []
    except Exception as e:
        logger.error(
            f"Unexpected error loading chat history for session {session_id}: {e}",
            exc_info=True,
        ) 
        return []
