"""Unit-of-work contract and in-memory transactional adapter."""

from __future__ import annotations

from enum import Enum
from typing import Protocol, Self

from .memory import InMemoryRepository
from .contracts import PersistenceSession, SessionFactory


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
    FAILED = "FAILED"


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


class SessionUnitOfWork:
    """Coordinate an adapter-provided transactional persistence session."""

    def __init__(self, session_factory: SessionFactory) -> None:
        if not isinstance(session_factory, SessionFactory):
            raise TypeError("Session unit of work requires a session factory.")
        self._session_factory = session_factory
        self._session: PersistenceSession | None = None
        self._state = UnitOfWorkState.READY

    @property
    def state(self) -> UnitOfWorkState:
        return self._state

    @property
    def session(self) -> PersistenceSession:
        if self._state is not UnitOfWorkState.ACTIVE or self._session is None:
            raise RuntimeError("Unit of work is not active.")
        return self._session

    def repository(self, name: str, identity):
        return self.session.repository(name, identity)

    def __enter__(self) -> "SessionUnitOfWork":
        if self._state is UnitOfWorkState.ACTIVE:
            raise RuntimeError("Unit of work is already active.")
        self._session = self._session_factory.open_session()
        try:
            self._session.begin()
        except Exception:
            self._session.close()
            self._session = None
            raise
        self._state = UnitOfWorkState.ACTIVE
        return self

    def commit(self) -> None:
        session = self.session
        try:
            session.commit()
        except Exception:
            self._state = UnitOfWorkState.FAILED
            raise
        self._state = UnitOfWorkState.COMMITTED

    def rollback(self) -> None:
        session = self.session
        session.rollback()
        self._state = UnitOfWorkState.ROLLED_BACK

    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        del exc_value, traceback
        try:
            if self._state is UnitOfWorkState.ACTIVE:
                if exc_type is None:
                    self.commit()
                else:
                    self.rollback()
        finally:
            if self._session is not None:
                self._session.close()
                self._session = None
        return False
