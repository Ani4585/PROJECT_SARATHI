"""
PROJECT SARATHI

Centralized logging system.
"""

import logging
from logging.handlers import RotatingFileHandler

from config.paths import LOG_DIR
from config.constants import DEFAULT_LOG_LEVEL

LOG_FILE = LOG_DIR / "sarathi.log"

logger = logging.getLogger("sarathi")

if not logger.handlers:
    level = getattr(logging, DEFAULT_LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(level)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=1_000_000,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    logger.propagate = False