import pytest
import json
from unittest.mock import patch, AsyncMock, call
import redis.asyncio as redis

from app.memory import service as memory_service
from app.core.config import settings


# --- Test Fixtures ---


@pytest.fixture
def mock_redis_client():
    """
    Provides an asynchronous mock of the Redis client, configured to simulate
    pipeline operations and list range queries for chat history.
    """
    client = AsyncMock(spec=redis.Redis)
    pipeline_mock = AsyncMock(spec=redis.client.Pipeline)
    pipeline_mock.__aenter__.return_value = pipeline_mock
    pipeline_mock.__aexit__.return_value = None
    pipeline_mock.execute = AsyncMock()
    pipeline_mock.rpush = AsyncMock()
    pipeline_mock.ltrim = AsyncMock()
    pipeline_mock.expire = AsyncMock()
    client.pipeline.return_value = pipeline_mock
    client.lrange = AsyncMock()
    return client


# --- Tests for `add_chat_turn` ---


@pytest.mark.asyncio
async def test_add_chat_turn_success(mock_redis_client):
    """
    Verifies the successful storage of a user-bot chat turn into Redis.
    Ensures that RPOP, LTRIM, and EXPIRE commands are called correctly
    within an atomic Redis pipeline.
    """
    session_id = "test-session-123"
    user_msg = "Hello there"
    bot_msg = "General Kenobi"
    history_key = f"{settings.REDIS_HISTORY_KEY_PREFIX}{session_id}"
    user_entry = json.dumps({"type": "user", "message": user_msg})
    bot_entry = json.dumps({"type": "assistant", "message": bot_msg})

    await memory_service.add_chat_turn(session_id, user_msg, bot_msg, mock_redis_client)

    # Assert that Redis commands were called as expected within the pipeline.
    pipeline_mock = mock_redis_client.pipeline.return_value
    pipeline_mock.rpush.assert_has_awaits(
        [call(history_key, user_entry), call(history_key, bot_entry)]
    )
    pipeline_mock.ltrim.assert_awaited_once_with(
        history_key, -settings.REDIS_MAX_HISTORY_LENGTH * 2, -1
    )
    pipeline_mock.expire.assert_awaited_once_with(
        history_key, settings.REDIS_HISTORY_TTL
    )
    pipeline_mock.execute.assert_awaited_once()


@pytest.mark.asyncio
@patch("app.memory.service.logger")
async def test_add_chat_turn_redis_error(mock_logger, mock_redis_client):
    """
    Tests error handling when a `redis.RedisError` occurs during chat turn storage.
    Ensures the error is logged and the function completes gracefully.
    """
    session_id = "test-session-error"
    user_msg = "Ping"
    bot_msg = "Pong"
    test_exception = redis.RedisError("Connection failed")

    # Simulate a Redis error during a pipeline command.
    pipeline_mock = mock_redis_client.pipeline.return_value
    pipeline_mock.rpush.side_effect = test_exception

    await memory_service.add_chat_turn(session_id, user_msg, bot_msg, mock_redis_client)

    # Verify that the error was logged with exception information.
    mock_logger.error.assert_called_once()
    assert "Redis error storing chat history" in mock_logger.error.call_args[0][0]
    assert mock_logger.error.call_args.kwargs["exc_info"] is True


@pytest.mark.asyncio
@patch("app.memory.service.logger")
async def test_add_chat_turn_unexpected_error(mock_logger, mock_redis_client):
    """
    Tests error handling for an unexpected `Exception` during chat turn preparation
    (e.g., JSON serialization failure). Ensures the error is logged.
    """
    session_id = "test-session-unexpected"
    user_msg = "Unexpected"
    bot_msg = "Error"
    test_exception = ValueError("Something else went wrong")

    # Simulate an error during JSON serialization.
    with patch("app.memory.service.json.dumps", side_effect=test_exception):
        await memory_service.add_chat_turn(
            session_id, user_msg, bot_msg, mock_redis_client
        )

    # Verify that the unexpected error was logged.
    mock_logger.error.assert_called_once()
    assert (
        "Unexpected error during Redis history storage"
        in mock_logger.error.call_args[0][0]
    )
    assert mock_logger.error.call_args.kwargs["exc_info"] is True


# --- Tests for `get_chat_history` ---


