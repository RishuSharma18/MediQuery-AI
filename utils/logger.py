"""
utils/logger.py
Centralized logging setup used across the app.
"""
from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler

from config import settings

_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_configured_loggers: set[str] = set()


def get_logger(name: str) -> logging.Logger:
    """Return a configured logger that writes to both console and a rotating file."""
    logger = logging.getLogger(name)

    if name in _configured_loggers:
        return logger

    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(_LOG_FORMAT)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Rotating file handler (5 MB x 3 backups)
    file_handler = RotatingFileHandler(
        settings.APP_LOG_PATH, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    logger.propagate = False
    _configured_loggers.add(name)
    return logger