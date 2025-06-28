import logging
import logging.config
import sys

from app.core.config import Settings
from app.core.logging_filters import RequestIdFilter, EndpointFilter


def setup_logging(settings: Settings):
    """Configures logging based on application settings."""

    # Determine formatter based on environment
    log_formatter = "json" if settings.ENVIRONMENT == "production" else "standard"
    log_level = settings.LOG_LEVEL.upper()

    # Define logging configuration dictionary
    LOGGING_CONFIG = {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {
            "request_id": {
                "()": RequestIdFilter,
            },
            "health_check_filter": {
                "()": EndpointFilter,
                "path": "/health",
            },
        },
        "formatters": {
            "standard": {
                # Add request_id to the standard format
                "format": "%(asctime)s - [%(request_id)s] - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "json": {
                "()": "pythonjsonlogger.json.JsonFormatter",  
                # Add request_id to the JSON format
                "format": "%(asctime)s %(name)s %(levelname)s %(request_id)s %(message)s %(pathname)s %(lineno)d",
                "datefmt": "%Y-%m-%dT%H:%M:%S%z",
            },
        },
        "handlers": {
            "console": {
                "level": log_level,
                "class": "logging.StreamHandler",
                "formatter": log_formatter,
                "stream": sys.stdout,
                "filters": [
                    "request_id"
                ],  # Apply request_id filter to general console logs
            },
            "access_console": {
                "level": log_level,
                "class": "logging.StreamHandler",
                "formatter": log_formatter,
                "stream": sys.stdout,
                "filters": ["request_id", "health_check_filter"],
            },
        },
        "loggers": {
            "": { 
                "handlers": ["console"],
                "level": log_level,
                "propagate": True,
            },
            "uvicorn.error": {
                "handlers": ["console"],
                "level": log_level,
                "propagate": False,  # Prevent duplicate logs in root
            },
            "uvicorn.access": {
                "handlers": ["access_console"],  # Use the dedicated access handler
                "level": log_level,
                "propagate": False,  # Keep propagation off
            },
            "sqlalchemy.engine": {
                "handlers": ["console"],
                "level": "WARNING",  # Reduce SQLAlchemy noise unless debugging
                "propagate": False,
            },
        },
    }

    # Apply the logging configuration
    logging.config.dictConfig(LOGGING_CONFIG)
    logging.getLogger(__name__).info("Logging configured successfully.")