@pytest.mark.asyncio
async def test_get_chat_history_success(mock_redis_client):
    """
    Verifies the successful retrieval and decoding of chat history from Redis.
    Ensures `lrange` is called with the correct parameters and history is returned.
    """
    session_id = "test-session-get"
    limit = 4
    history_key = f"{settings.REDIS_HISTORY_KEY_PREFIX}{session_id}"
    raw_data = [
        json.dumps({"type": "user", "message": "Older message"}),
        json.dumps({"type": "assistant", "message": "Older reply"}),
        json.dumps({"type": "user", "message": "Newer message"}),
        json.dumps({"type": "assistant", "message": "Newer reply"}),
    ]
    expected_history = [json.loads(entry) for entry in raw_data]

    mock_redis_client.lrange.return_value = raw_data

    history = await memory_service.get_chat_history(
        session_id, mock_redis_client, limit=limit
    )

    mock_redis_client.lrange.assert_awaited_once_with(history_key, -limit, -1)
    assert history == expected_history


@pytest.mark.asyncio
async def test_get_chat_history_empty(mock_redis_client):
    """
    Tests retrieving chat history when no entries exist in Redis for the session ID.
    Ensures an empty list is returned.
    """
    session_id = "test-session-empty"
    limit = 10
    history_key = f"{settings.REDIS_HISTORY_KEY_PREFIX}{session_id}"
    mock_redis_client.lrange.return_value = []

    history = await memory_service.get_chat_history(
        session_id, mock_redis_client, limit=limit
    )

    mock_redis_client.lrange.assert_awaited_once_with(history_key, -limit, -1)
    assert history == []


@pytest.mark.asyncio
@patch("app.memory.service.logger")
async def test_get_chat_history_redis_error(mock_logger, mock_redis_client):
    """
    Tests error handling when a `redis.RedisError` occurs during history retrieval.
    Ensures an empty list is returned and the error is logged.
    """
    session_id = "test-session-get-redis-error"
    limit = 5
    test_exception = redis.RedisError("LRANGE failed")
    mock_redis_client.lrange.side_effect = test_exception

    history = await memory_service.get_chat_history(
        session_id, mock_redis_client, limit=limit
    )

    assert history == []
    mock_logger.error.assert_called_once()
    assert "Redis error loading chat history" in mock_logger.error.call_args[0][0]
    assert mock_logger.error.call_args.kwargs["exc_info"] is True


@pytest.mark.asyncio
@patch("app.memory.service.logger")
async def test_get_chat_history_json_decode_error(mock_logger, mock_redis_client):
    """
    Tests error handling when a `JSONDecodeError` occurs while parsing history entries.
    Ensures an empty list is returned and the decoding error is logged.
    """
    session_id = "test-session-get-json-error"
    limit = 2
    history_key = f"{settings.REDIS_HISTORY_KEY_PREFIX}{session_id}"
    # Simulate Redis returning an invalid JSON entry.
    raw_data = ['{"type": "user", "message": "Valid"}', "this is not json"]
    mock_redis_client.lrange.return_value = raw_data

    history = await memory_service.get_chat_history(
        session_id, mock_redis_client, limit=limit
    )

    assert history == []
    mock_redis_client.lrange.assert_awaited_once_with(history_key, -limit, -1)
    mock_logger.error.assert_called_once()
    assert (
        "Error decoding history entry from Redis" in mock_logger.error.call_args[0][0]
    )
    assert mock_logger.error.call_args.kwargs["exc_info"] is True


@pytest.mark.asyncio
@patch("app.memory.service.logger")
async def test_get_chat_history_unexpected_error(mock_logger, mock_redis_client):
    """
    Tests error handling for any unexpected `Exception` during history retrieval.
    Ensures an empty list is returned and the error is logged.
    """
    session_id = "test-session-get-unexpected-error"
    limit = 3
    test_exception = TypeError("Something unexpected")
    # Simulate an unexpected error during the `lrange` call.
    mock_redis_client.lrange.side_effect = test_exception

    history = await memory_service.get_chat_history(
        session_id, mock_redis_client, limit=limit
    )

    assert history == []
    mock_logger.error.assert_called_once()
    assert "Unexpected error loading chat history" in mock_logger.error.call_args[0][0]
    assert mock_logger.error.call_args.kwargs["exc_info"] is True