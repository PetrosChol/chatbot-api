from unittest.mock import MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncEngine
import ssl

from app.db.engine import create_db_engine, _mask_url_password, RUNTIME_CA_CERT_PATH


@patch("app.db.engine.settings")
@patch("app.db.engine.create_async_engine")
def test_create_db_engine_success(mock_create_async, mock_settings):
    """
    Tests the successful creation of the database engine with default SSL configuration.
    Verifies that `create_async_engine` is called with the correct DSN and parameters.
    """
    # Configure mock settings for a standard successful scenario.
    mock_settings.DATABASE_URL = "postgresql+asyncpg://user:pass@host:port/db"
    mock_settings.DEBUG = False
    mock_settings.DO_DB_SSL_CERT_PATH = None
    mock_settings.DO_DB_SSL_CERT_CONTENT = None
    mock_settings.SQLALCHEMY_POOL_SIZE = 5
    mock_settings.SQLALCHEMY_MAX_OVERFLOW = 2
    mock_settings.SQLALCHEMY_POOL_RECYCLE = 1800

    # Mock the return value of `create_async_engine`.
    mock_engine = MagicMock(spec=AsyncEngine)
    mock_create_async.return_value = mock_engine

    # Call the function under test.
    engine = create_db_engine()

    # Assertions.
    assert engine is mock_engine
    expected_connect_args = {"ssl": "require"} # Default SSL mode for PgBouncer.
    mock_create_async.assert_called_once_with(
        "postgresql+asyncpg://user:pass@host:port/db",
        echo=False,
        pool_pre_ping=True,
        connect_args=expected_connect_args,
        pool_size=5,
        max_overflow=2,
        pool_recycle=1800,
    )


@patch("app.db.engine.settings")
@patch("app.db.engine.create_async_engine")
@patch("app.db.engine.logger")
def test_create_db_engine_no_url(mock_logger, mock_create_async, mock_settings):
    """
    Tests `create_db_engine` behavior when `DATABASE_URL` is not provided in settings.
    Ensures that the function returns `None` and logs an appropriate error.
    """
    # Configure mock settings to simulate missing DATABASE_URL.
    mock_settings.DATABASE_URL = None
    mock_settings.DO_DB_SSL_CERT_PATH = None
    mock_settings.DO_DB_SSL_CERT_CONTENT = None

    # Call the function under test.
    engine = create_db_engine()

    # Assertions.
    assert engine is None
    mock_logger.error.assert_called_once_with(
        "DATABASE_URL is None in settings. Cannot create DB engine."
    )
    mock_create_async.assert_not_called()


@patch("app.db.engine.settings")
@patch("app.db.engine.create_async_engine")
@patch("app.db.engine.logger")
def test_create_db_engine_creation_fails(mock_logger, mock_create_async, mock_settings):
    """
    Tests `create_db_engine` when `create_async_engine` itself raises an exception.
    Ensures the function returns `None` and logs the failure with exception info.
    """
    # Configure mock settings for an engine creation attempt.
    db_url_initial = "postgresql://user:pass@host:port/db"
    expected_engine_url_for_call = "postgresql+asyncpg://user:pass@host:port/db"

    mock_settings.DATABASE_URL = db_url_initial
    mock_settings.DEBUG = True
    mock_settings.DO_DB_SSL_CERT_PATH = None
    mock_settings.DO_DB_SSL_CERT_CONTENT = None
    mock_settings.SQLALCHEMY_POOL_SIZE = 5
    mock_settings.SQLALCHEMY_MAX_OVERFLOW = 2
    mock_settings.SQLALCHEMY_POOL_RECYCLE = 1800

    # Simulate `create_async_engine` raising an exception.
    test_exception = ValueError("DB connection failed")
    mock_create_async.side_effect = test_exception

    # Call the function under test.
    engine = create_db_engine()

    # Assertions.
    assert engine is None
    expected_connect_args = {"ssl": "require"}
    mock_create_async.assert_called_once_with(
        expected_engine_url_for_call,
        echo=True,
        pool_pre_ping=True,
        connect_args=expected_connect_args,
        pool_size=5,
        max_overflow=2,
        pool_recycle=1800,
    )
    assert mock_logger.error.called


