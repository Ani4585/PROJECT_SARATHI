"""Persistence composition root and runtime lifecycle."""

from __future__ import annotations

from collections.abc import Mapping

from .configuration import PersistenceSettings
from .contracts import SessionFactory
from .database import InMemoryConnection, InMemoryDatabase
from .exceptions import PersistenceConnectionError
from .unit_of_work import SessionUnitOfWork


class PersistenceRuntime:
    def __init__(self, settings: PersistenceSettings) -> None:
        self.settings = settings
        self.database = InMemoryDatabase(settings.database_name)
        self._connection: InMemoryConnection | None = None

    @property
    def healthy(self) -> bool:
        return self._connection is not None and self._connection.healthy

    @property
    def session_factory(self) -> SessionFactory:
        if self._connection is None or not self._connection.healthy:
            raise PersistenceConnectionError("Persistence runtime is not open.")
        return self._connection

    def open(self) -> "PersistenceRuntime":
        if self.healthy:
            return self
        self.database.open()
        self._connection = self.database.connect()
        return self

    def unit_of_work(self) -> SessionUnitOfWork:
        return SessionUnitOfWork(self.session_factory)

    def close(self) -> None:
        if self._connection is not None:
            self._connection.close()
            self._connection = None
        self.database.close()

    def __enter__(self) -> "PersistenceRuntime":
        return self.open()

    def __exit__(self, exc_type, exc, traceback) -> bool:
        del exc_type, exc, traceback
        self.close()
        return False


def create_persistence_runtime(
    configuration: PersistenceSettings | Mapping[str, object] | object | None = None,
) -> PersistenceRuntime:
    if configuration is None:
        settings = PersistenceSettings()
    elif isinstance(configuration, PersistenceSettings):
        settings = configuration
    else:
        settings = PersistenceSettings.from_configuration(configuration)
    return PersistenceRuntime(settings)
