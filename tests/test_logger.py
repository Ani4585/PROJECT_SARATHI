"""Tests for resilient centralized logger configuration."""

from __future__ import annotations

import logging
from pathlib import Path

from src.utils.logger import configure_logger


def test_unwritable_log_file_falls_back_to_console(tmp_path: Path) -> None:
    candidate = logging.Logger("sarathi-test-fallback")

    def denied(*args, **kwargs):
        del args, kwargs
        raise PermissionError("blocked")

    configured = configure_logger(
        candidate,
        log_file=tmp_path / "sarathi.log",
        file_handler_factory=denied,
    )
    assert configured is candidate
    assert len(candidate.handlers) == 1
    assert isinstance(candidate.handlers[0], logging.StreamHandler)
    assert candidate.propagate is False


def test_logger_configuration_is_idempotent(tmp_path: Path) -> None:
    candidate = logging.Logger("sarathi-test-idempotent")
    existing = logging.NullHandler()
    candidate.addHandler(existing)
    configured = configure_logger(candidate, log_file=tmp_path / "unused.log")
    assert configured.handlers == [existing]