@patch("app.db.engine.settings")
@patch("app.db.engine.create_async_engine")
@patch("app.db.engine.logger")
def test_create_db_engine_empty_url_string_from_pydantic(
    mock_logger, mock_create_async, mock_settings
):
    """
    Tests `create_db_engine` when `DATABASE_URL`, potentially a Pydantic URL object,
    resolves to an empty string. Ensures the function returns `None` and logs an error.
    """
    # Simulate a Pydantic URL object that renders as an empty string.
    mock_db_url_obj = MagicMock()
    mock_db_url_obj.render_as_string = MagicMock(return_value="")
    mock_db_url_obj.unicode_string = MagicMock(return_value=None)

    mock_settings.DATABASE_URL = mock_db_url_obj
    mock_settings.DO_DB_SSL_CERT_PATH = None
    mock_settings.DO_DB_SSL_CERT_CONTENT = None
    mock_settings.DEBUG = False

    # Call the function under test.
    engine = create_db_engine()

    # Assertions.
    assert engine is None
    mock_db_url_obj.unicode_string.assert_called_once()
    mock_db_url_obj.render_as_string.assert_called_once_with(hide_password=False)
    mock_logger.error.assert_called_once_with(
        "DATABASE_URL resolved to None or an empty string. Cannot create DB engine."
    )
    mock_create_async.assert_not_called()


@patch("app.db.engine.settings")
@patch("app.db.engine.create_async_engine")
@patch("app.db.engine.logger")
def test_create_db_engine_ssl_cert_path_is_empty_string(
    mock_logger, mock_create_async, mock_settings
):
    """
    Tests `create_db_engine` when `DO_DB_SSL_CERT_PATH` is an empty string.
    Ensures that default SSL behavior (`ssl: require`) is applied and a warning is logged.
    """
    # Configure settings with an empty SSL cert path.
    mock_settings.DATABASE_URL = "postgresql+asyncpg://user:pass@host:port/db"
    mock_settings.DEBUG = False
    mock_settings.DO_DB_SSL_CERT_PATH = ""
    mock_settings.DO_DB_SSL_CERT_CONTENT = None
    mock_settings.SQLALCHEMY_POOL_SIZE = 5
    mock_settings.SQLALCHEMY_MAX_OVERFLOW = 2
    mock_settings.SQLALCHEMY_POOL_RECYCLE = 1800

    # Mock the return value of `create_async_engine`.
    mock_engine = MagicMock(spec=AsyncEngine)
    mock_create_async.return_value = mock_engine

    # Call the function under test.
    engine = create_db_engine()

    # Assertions.
    assert engine is mock_engine
    expected_connect_args = {"ssl": "require"} # Should fall back to default 'require'
    mock_create_async.assert_called_once_with(
        "postgresql+asyncpg://user:pass@host:port/db",
        echo=False,
        pool_pre_ping=True,
        connect_args=expected_connect_args,
        pool_size=5,
        max_overflow=2,
        pool_recycle=1800,
    )
    mock_logger.info.assert_any_call(
        "SSL Configuration for PgBouncer: No valid CA certificate provided. Using 'ssl': 'require'. "
        "PgBouncer server certificate will not be verified against a specific CA."
    )


@patch("app.db.engine.settings")
@patch("app.db.engine.create_async_engine")
@patch("app.db.engine.logger")
@patch("ssl.create_default_context")
@patch("app.db.engine.os.path.exists")
def test_create_db_engine_with_ssl_cert_path_success(
    mock_os_path_exists,
    mock_ssl_create_context,
    mock_logger,
    mock_create_async,
    mock_settings,
):
    """
    Tests the successful creation of the database engine when `DO_DB_SSL_CERT_PATH`
    is provided and the certificate file exists. Verifies the SSL context is created
    and passed correctly.
    """
    # Configure settings with a valid SSL cert path.
    db_url_initial = "postgresql://user:pass@host:port/db"
    expected_engine_url_for_call = "postgresql+asyncpg://user:pass@host:port/db"
    cert_path = "/path/to/ca.pem"

    mock_settings.DATABASE_URL = db_url_initial
    mock_settings.DEBUG = False
    mock_settings.DO_DB_SSL_CERT_PATH = cert_path
    mock_settings.DO_DB_SSL_CERT_CONTENT = None
    mock_settings.SQLALCHEMY_POOL_SIZE = 5
    mock_settings.SQLALCHEMY_MAX_OVERFLOW = 2
    mock_settings.SQLALCHEMY_POOL_RECYCLE = 1800

    # Mock dependencies.
    mock_os_path_exists.return_value = True
    mock_ssl_obj = MagicMock(spec=ssl.SSLContext)
    mock_ssl_create_context.return_value = mock_ssl_obj
    mock_engine_instance = MagicMock(spec=AsyncEngine)
    mock_create_async.return_value = mock_engine_instance

    # Call the function under test.
    engine = create_db_engine()

    # Assertions.
    assert engine is mock_engine_instance
    mock_os_path_exists.assert_called_once_with(cert_path)
    mock_ssl_create_context.assert_called_once_with(
        ssl.Purpose.SERVER_AUTH, cafile=cert_path
    )
    expected_connect_args = {"ssl": mock_ssl_obj} # SSL context object should be passed.
    mock_create_async.assert_called_once_with(
        expected_engine_url_for_call,
        echo=False,
        pool_pre_ping=True,
        connect_args=expected_connect_args,
        pool_size=5,
        max_overflow=2,
        pool_recycle=1800,
    )


