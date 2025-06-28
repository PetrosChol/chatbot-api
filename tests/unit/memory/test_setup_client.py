import pytest
from unittest.mock import AsyncMock, patch
import redis.asyncio as redis_asyncio_real
from redis.exceptions import ConnectionError, TimeoutError, RedisError

# The module under test, responsible for setting up the Redis client.
from app.memory.setup_client import setup_redis_client, _mask_redis_url_password


@pytest.mark.asyncio
@patch("app.memory.setup_client.settings")
@patch("redis.asyncio.Redis.from_url")
@patch("app.memory.setup_client.logger")
async def test_setup_redis_client_success(mock_logger, mock_from_url, mock_settings):
    """
    Tests the successful initialization and connection verification of the Redis client.
    Ensures that the client is created from the correct URL and a ping succeeds.
    """
    # Configure mock settings with a valid Redis URL.
    raw_redis_url = "redis://user:password@localhost:6379"
    mock_settings.REDIS_URL = raw_redis_url

    # Mock the Redis client instance and its `ping` method.
    mock_client_instance = AsyncMock(spec=redis_asyncio_real.Redis)
    mock_from_url.return_value = mock_client_instance
    mock_client_instance.ping = AsyncMock(return_value=True)

    # Call the function under test.
    client = await setup_redis_client()

    # Assertions for successful client creation and connection.
    assert client is mock_client_instance
    mock_from_url.assert_called_once_with(
        str(mock_settings.REDIS_URL), encoding="utf-8", decode_responses=True
    )
    mock_client_instance.ping.assert_awaited_once()

    # Verify logging for successful operation.
    masked_url = _mask_redis_url_password(raw_redis_url)
    mock_logger.info.assert_any_call(
        f"Creating Redis client for REDIS URL (details masked): {masked_url}"
    )
    mock_logger.info.assert_any_call(
        "Successfully connected to Redis and ping successful."
    )


@pytest.mark.asyncio
@patch("app.memory.setup_client.settings")
@patch("redis.asyncio.Redis.from_url")
@patch("app.memory.setup_client.logger")
async def test_setup_redis_client_no_url(mock_logger, mock_from_url, mock_settings):
    """
    Tests the behavior of `setup_redis_client` when `REDIS_URL` is not configured.
    Ensures that no client is created and a warning is logged.
    """
    # Configure mock settings to simulate missing Redis URL.
    mock_settings.REDIS_URL = None

    # Call the function under test.
    client = await setup_redis_client()

    # Assertions.
    assert client is None
    # Verify that a warning is logged and no Redis client methods are called.
    mock_logger.warning.assert_called_once_with(
        "REDIS_URL not configured. Skipping Redis client creation."
    )
    mock_logger.error.assert_not_called()
    mock_logger.info.assert_not_called()
    mock_from_url.assert_not_called()


@pytest.mark.asyncio
@patch("app.memory.setup_client.settings")
@patch("redis.asyncio.Redis.from_url")
@patch("app.memory.setup_client.logger")
async def test_setup_redis_client_connection_error(
    mock_logger, mock_from_url, mock_settings
):
    """
    Tests `setup_redis_client` when a `ConnectionError` occurs during client creation.
    Ensures the client is `None` and an error is logged with exception details.
    """
    # Configure settings with a problematic Redis URL.
    raw_redis_url = "redis://invalid-host:6379"
    mock_settings.REDIS_URL = raw_redis_url

    # Simulate `redis.asyncio.Redis.from_url` raising a `ConnectionError`.
    test_exception = ConnectionError("DNS lookup failed")
    mock_from_url.side_effect = test_exception

    # Call the function under test.
    client = await setup_redis_client()

    # Assertions.
    assert client is None
    mock_from_url.assert_called_once_with(
        str(mock_settings.REDIS_URL), encoding="utf-8", decode_responses=True
    )

    # Verify specific error logging.
    masked_url = _mask_redis_url_password(raw_redis_url)
    mock_logger.info.assert_called_once_with(
        f"Creating Redis client for REDIS URL (details masked): {masked_url}"
    )
    mock_logger.error.assert_called_once_with(
        f"Error connecting to Redis (URL details masked: {masked_url}) or ping failed: {test_exception}",
        exc_info=True,
    )


