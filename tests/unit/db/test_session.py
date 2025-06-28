import pytest
from unittest.mock import MagicMock, AsyncMock
from fastapi import Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

# Module to test
from app.db.session import get_session


@pytest.mark.asyncio
async def test_get_session_success():
    """Test successfully getting a session."""
    mock_request = MagicMock(spec=Request)
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session_factory = MagicMock(spec=async_sessionmaker)

    # Configure the session factory mock to return an async context manager
    # that yields the mock session
    mock_session_factory.return_value.__aenter__.return_value = mock_session
    mock_session_factory.return_value.__aexit__.return_value = (
        None  # Don't raise exception on exit
    )

    # Set the factory on the mock app state
    mock_request.app.state.db_session_factory = mock_session_factory

    session_generator = get_session(mock_request)
    retrieved_session = await session_generator.__anext__()

    assert retrieved_session is mock_session

    # Simulate exiting the 'with' block in the dependency
    try:
        await session_generator.__anext__()
    except StopAsyncIteration:
        pass  # Expected behavior

    mock_session.rollback.assert_not_called()  # No error, so no rollback
    mock_session_factory.return_value.__aenter__.assert_awaited_once()
    mock_session_factory.return_value.__aexit__.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_session_factory_not_found():
    """Test when the session factory is not found in app state."""
    mock_request = MagicMock(spec=Request)
    # Simulate factory not being set
    del mock_request.app.state.db_session_factory

    session_generator = get_session(mock_request)

    with pytest.raises(HTTPException) as exc_info:
        await session_generator.__anext__()

    assert exc_info.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert "Database service not configured correctly" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_session_exception_and_rollback():
    """Test that rollback occurs if an exception happens during session use."""
    mock_request = MagicMock(spec=Request)
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session_factory = MagicMock(spec=async_sessionmaker)

    mock_session_factory.return_value.__aenter__.return_value = mock_session
    # Simulate __aexit__ handling the exception (typical context manager behavior)
    mock_session_factory.return_value.__aexit__.return_value = None

    mock_request.app.state.db_session_factory = mock_session_factory

    session_generator = get_session(mock_request)
    retrieved_session = await session_generator.__anext__()

    assert retrieved_session is mock_session

    # Simulate an exception occurring within the 'yield' block
    test_exception = ValueError("Something went wrong in the endpoint")
    with pytest.raises(ValueError, match="Something went wrong in the endpoint"):
        await session_generator.athrow(
            test_exception
        )  # Throw exception into the generator

    mock_session.rollback.assert_awaited_once()  # Rollback should have been called
    mock_session_factory.return_value.__aenter__.assert_awaited_once()
    # __aexit__ should still be awaited by the context manager protocol
    mock_session_factory.return_value.__aexit__.assert_awaited_once()