@patch("app.db.engine.settings")
@patch("app.db.engine.create_async_engine")
@patch("app.db.engine.logger")
@patch("app.db.engine.os.path.exists")
def test_create_db_engine_ssl_cert_path_not_found(
    mock_os_path_exists, mock_logger, mock_create_async, mock_settings
):
    """
    Tests `create_db_engine` when `DO_DB_SSL_CERT_PATH` is provided but the file does not exist.
    Ensures it falls back to `ssl: require` and logs a warning.
    """
    # Configure settings with an invalid SSL cert path.
    db_url_initial = "postgresql://user:pass@host:port/db"
    expected_engine_url_for_call = "postgresql+asyncpg://user:pass@host:port/db"
    invalid_cert_path = "/invalid/path/to/ca.pem"

    mock_settings.DATABASE_URL = db_url_initial
    mock_settings.DEBUG = False
    mock_settings.DO_DB_SSL_CERT_PATH = invalid_cert_path
    mock_settings.DO_DB_SSL_CERT_CONTENT = None
    mock_settings.SQLALCHEMY_POOL_SIZE = 5
    mock_settings.SQLALCHEMY_MAX_OVERFLOW = 2
    mock_settings.SQLALCHEMY_POOL_RECYCLE = 1800

    # Simulate path not existing.
    mock_os_path_exists.return_value = False
    mock_engine = MagicMock(spec=AsyncEngine)
    mock_create_async.return_value = mock_engine

    # Call the function under test.
    engine = create_db_engine()

    # Assertions.
    assert engine is mock_engine
    mock_os_path_exists.assert_called_once_with(invalid_cert_path)
    expected_connect_args = {"ssl": "require"} # Should fall back to default 'require'.
    mock_create_async.assert_called_once_with(
        expected_engine_url_for_call,
        echo=False,
        pool_pre_ping=True,
        connect_args=expected_connect_args,
        pool_size=5,
        max_overflow=2,
        pool_recycle=1800,
    )
    mock_logger.warning.assert_called_once_with(
        f"DO_DB_SSL_CERT_PATH ('{invalid_cert_path}') provided but file not found. Will attempt to proceed without custom CA."
    )


@patch("app.db.engine.settings")
@patch("app.db.engine.create_async_engine")
@patch("app.db.engine.logger")
@patch("ssl.create_default_context")
@patch("app.db.engine.os.path.exists")
@patch("app.db.engine.os.remove")
def test_create_db_engine_ssl_context_creation_fails_from_path(
    mock_os_remove,
    mock_os_path_exists,
    mock_ssl_create_context,
    mock_logger,
    mock_create_async,
    mock_settings,
):
    """
    Tests `create_db_engine` when SSL context creation fails even if the cert path exists.
    Ensures the function returns `None` and logs an error without attempting engine creation.
    """
    # Configure settings with a problematic SSL cert path.
    db_url_initial = "postgresql://user:pass@host:port/db"
    cert_path = "/path/to/problematic-ca.pem"
    mock_settings.DATABASE_URL = db_url_initial
    mock_settings.DEBUG = False
    mock_settings.DO_DB_SSL_CERT_PATH = cert_path
    mock_settings.DO_DB_SSL_CERT_CONTENT = None
    mock_settings.SQLALCHEMY_POOL_SIZE = 5
    mock_settings.SQLALCHEMY_MAX_OVERFLOW = 2
    mock_settings.SQLALCHEMY_POOL_RECYCLE = 1800

    # Simulate path existing, but SSL context creation failing.
    mock_os_path_exists.return_value = True
    ssl_error = ssl.SSLError("SSL context creation failed from path")
    mock_ssl_create_context.side_effect = ssl_error

    # Call the function under test.
    engine = create_db_engine()

    # Assertions.
    assert engine is None
    mock_os_path_exists.assert_called_once_with(cert_path)
    mock_ssl_create_context.assert_called_once_with(
        ssl.Purpose.SERVER_AUTH, cafile=cert_path
    )
    mock_create_async.assert_not_called()
    mock_logger.error.assert_called_once_with(
        f"Error creating SSLContext with CA '{cert_path}' for PgBouncer: {ssl_error}."
    )
    mock_os_remove.assert_not_called() # No runtime cert was created, so no removal expected.


