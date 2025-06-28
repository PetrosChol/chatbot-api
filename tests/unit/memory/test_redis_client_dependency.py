import pytest
from unittest.mock import MagicMock, AsyncMock
from fastapi import Request, HTTPException, status
import redis.asyncio as redis

# Module to test
from app.memory.client import get_redis


@pytest.mark.asyncio
async def test_get_redis_success():
    """Test successfully getting the Redis client from app state."""
    mock_request = MagicMock(spec=Request)
    mock_redis_instance = AsyncMock(spec=redis.Redis)
    mock_request.app.state.redis_client = mock_redis_instance

    retrieved_client = await get_redis(mock_request)

    assert retrieved_client is mock_redis_instance


@pytest.mark.asyncio
async def test_get_redis_client_not_found_in_state():
    """Test when redis_client is not set in app state."""
    mock_request = MagicMock(spec=Request)
    # Simulate client not being set by deleting the attribute if it exists
    # or ensuring it doesn't exist
    if hasattr(mock_request.app.state, "redis_client"):
        del mock_request.app.state.redis_client

    with pytest.raises(HTTPException) as exc_info:
        await get_redis(mock_request)

    assert exc_info.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert "Redis service not available" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_redis_client_is_none_in_state():
    """Test when redis_client is explicitly None in app state."""
    mock_request = MagicMock(spec=Request)
    mock_request.app.state.redis_client = None  # Set client to None

    with pytest.raises(HTTPException) as exc_info:
        await get_redis(mock_request)

    assert exc_info.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert "Redis service not available" in exc_info.value.detail
