import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import redis
from fastapi import HTTPException, Request, status
from sqlalchemy.exc import SQLAlchemyError

from app.main import health_check


# This module contains unit tests for the `/health` endpoint in `app.main`.
# It verifies that the health check function correctly assesses the status of
# critical application dependencies (database and Redis) under various conditions,
# including success, specific failures, timeouts, and unconfigured states.


# --- Test Fixtures ---


@pytest.fixture
def mock_request() -> Request:
    """
    Provides a mock FastAPI `Request` object, configured with mock application state
    for database session factory and Redis client, simulating the dependencies
    available during a real request.
    The `HEALTH_CHECK_TIMEOUT_S` setting is also patched for consistent testing.
    """
    request = MagicMock(spec=Request)
    request.app = MagicMock()
    request.app.state = MagicMock()

    # Mock DB Session Factory as an async context manager.
    mock_db_context_manager = AsyncMock()
    request.app.state.db_session_factory = MagicMock(
        return_value=mock_db_context_manager
    )

    # Mock Redis Client.
    request.app.state.redis_client = AsyncMock(spec=redis.Redis)

    # Patch settings to control health check timeout during tests.
    with patch("app.main.settings") as mock_main_settings:
        mock_main_settings.HEALTH_CHECK_TIMEOUT_S = 1
        yield request


# --- Test Cases ---


@pytest.mark.asyncio
async def test_health_check_all_healthy(mock_request):
    """
    Tests the `/health` endpoint when both the database and Redis are healthy.
    Ensures the response indicates an overall healthy status and detailed
    "ok" statuses for each dependency.
    """
    # Arrange: Configure mock DB session to indicate health.
    mock_db_context_manager = mock_request.app.state.db_session_factory.return_value
    mock_session = mock_db_context_manager.__aenter__.return_value
    mock_session.execute = AsyncMock()

    # Arrange: Configure mock Redis client to indicate health.
    mock_request.app.state.redis_client.ping = AsyncMock(return_value=True)

    # Act: Call the health check function.
    response = await health_check(mock_request)

    # Assert: Verify the expected healthy response.
    assert response == {
        "status": "healthy",
        "dependencies": {
            "database": {"status": "ok", "error": None},
            "redis": {"status": "ok", "error": None},
        },
    }


@pytest.mark.asyncio
async def test_health_check_db_sqlalchemy_error(mock_request):
    """
    Tests the `/health` endpoint when the database check fails due to an
    `SQLAlchemyError`. Verifies that an `HTTPException` with a 503 status
    and detailed error message is raised.
    """
    # Arrange: Configure mock DB session to raise a SQLAlchemyError.
    mock_db_context_manager = mock_request.app.state.db_session_factory.return_value
    mock_session = mock_db_context_manager.__aenter__.return_value
    db_error_message = "DB connection failed"
    mock_session.execute = AsyncMock(side_effect=SQLAlchemyError(db_error_message))

    # Arrange: Configure mock Redis client to indicate health.
    mock_request.app.state.redis_client.ping = AsyncMock(return_value=True)

    # Act & Assert: Expect an HTTPException due to DB failure.
    with pytest.raises(HTTPException) as exc_info:
        await health_check(mock_request)

    assert exc_info.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert exc_info.value.detail == {
        "status": "unhealthy",
        "dependencies": {
            "database": {
                "status": "unhealthy",
                "error": f"Database error: {db_error_message}",
            },
            "redis": {"status": "ok", "error": None},
        },
    }


@pytest.mark.asyncio
@patch("asyncio.wait_for")
async def test_health_check_db_timeout(mock_wait_for, mock_request):
    """
    Tests the `/health` endpoint when the database check times out.
    Uses `patch` on `asyncio.wait_for` to simulate the timeout.
    """
    # Arrange: Configure `asyncio.wait_for` to raise `TimeoutError` specifically for the DB check.
    db_check_coro = None # To capture the coroutine passed to wait_for.

    async def side_effect_timeout_db(*args, **kwargs):
        nonlocal db_check_coro
        # Identify the database check task by its qualified name.
        if "db_check_task" in getattr(args[0], "__qualname__", ""):
            db_check_coro = args[0]
            raise asyncio.TimeoutError("DB timeout")
        # Allow Redis check to proceed normally or succeed mock.
        return "ok"

    mock_wait_for.side_effect = side_effect_timeout_db

    # Arrange: Mock Redis to succeed and DB session setup for task creation.
    mock_request.app.state.redis_client.ping = AsyncMock(return_value=True)
    mock_db_context_manager = mock_request.app.state.db_session_factory.return_value
    mock_session = mock_db_context_manager.__aenter__.return_value
    mock_session.execute = AsyncMock()

    # Act & Assert: Expect an HTTPException due to DB timeout.
    with pytest.raises(HTTPException) as exc_info:
        await health_check(mock_request)

    assert exc_info.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    timeout = 1
    assert exc_info.value.detail == {
        "status": "unhealthy",
        "dependencies": {
            "database": {
                "status": "unhealthy",
                "error": f"Database check timed out after {timeout}s",
            },
            "redis": {"status": "ok", "error": None},
        },
    }
    assert db_check_coro is not None