@patch("app.db.engine.settings")
@patch("app.db.engine.create_async_engine")
@patch("app.db.engine.logger")
@patch("ssl.create_default_context")
@patch("builtins.open", new_callable=MagicMock)
@patch("app.db.engine.os.remove")
@patch("app.db.engine.os.path.exists")
def test_create_db_engine_ssl_cert_content_success(
    mock_os_path_exists,
    mock_os_remove,
    mock_builtin_open,
    mock_ssl_create_context,
    mock_logger,
    mock_create_async,
    mock_settings,
):
    """
    Tests the successful creation of the database engine when `DO_DB_SSL_CERT_CONTENT`
    is provided. Verifies that the content is written to a temporary file,
    an SSL context is created from it, and the temporary file is cleaned up.
    """
    # Configure settings with SSL cert content.
    db_url_initial = "postgresql://user:pass@host:port/db"
    expected_engine_url_for_call = "postgresql+asyncpg://user:pass@host:port/db"
    cert_content = (
        "-----BEGIN CERTIFICATE-----\n...content...\n-----END CERTIFICATE-----"
    )

    mock_settings.DATABASE_URL = db_url_initial
    mock_settings.DEBUG = False
    mock_settings.DO_DB_SSL_CERT_PATH = None
    mock_settings.DO_DB_SSL_CERT_CONTENT = cert_content
    mock_settings.SQLALCHEMY_POOL_SIZE = 5
    mock_settings.SQLALCHEMY_MAX_OVERFLOW = 2
    mock_settings.SQLALCHEMY_POOL_RECYCLE = 1800

    # Mock dependencies for successful flow.
    mock_os_path_exists.return_value = True # For the cleanup check.
    mock_ssl_obj = MagicMock(spec=ssl.SSLContext)
    mock_ssl_create_context.return_value = mock_ssl_obj
    mock_engine_instance = MagicMock(spec=AsyncEngine)
    mock_create_async.return_value = mock_engine_instance
    mock_file_handle = MagicMock()
    mock_builtin_open.return_value.__enter__.return_value = mock_file_handle

    # Call the function under test.
    engine = create_db_engine()

    # Assertions.
    assert engine is mock_engine_instance
    mock_builtin_open.assert_called_once_with(RUNTIME_CA_CERT_PATH, "w")
    mock_file_handle.write.assert_called_once_with(cert_content)
    mock_ssl_create_context.assert_called_once_with(
        ssl.Purpose.SERVER_AUTH, cafile=RUNTIME_CA_CERT_PATH
    )
    expected_connect_args = {"ssl": mock_ssl_obj}
    mock_create_async.assert_called_once_with(
        expected_engine_url_for_call,
        echo=False,
        pool_pre_ping=True,
        connect_args=expected_connect_args,
        pool_size=5,
        max_overflow=2,
        pool_recycle=1800,
    )
    mock_os_path_exists.assert_called_once_with(RUNTIME_CA_CERT_PATH)
    mock_os_remove.assert_called_once_with(RUNTIME_CA_CERT_PATH) # Verify cleanup.


