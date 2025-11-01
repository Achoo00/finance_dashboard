"""Logging configuration for the application."""
import logging
import logging.config
import os
from pathlib import Path
from typing import Any, Dict, Optional

from app.config.settings import settings


def setup_logging(
    log_level: Optional[str] = None,
    log_file: Optional[str] = None,
) -> None:
    """Set up logging configuration.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file. If None, logs to console only.
    """
    log_level = log_level or settings.LOG_LEVEL
    log_file = log_file or str(settings.LOGS_DIR / "finance_dashboard.log")

    # Ensure log directory exists
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    # Define log format
    log_format = settings.LOG_FORMAT

    # Configure logging
    log_config: Dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": log_format,
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "json": {
                "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "level": log_level,
                "class": "logging.StreamHandler",
                "formatter": "standard",
                "stream": "ext://sys.stdout",
            },
            "file": {
                "level": log_level,
                "class": "logging.handlers.RotatingFileHandler",
                "filename": log_file,
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "formatter": "standard",
                "encoding": "utf8",
            },
        },
        "loggers": {
            "app": {
                "handlers": ["console", "file"],
                "level": log_level,
                "propagate": False,
            },
            "uvicorn": {
                "handlers": ["console", "file"],
                "level": log_level,
                "propagate": False,
            },
            "sqlalchemy": {
                "handlers": ["console", "file"],
                "level": "WARNING",  # Reduce SQLAlchemy log level
                "propagate": False,
            },
        },
        "root": {
            "handlers": ["console", "file"],
            "level": log_level,
        },
    }

    # Apply the configuration
    logging.config.dictConfig(log_config)

    # Set log level for all loggers
    logging.getLogger().setLevel(log_level)
    for logger_name in logging.root.manager.loggerDict:
        if logger_name.startswith("app"):
            logging.getLogger(logger_name).setLevel(log_level)

    # Configure SQLAlchemy logging
    if settings.DEBUG:
        logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
    else:
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


# Initialize logging when the module is imported
setup_logging()

# Create a logger for this module
logger = logging.getLogger(__name__)
