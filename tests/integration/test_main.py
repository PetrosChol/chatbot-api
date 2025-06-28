import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from app.main import app


# --- Fixtures for Mocking Dependencies ---

@pytest.fixture(scope="function")
def mock_db_engine():
    """
    Provides a mock SQLAlchemy AsyncEngine for testing database initialization.
    The dispose method is mocked to simulate proper cleanup.
    """
    engine = AsyncMock(spec=AsyncEngine)
    engine.dispose = AsyncMock()
    return engine


@pytest.fixture(scope="function")
def mock_db_session_factory():
    """
    Provides a mock SQLAlchemy async_sessionmaker for testing database session creation.
    """
    return MagicMock(spec=async_sessionmaker)


@pytest.fixture(scope="function")
def mock_redis_client():
    """
    Provides a mock Redis client for testing Redis setup and teardown.
    The aclose method is mocked to simulate proper connection closure.
    """
    client = AsyncMock(spec=redis.Redis)
    client.aclose = AsyncMock()
    return client


# --- Test Cases for FastAPI Lifespan Events ---


@patch("app.main.create_db_engine")
@patch("app.main.create_db_session_factory")
@patch("app.main.setup_redis_client")
@patch("app.main.FastAPILimiter.init")
@patch("app.main.shutdown_redis_client")
@pytest.mark.asyncio
async def test_lifespan_success(
    mock_shutdown_redis,
    mock_limiter_init,
    mock_setup_redis,
    mock_create_session_factory,
    mock_create_engine,
    mock_db_engine,
    mock_db_session_factory,
    mock_redis_client,
):
    """
    Tests the successful execution of FastAPI's lifespan events (startup and shutdown).
    Verifies that all dependencies are initialized and cleaned up correctly.
    """
    # Configure mocks to return successful instances
    mock_create_engine.return_value = mock_db_engine
    mock_create_session_factory.return_value = mock_db_session_factory
    mock_setup_redis.return_value = mock_redis_client

    # Use TestClient to trigger FastAPI's startup and shutdown events
    with TestClient(app) as client:
        # Assertions for startup phase
        mock_create_engine.assert_called_once()
        mock_create_session_factory.assert_called_once_with(mock_db_engine)
        mock_setup_redis.assert_awaited_once()
        mock_limiter_init.assert_awaited_once_with(mock_redis_client)
        assert app.state.db_engine is mock_db_engine
        assert app.state.db_session_factory is mock_db_session_factory
        assert app.state.redis_client is mock_redis_client

    # Assertions for shutdown phase
    mock_shutdown_redis.assert_awaited_once_with(mock_redis_client)
    mock_db_engine.dispose.assert_awaited_once()


@patch("app.main.create_db_engine")
@patch("app.main.create_db_session_factory")
@patch("app.main.setup_redis_client")
@patch("app.main.FastAPILimiter.init")
@patch("app.main.shutdown_redis_client")
@patch("app.main.logger")
@pytest.mark.asyncio
async def test_lifespan_db_failure(
    mock_logger,
    mock_shutdown_redis,
    mock_limiter_init,
    mock_setup_redis,
    mock_create_session_factory,
    mock_create_engine,
    mock_redis_client,
):
    """
    Tests the lifespan manager's behavior when database engine creation fails.
    Ensures appropriate logging and graceful handling of the failed dependency.
    """
    # Simulate DB engine failure
    mock_create_engine.return_value = None
    mock_create_session_factory.return_value = None
    mock_setup_redis.return_value = mock_redis_client

    with TestClient(app) as client:
        # Assertions for startup phase with DB failure
        mock_create_engine.assert_called_once()
        mock_create_session_factory.assert_called_once_with(None)
        mock_setup_redis.assert_awaited_once()
        mock_limiter_init.assert_awaited_once_with(mock_redis_client)

        # Verify critical log message for DB initialization failure
        mock_logger.critical.assert_called_once_with(
            "FATAL: Database session factory failed to initialize."
        )
        # Confirm app state reflects the DB initialization failure
        assert not hasattr(app.state, "db_engine") or app.state.db_engine is None
        assert (
            not hasattr(app.state, "db_session_factory")
            or app.state.db_session_factory is None
        )
        assert app.state.redis_client is mock_redis_client

    # Assertions for shutdown phase
    mock_shutdown_redis.assert_awaited_once_with(mock_redis_client)
    # Ensure dispose is NOT called if the engine failed to initialize
    db_engine = getattr(app.state, "db_engine", None)
    if db_engine:
        db_engine.dispose.assert_not_called()


@patch("app.main.create_db_engine")
@patch("app.main.create_db_session_factory")
@patch("app.main.setup_redis_client")
@patch("app.main.FastAPILimiter.init")
@patch("app.main.shutdown_redis_client")
@patch("app.main.logger")
@pytest.mark.asyncio
async def test_lifespan_redis_failure(
    mock_logger,
    mock_shutdown_redis,
    mock_limiter_init,
    mock_setup_redis,
    mock_create_session_factory,
    mock_create_engine,
    mock_db_engine,
    mock_db_session_factory,
):
    """
    Tests the lifespan manager's behavior when Redis client setup fails.
    Ensures appropriate logging and that the application can still proceed without Redis.
    """
    mock_create_engine.return_value = mock_db_engine
    mock_create_session_factory.return_value = mock_db_session_factory
    # Simulate Redis client failure
    mock_setup_redis.return_value = None

    with TestClient(app) as client:
        # Assertions for startup phase with Redis failure
        mock_create_engine.assert_called_once()
        mock_create_session_factory.assert_called_once_with(mock_db_engine)
        mock_setup_redis.assert_awaited_once()
        # FastAPILimiter.init should not be called if Redis client is None
        mock_limiter_init.assert_not_awaited()

        # Verify warning log messages for Redis failure and skipped limiter initialization
        mock_logger.warning.assert_any_call(
            "Redis client failed to initialize. Proceeding without Redis."
        )
        mock_logger.warning.assert_any_call(
            "Redis client not available. Skipping FastAPI Limiter initialization."
        )
        assert app.state.db_engine is mock_db_engine
        assert app.state.db_session_factory is mock_db_session_factory
        # Confirm app state reflects Redis initialization failure
        assert not hasattr(app.state, "redis_client") or app.state.redis_client is None

    # Assertions for shutdown phase
    # shutdown_redis_client should still be called, even with a None client
    mock_shutdown_redis.assert_awaited_once_with(None)
    # Database engine should still be disposed correctly
    mock_db_engine.dispose.assert_awaited_once()