@pytest.mark.asyncio
@patch("app.memory.setup_client.settings")
@patch("redis.asyncio.Redis.from_url")
@patch("app.memory.setup_client.logger")
async def test_setup_redis_client_ping_error(mock_logger, mock_from_url, mock_settings):
    """
    Tests `setup_redis_client` when the Redis client is created, but the initial
    `ping` operation fails (e.g., due to a timeout).
    Ensures the client is `None` and an error is logged.
    """
    # Configure settings with a valid Redis URL.
    raw_redis_url = "redis://localhost:6379"
    mock_settings.REDIS_URL = raw_redis_url

    # Mock a successful client instance, but make its `ping` method fail.
    mock_client_instance = AsyncMock(spec=redis_asyncio_real.Redis)
    mock_from_url.return_value = mock_client_instance

    test_exception = TimeoutError("Ping timed out")
    mock_client_instance.ping = AsyncMock(side_effect=test_exception)

    # Call the function under test.
    client = await setup_redis_client()

    # Assertions.
    assert client is None
    mock_from_url.assert_called_once_with(
        str(mock_settings.REDIS_URL), encoding="utf-8", decode_responses=True
    )
    mock_client_instance.ping.assert_awaited_once()

    # Verify error logging.
    masked_url = _mask_redis_url_password(raw_redis_url)
    mock_logger.info.assert_called_once_with(
        f"Creating Redis client for REDIS URL (details masked): {masked_url}"
    )
    mock_logger.error.assert_called_once_with(
        f"Error connecting to Redis (URL details masked: {masked_url}) or ping failed: {test_exception}",
        exc_info=True,
    )


@pytest.mark.asyncio
@patch("app.memory.setup_client.settings")
@patch("redis.asyncio.Redis.from_url")
@patch("app.memory.setup_client.logger")
async def test_setup_redis_client_general_exception_handled_as_connection_ping_failure(
    mock_logger, mock_from_url, mock_settings
):
    """
    Tests `setup_redis_client` when a general `Exception` occurs during client creation.
    Ensures that this exception is caught and handled similarly to a connection/ping failure.
    """
    # Configure settings with a valid Redis URL.
    raw_redis_url = "redis://localhost:6379"
    mock_settings.REDIS_URL = raw_redis_url

    # Simulate `redis.asyncio.Redis.from_url` raising a general `Exception`.
    test_exception = Exception("Some other non-specific error")
    mock_from_url.side_effect = test_exception

    # Call the function under test.
    client = await setup_redis_client()

    # Assertions.
    assert client is None
    # Verify error logging for the general exception.
    masked_url = _mask_redis_url_password(raw_redis_url)
    mock_logger.info.assert_called_once_with(
        f"Creating Redis client for REDIS URL (details masked): {masked_url}"
    )
    mock_logger.error.assert_called_once_with(
        f"Error connecting to Redis (URL details masked: {masked_url}) or ping failed: {test_exception}",
        exc_info=True,
    )


@pytest.mark.asyncio
@patch("app.memory.setup_client.settings")
@patch("redis.asyncio.Redis.from_url")
@patch("app.memory.setup_client.logger")
async def test_setup_redis_client_specific_redis_error_handled_as_connection_ping_failure(
    mock_logger, mock_from_url, mock_settings
):
    """
    Tests `setup_redis_client` when a specific `RedisError` (not `ConnectionError`
    or `TimeoutError`) occurs during client creation.
    Ensures it is caught and treated as a connection/ping failure.
    """
    # Configure settings with a valid Redis URL.
    raw_redis_url = "redis://localhost:6379"
    mock_settings.REDIS_URL = raw_redis_url

    # Simulate `redis.asyncio.Redis.from_url` raising a `RedisError`.
    test_exception = RedisError("A specific Redis library error")
    mock_from_url.side_effect = test_exception

    # Call the function under test.
    client = await setup_redis_client()

    # Assertions.
    assert client is None
    # Verify error logging for the specific RedisError.
    masked_url = _mask_redis_url_password(raw_redis_url)
    mock_logger.info.assert_called_once_with(
        f"Creating Redis client for REDIS URL (details masked): {masked_url}"
    )
    mock_logger.error.assert_called_once_with(
        f"Error connecting to Redis (URL details masked: {masked_url}) or ping failed: {test_exception}",
        exc_info=True,
    )