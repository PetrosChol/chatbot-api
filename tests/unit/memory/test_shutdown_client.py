import pytest
from unittest.mock import AsyncMock, patch
import redis.asyncio as redis

# Module to test
from app.memory.shutdown_client import shutdown_redis_client


@pytest.mark.asyncio
@patch("app.memory.shutdown_client.logger")
async def test_shutdown_redis_client_success(mock_logger):
    """Test successful Redis client shutdown."""
    mock_client = AsyncMock(spec=redis.Redis)
    mock_client.aclose = AsyncMock()  # Mock the aclose method specifically

    await shutdown_redis_client(mock_client)

    mock_client.aclose.assert_awaited_once()
    mock_logger.info.assert_any_call("Closing Redis client connection pool...")
    mock_logger.info.assert_any_call("Redis client connection pool closed.")
    mock_logger.error.assert_not_called()


@pytest.mark.asyncio
@patch("app.memory.shutdown_client.logger")
async def test_shutdown_redis_client_none(mock_logger):
    """Test shutdown when the client instance is None."""
    await shutdown_redis_client(None)

    mock_logger.info.assert_called_once_with("No Redis client instance found to close.")
    mock_logger.error.assert_not_called()


@pytest.mark.asyncio
@patch("app.memory.shutdown_client.logger")
async def test_shutdown_redis_client_aclose_fails(mock_logger):
    """Test shutdown when client.aclose() raises an exception."""
    mock_client = AsyncMock(spec=redis.Redis)
    test_exception = ConnectionError("Failed to close connection")
    mock_client.aclose = AsyncMock(side_effect=test_exception)

    await shutdown_redis_client(mock_client)

    mock_client.aclose.assert_awaited_once()
    mock_logger.info.assert_called_once_with("Closing Redis client connection pool...")
    mock_logger.error.assert_called_once_with(
        f"Error closing Redis client: {test_exception}", exc_info=True
    )