@pytest.mark.asyncio
async def test_health_check_redis_error(mock_request):
    """
    Tests the `/health` endpoint when the Redis check fails due to a `RedisError`.
    Verifies that an `HTTPException` with a 503 status and detailed error message is raised.
    """
    # Arrange: Configure mock DB session for success.
    mock_db_context_manager = mock_request.app.state.db_session_factory.return_value
    mock_session = mock_db_context_manager.__aenter__.return_value
    mock_session.execute = AsyncMock()

    # Arrange: Configure mock Redis client to raise a `RedisError`.
    redis_error_message = "Redis connection failed"
    mock_request.app.state.redis_client.ping = AsyncMock(
        side_effect=redis.RedisError(redis_error_message)
    )

    # Act & Assert: Expect an HTTPException due to Redis failure.
    with pytest.raises(HTTPException) as exc_info:
        await health_check(mock_request)

    assert exc_info.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert exc_info.value.detail == {
        "status": "unhealthy",
        "dependencies": {
            "database": {"status": "ok", "error": None},
            "redis": {
                "status": "unhealthy",
                "error": f"Redis error: {redis_error_message}",
            },
        },
    }


@pytest.mark.asyncio
@patch("asyncio.wait_for")
@pytest.mark.filterwarnings(
    "ignore:coroutine 'health_check.<locals>.*_check_task' was never awaited:RuntimeWarning"
)
async def test_health_check_redis_timeout(mock_wait_for, mock_request):
    """
    Tests the `/health` endpoint when the Redis check times out.
    Uses `patch` on `asyncio.wait_for` to simulate the timeout.
    `filterwarnings` is used to suppress benign RuntimeWarnings from unawaited coroutines
    due to the nature of `asyncio.wait_for` side effects in testing.
    """
    # Arrange: Configure `asyncio.wait_for` to raise `TimeoutError` specifically for the Redis check.
    redis_check_coro = None

    async def side_effect_timeout_redis(*args, **kwargs):
        nonlocal redis_check_coro
        # Identify the Redis check task.
        if "redis_check_task" in getattr(args[0], "__qualname__", ""):
            redis_check_coro = args[0]
            raise asyncio.TimeoutError("Redis timeout")
        # Allow DB check to proceed normally or succeed mock.
        return "ok"

    mock_wait_for.side_effect = side_effect_timeout_redis

    # Arrange: Mock DB session factory for success and Redis client for task creation.
    mock_db_context_manager = mock_request.app.state.db_session_factory.return_value
    mock_session = mock_db_context_manager.__aenter__.return_value
    mock_session.execute = AsyncMock()
    mock_request.app.state.redis_client.ping = AsyncMock(return_value=True)

    # Act & Assert: Expect an HTTPException due to Redis timeout.
    with pytest.raises(HTTPException) as exc_info:
        await health_check(mock_request)

    assert exc_info.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    timeout = 1
    assert exc_info.value.detail == {
        "status": "unhealthy",
        "dependencies": {
            "database": {"status": "ok", "error": None},
            "redis": {
                "status": "unhealthy",
                "error": f"Redis check timed out after {timeout}s",
            },
        },
    }
    assert redis_check_coro is not None


@pytest.mark.asyncio
async def test_health_check_db_unavailable(mock_request):
    """
    Tests the `/health` endpoint when the database session factory is not
    configured (e.g., `app.state.db_session_factory` is `None`).
    Ensures the response indicates DB as "unavailable".
    """
    # Arrange: Simulate missing DB session factory.
    mock_request.app.state.db_session_factory = None

    # Arrange: Configure mock Redis client to indicate health.
    mock_request.app.state.redis_client.ping = AsyncMock(return_value=True)

    # Act: Call the health check function.
    response = await health_check(mock_request)

    # Assert: Verify the response showing DB as unavailable.
    assert response == {
        "status": "healthy", # Overall status is still healthy if other dependencies are ok.
        "dependencies": {
            "database": {
                "status": "unavailable",
                "error": "Database session factory not configured",
            },
            "redis": {"status": "ok", "error": None},
        },
    }


