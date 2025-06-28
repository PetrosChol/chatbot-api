import logging
import ssl
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from urllib.parse import urlparse, urlunparse
import os

from app.core.config import settings 

logger = logging.getLogger(__name__)

RUNTIME_CA_CERT_PATH = "/tmp/do_ca_certificate.crt"


def _mask_url_password(db_url_str: Optional[str]) -> str:
    """Masks the password in a database URL string."""
    if not db_url_str:
        return "URL not provided"
    try:
        parsed_url = urlparse(db_url_str)
        if parsed_url.password:
            netloc_parts = parsed_url.netloc.split("@", 1)
            if ":" in netloc_parts[0]:
                user_part = netloc_parts[0].split(":", 1)[0]
                new_netloc = f"{user_part}:********"
                if len(netloc_parts) > 1:
                    new_netloc += f"@{netloc_parts[1]}"
                parsed_url = parsed_url._replace(netloc=new_netloc)
        return urlunparse(parsed_url)
    except Exception:
        return "Error parsing URL for masking"


def create_db_engine() -> Optional[AsyncEngine]:
    """
    Creates the SQLAlchemy async engine with proper SSL configuration for DigitalOcean
    using connect_args for asyncpg.
    Prioritizes CA certificate content from environment variable, then falls back to path.
    Connects to the DATABASE_URL which should be the PgBouncer URI.
    """
    runtime_ca_cert_created_from_content = False 

    try:
        masked_db_url_for_log = _mask_url_password(str(settings.DATABASE_URL))
        logger.info(
            f"Attempting to create DB engine. DATABASE_URL (should be PgBouncer URI): '{masked_db_url_for_log}'"
        )
        logger.debug(
            f"DO_DB_SSL_CERT_PATH (file path setting): '{settings.DO_DB_SSL_CERT_PATH}'"
        )
        logger.debug(
            f"DO_DB_SSL_CERT_CONTENT (env content setting) is set: {bool(settings.DO_DB_SSL_CERT_CONTENT)}"
        )
        logger.debug(f"DEBUG mode from settings: {settings.DEBUG}")

        if settings.DATABASE_URL is None:
            logger.error("DATABASE_URL is None in settings. Cannot create DB engine.")
            return None

        db_url_initial_str: Optional[str] = None
        if hasattr(settings.DATABASE_URL, "unicode_string"):
            method_val = settings.DATABASE_URL.unicode_string()
            if isinstance(method_val, str):
                db_url_initial_str = method_val
        if db_url_initial_str is None and hasattr(
            settings.DATABASE_URL, "render_as_string"
        ):
            method_val = settings.DATABASE_URL.render_as_string(hide_password=False)
            if isinstance(method_val, str):
                db_url_initial_str = method_val
        if db_url_initial_str is None and isinstance(settings.DATABASE_URL, str):
            db_url_initial_str = settings.DATABASE_URL

        if not db_url_initial_str:
            logger.error(
                "DATABASE_URL resolved to None or an empty string. Cannot create DB engine."
            )
            return None

        logger.info(
            "Constructing database engine configuration to connect to PgBouncer..."
        )

        final_db_url_for_engine: str
        scheme_adjusted_url_parts = []
        if db_url_initial_str.startswith("postgresql://"):
            scheme_adjusted_url_parts = db_url_initial_str.split("?", 1)
            base_dsn_part = scheme_adjusted_url_parts[0].replace(
                "postgresql://", "postgresql+asyncpg://", 1
            )
        elif db_url_initial_str.startswith("postgresql+asyncpg://"):
            scheme_adjusted_url_parts = db_url_initial_str.split("?", 1)
            base_dsn_part = scheme_adjusted_url_parts[0]
        else:
            logger.error(
                f"DATABASE_URL (scheme: '{urlparse(db_url_initial_str).scheme}') must start with 'postgresql://' or 'postgresql+asyncpg://'."
            )
            return None

        if len(scheme_adjusted_url_parts) > 1 and scheme_adjusted_url_parts[1]:
            original_query = scheme_adjusted_url_parts[1]
            other_query_params = "&".join(
                p
                for p in original_query.split("&")
                if not p.startswith("sslmode=") and not p.startswith("sslrootcert=")
            )
            if other_query_params:
                final_db_url_for_engine = f"{base_dsn_part}?{other_query_params}"
            else:
                final_db_url_for_engine = base_dsn_part
        else:
            final_db_url_for_engine = base_dsn_part

        logger.debug(
            f"Base DSN for engine (scheme adjusted, SSL query params stripped, password masked): {_mask_url_password(final_db_url_for_engine)}"
        )

        connect_args = {}
        ssl_config_applied_log_msg = (
            "No specific SSL configuration applied via connect_args."
        )
        effective_ca_cert_path: Optional[str] = None
        # runtime_ca_cert_created_from_content is already initialized at the function start

        # SSL Configuration for connection to PgBouncer (it also needs the CA cert)
        if settings.DO_DB_SSL_CERT_CONTENT and settings.DO_DB_SSL_CERT_CONTENT.strip():
            try:
                if "-----BEGIN CERTIFICATE-----" not in settings.DO_DB_SSL_CERT_CONTENT:
                    logger.warning(
                        "DO_DB_SSL_CERT_CONTENT does not appear to be a valid certificate. Will attempt to proceed without custom CA if no path is set."
                    )
                else:
                    with open(RUNTIME_CA_CERT_PATH, "w") as f:
                        f.write(settings.DO_DB_SSL_CERT_CONTENT)
                    effective_ca_cert_path = RUNTIME_CA_CERT_PATH
                    runtime_ca_cert_created_from_content = True
                    logger.info(
                        f"CA certificate content from DO_DB_SSL_CERT_CONTENT written to {RUNTIME_CA_CERT_PATH} for PgBouncer connection."
                    )
            except IOError as e:
                logger.error(
                    f"Failed to write CA certificate content to {RUNTIME_CA_CERT_PATH}: {e}",
                    exc_info=True,
                )
                return None
            except Exception as e:
                logger.error(
                    f"Unexpected error processing DO_DB_SSL_CERT_CONTENT: {e}",
                    exc_info=True,
                )
                return None

        if not effective_ca_cert_path and settings.DO_DB_SSL_CERT_PATH:
            if os.path.exists(settings.DO_DB_SSL_CERT_PATH):
                effective_ca_cert_path = settings.DO_DB_SSL_CERT_PATH
                logger.info(
                    f"Using CA certificate from file path: {effective_ca_cert_path} for PgBouncer connection."
                )
            else:
                logger.warning(
                    f"DO_DB_SSL_CERT_PATH ('{settings.DO_DB_SSL_CERT_PATH}') provided but file not found. Will attempt to proceed without custom CA."
                )

        if effective_ca_cert_path:
            try:
                logger.debug(
                    f"Attempting to create SSLContext with cafile: {effective_ca_cert_path} for PgBouncer connection."
                )
                ssl_context = ssl.create_default_context(
                    ssl.Purpose.SERVER_AUTH, cafile=effective_ca_cert_path
                )
                connect_args["ssl"] = ssl_context
                ssl_config_applied_log_msg = f"SSL Configuration for PgBouncer: Using SSLContext with cafile: {effective_ca_cert_path}"
            except (
                FileNotFoundError
            ):  # Handles if effective_ca_cert_path (from content or path) is not found by create_default_context
                logger.error(
                    f"Effective CA certificate path ('{effective_ca_cert_path}') not found for PgBouncer."
                )
                return None
            except ssl.SSLError as e:
                logger.error(
                    f"Error creating SSLContext with CA '{effective_ca_cert_path}' for PgBouncer: {e}."
                )
                return None
            except Exception as e:
                logger.error(
                    f"Unexpected error creating SSLContext with CA '{effective_ca_cert_path}' for PgBouncer: {e}",
                    exc_info=True,
                )
                return None
        else:
            connect_args["ssl"] = "require"
            ssl_config_applied_log_msg = (
                "SSL Configuration for PgBouncer: No valid CA certificate provided. Using 'ssl': 'require'. "
                "PgBouncer server certificate will not be verified against a specific CA."
            )

        logger.info(ssl_config_applied_log_msg)
        log_dsn = _mask_url_password(final_db_url_for_engine)
        logger.info(
            f"Attempting to create SQLAlchemy engine to connect to PgBouncer at: {log_dsn}"
        )
        logger.debug(
            f"Full DSN for create_async_engine (password masked): {_mask_url_password(final_db_url_for_engine)}"
        )
        logger.debug(f"Connect_args for create_async_engine: {connect_args}")

        # Engine creation itself
        sqlalchemy_pool_size = getattr(settings, "SQLALCHEMY_POOL_SIZE", 5)
        sqlalchemy_max_overflow = getattr(settings, "SQLALCHEMY_MAX_OVERFLOW", 2)
        sqlalchemy_pool_recycle = getattr(settings, "SQLALCHEMY_POOL_RECYCLE", 1800)

        logger.info(
            f"SQLAlchemy pool settings: size={sqlalchemy_pool_size}, max_overflow={sqlalchemy_max_overflow}, recycle={sqlalchemy_pool_recycle} seconds."
        )

        engine_parameters = {
            "echo": settings.DEBUG,
            "pool_pre_ping": True,
            "connect_args": connect_args,
            "pool_size": sqlalchemy_pool_size,
            "max_overflow": sqlalchemy_max_overflow,
            "pool_recycle": sqlalchemy_pool_recycle,
        }

        engine: AsyncEngine = create_async_engine( 
            final_db_url_for_engine, **engine_parameters
        )
        logger.info("SQLAlchemy database engine (to PgBouncer) created successfully.")
        return engine

    except (
        Exception
    ) as e_main:  # Catch any other unexpected errors from the main body of the function
        # This could be an error from create_async_engine if not caught by a more specific try/except,
        # or any other unhandled error in the setup process.
        logger.error(
            f"Unhandled exception during DB engine creation process: {e_main}",
            exc_info=True,
        )
        return None  # Ensure None is returned on unhandled failure

    finally:
        if runtime_ca_cert_created_from_content and os.path.exists(
            RUNTIME_CA_CERT_PATH
        ):
            try:
                os.remove(RUNTIME_CA_CERT_PATH)
                logger.debug(
                    f"Removed temporary CA certificate: {RUNTIME_CA_CERT_PATH}"
                )
            except OSError as e_rm:
                logger.warning(
                    f"Could not remove temporary CA certificate {RUNTIME_CA_CERT_PATH}: {e_rm}"
                )
