"""
PROJECT SARATHI

Centralized logging system.
"""

import logging
from collections.abc import Callable
from logging.handlers import RotatingFileHandler
from pathlib import Path

from config.paths import LOG_DIR
from config.constants import DEFAULT_LOG_LEVEL

LOG_FILE = LOG_DIR / "sarathi.log"

def configure_logger(
    target: logging.Logger | None = None,
    *,
    log_file: Path = LOG_FILE,
    file_handler_factory: Callable[..., logging.Handler] = RotatingFileHandler,
) -> logging.Logger:
    """Configure console logging and optional failure-tolerant file logging."""

    target = target or logging.getLogger("sarathi")
    if target.handlers:
        return target
    level = getattr(logging, DEFAULT_LOG_LEVEL.upper(), logging.INFO)
    target.setLevel(level)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    target.addHandler(console_handler)
    try:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = file_handler_factory(
            log_file,
            maxBytes=1_000_000,
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        target.addHandler(file_handler)
    except OSError as error:
        target.warning(
            "File logging is unavailable; continuing with console logging (%s).",
            type(error).__name__,
        )
    target.propagate = False
    return target


logger = configure_logger()