@patch("app.db.engine.settings")
@patch("app.db.engine.create_async_engine")
@patch("app.db.engine.logger")
@patch("app.db.engine.os.remove")
@patch("app.db.engine.os.path.exists")
def test_create_db_engine_ssl_cert_content_invalid_format_warning(
    mock_os_path_exists, mock_os_remove, mock_logger, mock_create_async, mock_settings
):
    """
    Tests `create_db_engine` when `DO_DB_SSL_CERT_CONTENT` is provided but
    does not appear to be a valid certificate format. Ensures a warning is logged
    and falls back to `ssl: require`.
    """
    # Configure settings with invalid SSL cert content.
    db_url_initial = "postgresql://user:pass@host:port/db"
    expected_engine_url_for_call = "postgresql+asyncpg://user:pass@host:port/db"
    invalid_cert_content = "this is not a valid cert marker"

    mock_settings.DATABASE_URL = db_url_initial
    mock_settings.DEBUG = False
    mock_settings.DO_DB_SSL_CERT_PATH = None
    mock_settings.DO_DB_SSL_CERT_CONTENT = invalid_cert_content
    mock_settings.SQLALCHEMY_POOL_SIZE = 5
    mock_settings.SQLALCHEMY_MAX_OVERFLOW = 2
    mock_settings.SQLALCHEMY_POOL_RECYCLE = 1800

    # Mock engine for successful creation after warning.
    mock_engine_instance = MagicMock(spec=AsyncEngine)
    mock_create_async.return_value = mock_engine_instance

    # Call the function under test.
    engine = create_db_engine()

    # Assertions.
    assert engine is mock_engine_instance
    mock_logger.warning.assert_called_once_with(
        "DO_DB_SSL_CERT_CONTENT does not appear to be a valid certificate. Will attempt to proceed without custom CA if no path is set."
    )
    expected_connect_args = {"ssl": "require"} # Should fall back to default.
    mock_create_async.assert_called_once_with(
        expected_engine_url_for_call,
        echo=False,
        pool_pre_ping=True,
        connect_args=expected_connect_args,
        pool_size=5,
        max_overflow=2,
        pool_recycle=1800,
    )
    mock_os_path_exists.assert_not_called() # No runtime cert created, so no cleanup check.
    mock_os_remove.assert_not_called() # No runtime cert created, so no removal.


@patch("app.db.engine.settings")
@patch("app.db.engine.create_async_engine")
@patch("app.db.engine.logger")
@patch("builtins.open", new_callable=MagicMock)
@patch("app.db.engine.os.remove")
@patch("app.db.engine.os.path.exists")
def test_create_db_engine_ssl_cert_content_write_io_error(
    mock_os_path_exists,
    mock_os_remove,
    mock_builtin_open,
    mock_logger,
    mock_create_async,
    mock_settings,
):
    """
    Tests `create_db_engine` when an `IOError` occurs while attempting to
    write the `DO_DB_SSL_CERT_CONTENT` to a temporary file.
    Ensures the function returns `None` and logs an error.
    """
    # Configure settings with SSL cert content.
    db_url_initial = "postgresql://user:pass@host:port/db"
    cert_content = "-----BEGIN CERTIFICATE-----\n...cert...\n-----END CERTIFICATE-----"
    io_error = IOError("Permission denied to write cert")

    mock_settings.DATABASE_URL = db_url_initial
    mock_settings.DEBUG = False
    mock_settings.DO_DB_SSL_CERT_PATH = None
    mock_settings.DO_DB_SSL_CERT_CONTENT = cert_content
    mock_settings.SQLALCHEMY_POOL_SIZE = 5
    mock_settings.SQLALCHEMY_MAX_OVERFLOW = 2
    mock_settings.SQLALCHEMY_POOL_RECYCLE = 1800

    # Simulate IOError during file writing.
    mock_builtin_open.side_effect = io_error

    # Call the function under test.
    engine = create_db_engine()

    # Assertions.
    assert engine is None
    mock_builtin_open.assert_called_once_with(RUNTIME_CA_CERT_PATH, "w")
    mock_logger.error.assert_called_once_with(
        f"Failed to write CA certificate content to {RUNTIME_CA_CERT_PATH}: {io_error}",
        exc_info=True,
    )
    mock_create_async.assert_not_called()
    mock_os_path_exists.assert_not_called()
    mock_os_remove.assert_not_called()


