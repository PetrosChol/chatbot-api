from unittest.mock import patch, MagicMock
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, AsyncSession

# Module to test
from app.db.session_factory import create_db_session_factory


@patch("app.db.session_factory.async_sessionmaker")
def test_create_db_session_factory_success(mock_async_sessionmaker):
    """Test successful session factory creation."""
    mock_engine = MagicMock(spec=AsyncEngine)
    mock_factory = MagicMock(spec=async_sessionmaker)
    mock_async_sessionmaker.return_value = mock_factory

    factory = create_db_session_factory(mock_engine)

    assert factory is mock_factory
    mock_async_sessionmaker.assert_called_once_with(
        bind=mock_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )


@patch("app.db.session_factory.async_sessionmaker")
@patch("app.db.session_factory.logger")
def test_create_db_session_factory_no_engine(mock_logger, mock_async_sessionmaker):
    """Test factory creation when no engine is provided."""
    factory = create_db_session_factory(None)

    assert factory is None
    mock_logger.warning.assert_called_once_with(
        "No DB engine provided. Cannot create session factory."
    )
    mock_async_sessionmaker.assert_not_called()


@patch("app.db.session_factory.async_sessionmaker")
@patch("app.db.session_factory.logger")
def test_create_db_session_factory_creation_fails(mock_logger, mock_async_sessionmaker):
    """Test factory creation when async_sessionmaker raises an exception."""
    mock_engine = MagicMock(spec=AsyncEngine)
    test_exception = RuntimeError("Factory creation error")
    mock_async_sessionmaker.side_effect = test_exception

    factory = create_db_session_factory(mock_engine)

    assert factory is None
    mock_async_sessionmaker.assert_called_once_with(
        bind=mock_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )
    mock_logger.error.assert_called_once_with(
        f"Failed to create session factory: {test_exception}", exc_info=True
    )
