"""Unit-of-work contract and in-memory transactional adapter."""

from __future__ import annotations

from enum import Enum
from typing import Protocol, Self

from .memory import InMemoryRepository


class UnitOfWork(Protocol):
    """Explicit transaction boundary."""

    def __enter__(self) -> Self:
        """Begin a transaction."""

    def commit(self) -> None:
        """Commit all work."""

    def rollback(self) -> None:
        """Undo all uncommitted work."""

    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        """Commit or roll back the active transaction."""


class UnitOfWorkState(Enum):
    READY = "READY"
    ACTIVE = "ACTIVE"
    COMMITTED = "COMMITTED"
    ROLLED_BACK = "ROLLED_BACK"


class InMemoryUnitOfWork:
    """Coordinate transactional snapshots across in-memory repositories."""

    def __init__(self) -> None:
        self._repositories: dict[str, InMemoryRepository] = {}
        self._snapshots: dict[str, dict] = {}
        self._state = UnitOfWorkState.READY

    @property
    def state(self) -> UnitOfWorkState:
        return self._state

    def register_repository(self, name: str, repository: InMemoryRepository) -> None:
        normalized = name.strip()
        if not normalized:
            raise ValueError("Repository name must not be blank.")
        if self._state is UnitOfWorkState.ACTIVE:
            raise RuntimeError("Repositories cannot be registered during a transaction.")
        if normalized in self._repositories:
            raise ValueError(f"Repository {normalized!r} is already registered.")
        self._repositories[normalized] = repository

    def repository(self, name: str) -> InMemoryRepository:
        try:
            return self._repositories[name]
        except KeyError as error:
            raise KeyError(f"Repository {name!r} is not registered.") from error

    def __enter__(self) -> InMemoryUnitOfWork:
        if self._state is UnitOfWorkState.ACTIVE:
            raise RuntimeError("Unit of work is already active.")
        self._snapshots = {
            name: repository.snapshot()
            for name, repository in self._repositories.items()
        }
        self._state = UnitOfWorkState.ACTIVE
        return self

    def commit(self) -> None:
        self._require_active()
        self._snapshots.clear()
        self._state = UnitOfWorkState.COMMITTED

    def rollback(self) -> None:
        self._require_active()
        for name, snapshot in self._snapshots.items():
            self._repositories[name].restore(snapshot)
        self._snapshots.clear()
        self._state = UnitOfWorkState.ROLLED_BACK

    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        del exc_value, traceback
        if self._state is UnitOfWorkState.ACTIVE:
            if exc_type is None:
                self.commit()
            else:
                self.rollback()
        return False

    def _require_active(self) -> None:
        if self._state is not UnitOfWorkState.ACTIVE:
            raise RuntimeError("Unit of work is not active.")
