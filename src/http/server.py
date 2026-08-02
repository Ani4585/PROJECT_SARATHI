"""Concrete ASGI server adapter integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from importlib import import_module
from typing import TypeAlias

from .contracts import ASGIApplication
from .exceptions import ServerAdapterUnavailableError


ServerRunner: TypeAlias = Callable[..., object]


@dataclass(frozen=True, slots=True)
class ServerConfiguration:
    """Validated network settings passed to an ASGI server runner."""

    host: str = "127.0.0.1"
    port: int = 8000
    log_level: str = "info"

    def __post_init__(self) -> None:
        if not isinstance(self.host, str) or not self.host.strip():
            raise ValueError("HTTP server host must be a non-blank string.")
        if (
            not isinstance(self.port, int)
            or isinstance(self.port, bool)
            or not 1 <= self.port <= 65535
        ):
            raise ValueError("HTTP server port must be an integer from 1 to 65535.")
        if not isinstance(self.log_level, str) or self.log_level.lower() not in {
            "critical",
            "error",
            "warning",
            "info",
            "debug",
            "trace",
        }:
            raise ValueError("HTTP server log level is invalid.")
        object.__setattr__(self, "host", self.host.strip())
        object.__setattr__(self, "log_level", self.log_level.lower())


class UvicornServerAdapter:
    """Run a SARATHI ASGI application through an optional Uvicorn runner."""

    def __init__(
        self,
        configuration: ServerConfiguration | None = None,
        *,
        runner: ServerRunner | None = None,
    ) -> None:
        if runner is not None and not callable(runner):
            raise TypeError("ASGI server runner must be callable.")
        self.configuration = configuration or ServerConfiguration()
        self._runner = runner

    def run(self, application: ASGIApplication) -> None:
        """Start the configured server and block until it exits."""

        if not callable(application):
            raise TypeError("ASGI application must be callable.")
        runner = self._runner or self._load_runner()
        runner(
            application,
            host=self.configuration.host,
            port=self.configuration.port,
            log_level=self.configuration.log_level,
        )

    @staticmethod
    def _load_runner() -> ServerRunner:
        try:
            module = import_module("uvicorn")
        except ModuleNotFoundError as error:
            raise ServerAdapterUnavailableError(
                "Uvicorn is not installed. Install it before running the HTTP server."
            ) from error
        runner = getattr(module, "run", None)
        if not callable(runner):
            raise ServerAdapterUnavailableError(
                "The installed Uvicorn package does not expose a callable run function."
            )
        return runner