@patch("app.db.engine.settings")
@patch("app.db.engine.create_async_engine")
@patch("app.db.engine.logger")
@patch("ssl.create_default_context")
@patch("builtins.open", new_callable=MagicMock)
@patch("app.db.engine.os.remove")
@patch("app.db.engine.os.path.exists")
def test_create_db_engine_ssl_context_creation_fails_from_content(
    mock_os_path_exists,
    mock_os_remove,
    mock_builtin_open,
    mock_ssl_create_context,
    mock_logger,
    mock_create_async,
    mock_settings,
):
    """
    Tests `create_db_engine` when SSL context creation fails after writing
    `DO_DB_SSL_CERT_CONTENT` to a temporary file. Ensures proper error logging
    and cleanup of the temporary file.
    """
    # Configure settings with SSL cert content.
    db_url_initial = "postgresql://user:pass@host:port/db"
    cert_content = "-----BEGIN CERTIFICATE-----\n...cert...\n-----END CERTIFICATE-----"
    ssl_error = ssl.SSLError("Bad cert from content file")

    mock_settings.DATABASE_URL = db_url_initial
    mock_settings.DEBUG = False
    mock_settings.DO_DB_SSL_CERT_PATH = None
    mock_settings.DO_DB_SSL_CERT_CONTENT = cert_content
    mock_settings.SQLALCHEMY_POOL_SIZE = 5
    mock_settings.SQLALCHEMY_MAX_OVERFLOW = 2
    mock_settings.SQLALCHEMY_POOL_RECYCLE = 1800

    # Mock dependencies for this failure scenario.
    mock_file_handle = MagicMock()
    mock_builtin_open.return_value.__enter__.return_value = mock_file_handle
    mock_ssl_create_context.side_effect = ssl_error
    mock_os_path_exists.return_value = True # For the 'finally' block cleanup check.

    # Call the function under test.
    engine = create_db_engine()

    # Assertions.
    assert engine is None
    mock_builtin_open.assert_called_once_with(RUNTIME_CA_CERT_PATH, "w")
    mock_file_handle.write.assert_called_once_with(cert_content)
    mock_ssl_create_context.assert_called_once_with(
        ssl.Purpose.SERVER_AUTH, cafile=RUNTIME_CA_CERT_PATH
    )
    mock_logger.error.assert_called_once_with(
        f"Error creating SSLContext with CA '{RUNTIME_CA_CERT_PATH}' for PgBouncer: {ssl_error}."
    )
    mock_create_async.assert_not_called()
    mock_os_path_exists.assert_called_once_with(RUNTIME_CA_CERT_PATH)
    mock_os_remove.assert_called_once_with(RUNTIME_CA_CERT_PATH) # Verify cleanup.


@patch("app.db.engine.settings")
@patch("app.db.engine.create_async_engine")
def test_create_db_engine_with_url_query_params_stripping(
    mock_create_async, mock_settings
):
    """
    Tests that specific SSL-related query parameters are stripped from the
    DATABASE_URL before passing it to SQLAlchemy's create_async_engine,
    as these should be handled via `connect_args`.
    """
    # Define a URL with query parameters that should be stripped.
    db_url_with_query = "postgresql://user:pass@host/db?sslmode=verify-full&otherparam=value&sslrootcert=file.pem&appname=test"
    expected_engine_url = (
        "postgresql+asyncpg://user:pass@host/db?otherparam=value&appname=test"
    )

    mock_settings.DATABASE_URL = db_url_with_query
    mock_settings.DEBUG = False
    mock_settings.DO_DB_SSL_CERT_PATH = None
    mock_settings.DO_DB_SSL_CERT_CONTENT = None
    mock_settings.SQLALCHEMY_POOL_SIZE = 7
    mock_settings.SQLALCHEMY_MAX_OVERFLOW = 3
    mock_settings.SQLALCHEMY_POOL_RECYCLE = 900

    # Mock engine.
    mock_engine = MagicMock(spec=AsyncEngine)
    mock_create_async.return_value = mock_engine

    # Call the function under test.
    engine = create_db_engine()
    assert engine is mock_engine
    expected_connect_args = {"ssl": "require"}
    mock_create_async.assert_called_once_with(
        expected_engine_url, # Verify stripped URL.
        echo=False,
        pool_pre_ping=True,
        connect_args=expected_connect_args,
        pool_size=7,
        max_overflow=3,
        pool_recycle=900,
    )