@pytest.mark.asyncio
@pytest.mark.filterwarnings(
    "ignore:coroutine 'health_check.<locals>.*_check_task' was never awaited:RuntimeWarning"
)
async def test_health_check_redis_unavailable(mock_request):
    """
    Tests the `/health` endpoint when the Redis client is not configured
    (e.g., `app.state.redis_client` is `None`).
    Ensures the response indicates Redis as "unavailable".
    `filterwarnings` is used for similar reasons as in timeout tests.
    """
    # Arrange: Configure mock DB session for success.
    mock_db_context_manager = mock_request.app.state.db_session_factory.return_value
    mock_session = mock_db_context_manager.__aenter__.return_value
    mock_session.execute = AsyncMock()

    # Arrange: Simulate missing Redis client.
    mock_request.app.state.redis_client = None

    # Act: Call the health check function.
    response = await health_check(mock_request)

    # Assert: Verify the response showing Redis as unavailable.
    assert response == {
        "status": "healthy", # Overall status is still healthy if other dependencies are ok.
        "dependencies": {
            "database": {"status": "ok", "error": None},
            "redis": {"status": "unavailable", "error": "Redis client not configured"},
        },
    }


@pytest.mark.asyncio
async def test_health_check_both_unhealthy(mock_request):
    """
    Tests the `/health` endpoint when both database and Redis checks fail.
    Ensures an `HTTPException` with a 503 status is raised, detailing both failures.
    """
    # Arrange: Configure mock DB session to raise an error.
    mock_db_context_manager = mock_request.app.state.db_session_factory.return_value
    mock_session = mock_db_context_manager.__aenter__.return_value
    db_error_message = "DB connection failed"
    mock_session.execute = AsyncMock(side_effect=SQLAlchemyError(db_error_message))

    # Arrange: Configure mock Redis client to raise an error.
    redis_error_message = "Redis connection failed"
    mock_request.app.state.redis_client.ping = AsyncMock(
        side_effect=redis.RedisError(redis_error_message)
    )

    # Act & Assert: Expect an HTTPException due to both failures.
    with pytest.raises(HTTPException) as exc_info:
        await health_check(mock_request)

    assert exc_info.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert exc_info.value.detail == {
        "status": "unhealthy",
        "dependencies": {
            "database": {
                "status": "unhealthy",
                "error": f"Database error: {db_error_message}",
            },
            "redis": {
                "status": "unhealthy",
                "error": f"Redis error: {redis_error_message}",
            },
        },
    }


@pytest.mark.asyncio
@pytest.mark.filterwarnings(
    "ignore:coroutine 'health_check.<locals>.*_check_task' was never awaited:RuntimeWarning"
)
async def test_health_check_db_unexpected_error(mock_request):
    """
    Tests the `/health` endpoint when the database check encounters an unexpected
    general `Exception`. Ensures a 503 HTTP status and detailed error message.
    """
    # Arrange: Configure mock DB session to raise a general Exception.
    mock_db_context_manager = mock_request.app.state.db_session_factory.return_value
    mock_session = mock_db_context_manager.__aenter__.return_value
    db_error_message = "Unexpected DB issue"
    mock_session.execute = AsyncMock(side_effect=Exception(db_error_message))

    # Arrange: Configure mock Redis client for success.
    mock_request.app.state.redis_client.ping = AsyncMock(return_value=True)

    # Act & Assert: Expect an HTTPException due to the unexpected DB error.
    with pytest.raises(HTTPException) as exc_info:
        await health_check(mock_request)

    assert exc_info.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert exc_info.value.detail == {
        "status": "unhealthy",
        "dependencies": {
            "database": {
                "status": "unhealthy",
                "error": f"Unexpected error during DB check: {db_error_message}",
            },
            "redis": {"status": "ok", "error": None},
        },
    }


@pytest.mark.asyncio
@pytest.mark.filterwarnings(
    "ignore:coroutine 'health_check.<locals>.*_check_task' was never awaited:RuntimeWarning"
)
async def test_health_check_redis_unexpected_error(mock_request):
    """
    Tests the `/health` endpoint when the Redis check encounters an unexpected
    general `Exception`. Ensures a 503 HTTP status and detailed error message.
    """
    # Arrange: Configure mock DB session for success.
    mock_db_context_manager = mock_request.app.state.db_session_factory.return_value
    mock_session = mock_db_context_manager.__aenter__.return_value
    mock_session.execute = AsyncMock()

    # Arrange: Configure mock Redis client to raise a general Exception.
    redis_error_message = "Unexpected Redis issue"
    mock_request.app.state.redis_client.ping = AsyncMock(
        side_effect=Exception(redis_error_message)
    )

    # Act & Assert: Expect an HTTPException due to the unexpected Redis error.
    with pytest.raises(HTTPException) as exc_info:
        await health_check(mock_request)

    assert exc_info.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert exc_info.value.detail == {
        "status": "unhealthy",
        "dependencies": {
            "database": {"status": "ok", "error": None},
            "redis": {
                "status": "unhealthy",
                "error": f"Unexpected error during Redis check: {redis_error_message}",
            },
        },
    }