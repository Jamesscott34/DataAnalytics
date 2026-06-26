"""Structured logging configuration.

Configures JSON application logs and plain-text fallback for local debugging.
Audit events use ``app.utils.logging_utils`` helpers with a dedicated logger name.
"""

import logging
import sys
from logging.config import dictConfig

from app.config import get_settings


def configure_logging() -> None:
    """Apply logging configuration based on application settings."""
    settings = get_settings()
    use_json = settings.log_json and settings.app_env != "test"

    if use_json:
        formatter_name = "json"
        formatter_config = {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
        }
    else:
        formatter_name = "standard"
        formatter_config = {
            "format": "%(asctime)s %(levelname)s [%(name)s] %(message)s",
        }

    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                formatter_name: formatter_config,
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "stream": sys.stdout,
                    "formatter": formatter_name,
                },
            },
            "loggers": {
                "app": {"handlers": ["console"], "level": settings.log_level},
                "app.audit": {"handlers": ["console"], "level": settings.log_level},
                "uvicorn": {"handlers": ["console"], "level": settings.log_level},
            },
            "root": {"handlers": ["console"], "level": settings.log_level},
        }
    )

    logging.getLogger(__name__).debug("Logging configured", extra={"json": use_json})