@patch("app.db.engine.settings")
@patch("app.db.engine.create_async_engine")
def test_create_db_engine_pydantic_v1_url_object(mock_create_async, mock_settings):
    """
    Tests `create_db_engine` with a Pydantic V1 `PostgresDsn` or similar object,
    which uses `unicode_string` for its raw value.
    """
    # Simulate a Pydantic V1 URL object.
    mock_db_url_v1 = MagicMock()
    mock_db_url_v1.unicode_string = MagicMock(
        return_value="postgresql://user:v1@host/db_v1"
    )
    mock_db_url_v1.render_as_string = MagicMock(return_value=None) # Not used in V1.

    mock_settings.DATABASE_URL = mock_db_url_v1
    mock_settings.DEBUG = True
    mock_settings.DO_DB_SSL_CERT_PATH = None
    mock_settings.DO_DB_SSL_CERT_CONTENT = None
    mock_settings.SQLALCHEMY_POOL_SIZE = 5
    mock_settings.SQLALCHEMY_MAX_OVERFLOW = 2
    mock_settings.SQLALCHEMY_POOL_RECYCLE = 1800

    # Mock engine.
    mock_engine = MagicMock(spec=AsyncEngine)
    mock_create_async.return_value = mock_engine
    # Call the function under test.
    engine = create_db_engine()

    # Assertions.
    assert engine is mock_engine
    mock_db_url_v1.unicode_string.assert_called_once()
    mock_db_url_v1.render_as_string.assert_not_called()
    expected_url = "postgresql+asyncpg://user:v1@host/db_v1"
    mock_create_async.assert_called_once_with(
        expected_url,
        echo=True,
        pool_pre_ping=True,
        connect_args={"ssl": "require"},
        pool_size=5,
        max_overflow=2,
        pool_recycle=1800,
    )


@patch("app.db.engine.settings")
@patch("app.db.engine.create_async_engine")
def test_create_db_engine_pydantic_v2_url_object(mock_create_async, mock_settings):
    """
    Tests `create_db_engine` with a Pydantic V2 `PostgresDsn` or similar object,
    which uses `render_as_string` for its raw value.
    """
    # Simulate a Pydantic V2 URL object.
    mock_db_url_v2 = MagicMock()
    mock_db_url_v2.unicode_string = MagicMock(return_value=None) # Not used in V2.
    mock_db_url_v2.render_as_string = MagicMock(
        return_value="postgresql://user:v2@host/db_v2"
    )

    mock_settings.DATABASE_URL = mock_db_url_v2
    mock_settings.DEBUG = False
    mock_settings.DO_DB_SSL_CERT_PATH = None
    mock_settings.DO_DB_SSL_CERT_CONTENT = None
    mock_settings.SQLALCHEMY_POOL_SIZE = 5
    mock_settings.SQLALCHEMY_MAX_OVERFLOW = 2
    mock_settings.SQLALCHEMY_POOL_RECYCLE = 1800

    # Mock engine.
    mock_engine = MagicMock(spec=AsyncEngine)
    mock_create_async.return_value = mock_engine
    # Call the function under test.
    engine = create_db_engine()

    # Assertions.
    assert engine is mock_engine
    mock_db_url_v2.unicode_string.assert_called_once()
    mock_db_url_v2.render_as_string.assert_called_once_with(hide_password=False)
    expected_url = "postgresql+asyncpg://user:v2@host/db_v2"
    mock_create_async.assert_called_once_with(
        expected_url,
        echo=False,
        pool_pre_ping=True,
        connect_args={"ssl": "require"},
        pool_size=5,
        max_overflow=2,
        pool_recycle=1800,
    )


@patch("app.db.engine.settings")
@patch("app.db.engine.create_async_engine")
@patch("app.db.engine.logger")
def test_create_db_engine_incorrect_url_scheme(
    mock_logger, mock_create_async, mock_settings
):
    """
    Tests `create_db_engine` when `DATABASE_URL` has an unsupported scheme.
    Ensures the function returns `None` and logs an error.
    """
    # Configure settings with an unsupported database scheme.
    mock_settings.DATABASE_URL = "mysql://user:pass@host/db"
    mock_settings.DEBUG = False
    mock_settings.DO_DB_SSL_CERT_PATH = None
    mock_settings.DO_DB_SSL_CERT_CONTENT = None
    mock_settings.SQLALCHEMY_POOL_SIZE = 5
    mock_settings.SQLALCHEMY_MAX_OVERFLOW = 2
    mock_settings.SQLALCHEMY_POOL_RECYCLE = 1800

    # Call the function under test.
    engine = create_db_engine()

    # Assertions.
    assert engine is None
    mock_logger.error.assert_called_once_with(
        "DATABASE_URL (scheme: 'mysql') must start with 'postgresql://' or 'postgresql+asyncpg://'."
    )
    mock_create_async.assert_not_called()