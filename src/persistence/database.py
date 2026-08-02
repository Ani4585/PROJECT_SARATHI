"""Transactional in-memory reference persistence adapter."""

from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy
from enum import StrEnum
from threading import RLock
from typing import Generic, TypeVar, cast

from .exceptions import (
    ActiveSessionError,
    EntityAlreadyExistsError,
    EntityNotFoundError,
    PersistenceConnectionError,
    PersistenceSessionError,
    TransactionConflictError,
)


EntityT = TypeVar("EntityT")
IdentifierT = TypeVar("IdentifierT")


class DatabaseState(StrEnum):
    CLOSED = "closed"
    CLOSING = "closing"
    OPEN = "open"


class SessionState(StrEnum):
    READY = "ready"
    ACTIVE = "active"
    COMMITTED = "committed"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"
    CLOSED = "closed"


class InMemoryDatabase:
    """Shared versioned data store used by the reference adapter."""

    def __init__(self, name: str = "sarathi") -> None:
        normalized = name.strip()
        if not normalized:
            raise ValueError("Database name must not be blank.")
        self._name = normalized
        self._tables: dict[str, dict[object, object]] = {}
        self._version = 0
        self._state = DatabaseState.CLOSED
        self._connections: set[InMemoryConnection] = set()
        self._lock = RLock()

    @property
    def name(self) -> str:
        return self._name

    @property
    def state(self) -> DatabaseState:
        with self._lock:
            return self._state

    @property
    def version(self) -> int:
        with self._lock:
            return self._version

    @property
    def healthy(self) -> bool:
        return self.state is DatabaseState.OPEN

    def open(self) -> "InMemoryDatabase":
        with self._lock:
            if self._state is DatabaseState.CLOSING:
                raise PersistenceConnectionError("Database is currently closing.")
            self._state = DatabaseState.OPEN
            return self

    def connect(self) -> "InMemoryConnection":
        with self._lock:
            if self._state is not DatabaseState.OPEN:
                raise PersistenceConnectionError("Database is not open.")
            connection = InMemoryConnection(self)
            self._connections.add(connection)
            return connection

    def close(self) -> None:
        with self._lock:
            if self._state is DatabaseState.CLOSED:
                return
            self._state = DatabaseState.CLOSING
            connections = tuple(self._connections)
        active = tuple(connection for connection in connections if connection.is_open)
        if active:
            with self._lock:
                self._state = DatabaseState.OPEN
            raise PersistenceConnectionError(
                f"Database has {len(active)} open connection(s)."
            )
        with self._lock:
            self._state = DatabaseState.CLOSED

    def _snapshot(self) -> tuple[int, dict[str, dict[object, object]]]:
        with self._lock:
            if self._state is not DatabaseState.OPEN:
                raise PersistenceConnectionError("Database is not open.")
            return self._version, deepcopy(self._tables)

    def _commit(
        self,
        base_version: int,
        tables: dict[str, dict[object, object]],
    ) -> int:
        with self._lock:
            if self._state is not DatabaseState.OPEN:
                raise PersistenceConnectionError("Database is not open.")
            if base_version != self._version:
                raise TransactionConflictError(
                    "Transaction conflicts with a newer committed database version."
                )
            self._tables = deepcopy(tables)
            self._version += 1
            return self._version

    def _discard_connection(self, connection: "InMemoryConnection") -> None:
        with self._lock:
            self._connections.discard(connection)


class InMemoryConnection:
    """Own sessions created against one open in-memory database."""

    def __init__(self, database: InMemoryDatabase) -> None:
        self._database = database
        self._sessions: set[InMemorySession] = set()
        self._open = True
        self._lock = RLock()

    @property
    def healthy(self) -> bool:
        with self._lock:
            return self._open and self._database.healthy

    @property
    def is_open(self) -> bool:
        with self._lock:
            return self._open

    @property
    def active_sessions(self) -> int:
        with self._lock:
            return sum(session.state is SessionState.ACTIVE for session in self._sessions)

    def open_session(self) -> "InMemorySession":
        with self._lock:
            if not self.healthy:
                raise PersistenceConnectionError("Persistence connection is not open.")
            session = InMemorySession(self, self._database)
            self._sessions.add(session)
            return session

    def close(self) -> None:
        with self._lock:
            if not self._open:
                return
            self._open = False
            sessions = tuple(self._sessions)
        active = tuple(
            session for session in sessions if session.state is SessionState.ACTIVE
        )
        if active:
            with self._lock:
                self._open = True
            raise ActiveSessionError(
                f"Connection has {len(active)} active session(s)."
            )
        for session in sessions:
            session.close()
        self._database._discard_connection(self)

    def _discard_session(self, session: "InMemorySession") -> None:
        with self._lock:
            self._sessions.discard(session)


class InMemorySession:
    """Isolated transactional view of all reference-adapter tables."""

    def __init__(
        self,
        connection: InMemoryConnection,
        database: InMemoryDatabase,
    ) -> None:
        self._connection = connection
        self._database = database
        self._state = SessionState.READY
        self._base_version: int | None = None
        self._tables: dict[str, dict[object, object]] | None = None
        self._lock = RLock()

    @property
    def state(self) -> SessionState:
        with self._lock:
            return self._state

    def begin(self) -> None:
        with self._lock:
            if self._state is not SessionState.READY:
                raise PersistenceSessionError(
                    f"Session cannot begin from state {self._state.value}."
                )
            if not self._connection.healthy:
                raise PersistenceConnectionError("Persistence connection is not open.")
            self._base_version, self._tables = self._database._snapshot()
            self._state = SessionState.ACTIVE

    def repository(
        self,
        name: str,
        identity: Callable[[EntityT], IdentifierT],
    ) -> "InMemorySessionRepository[EntityT, IdentifierT]":
        normalized = name.strip()
        if not normalized:
            raise ValueError("Repository name must not be blank.")
        if not callable(identity):
            raise TypeError("Repository identity selector must be callable.")
        self._require_active()
        return InMemorySessionRepository(self, normalized, identity)

    def commit(self) -> None:
        with self._lock:
            self._require_active()
            assert self._base_version is not None and self._tables is not None
            try:
                self._database._commit(self._base_version, self._tables)
            except Exception:
                self._state = SessionState.FAILED
                raise
            self._tables = None
            self._base_version = None
            self._state = SessionState.COMMITTED

    def rollback(self) -> None:
        with self._lock:
            self._require_active()
            self._tables = None
            self._base_version = None
            self._state = SessionState.ROLLED_BACK

    def close(self) -> None:
        with self._lock:
            if self._state is SessionState.CLOSED:
                return
            if self._state is SessionState.ACTIVE:
                self.rollback()
            self._tables = None
            self._base_version = None
            self._state = SessionState.CLOSED
            self._connection._discard_session(self)

    def _table(self, name: str) -> dict[object, object]:
        self._require_active()
        assert self._tables is not None
        return self._tables.setdefault(name, {})

    def _require_active(self) -> None:
        if self._state is not SessionState.ACTIVE:
            raise PersistenceSessionError("Persistence session is not active.")

    def __enter__(self) -> "InMemorySession":
        self.begin()
        return self

    def __exit__(self, exc_type, exc, traceback) -> bool:
        del exc, traceback
        try:
            if self._state is SessionState.ACTIVE:
                if exc_type is None:
                    self.commit()
                else:
                    self.rollback()
        finally:
            self.close()
        return False


class InMemorySessionRepository(Generic[EntityT, IdentifierT]):
    """Repository view bound to one active session and named table."""

    def __init__(
        self,
        session: InMemorySession,
        name: str,
        identity: Callable[[EntityT], IdentifierT],
    ) -> None:
        self._session = session
        self._name = name
        self._identity = identity

    def add(self, entity: EntityT) -> None:
        table = self._table()
        identifier = self._identity(entity)
        if identifier in table:
            raise EntityAlreadyExistsError(identifier)
        table[identifier] = entity

    def get(self, identifier: IdentifierT) -> EntityT | None:
        return cast(EntityT | None, self._table().get(identifier))

    def require(self, identifier: IdentifierT) -> EntityT:
        entity = self.get(identifier)
        if entity is None:
            raise EntityNotFoundError(identifier)
        return entity

    def remove(self, identifier: IdentifierT) -> EntityT:
        try:
            return cast(EntityT, self._table().pop(identifier))
        except KeyError as error:
            raise EntityNotFoundError(identifier) from error

    def list(self) -> tuple[EntityT, ...]:
        return cast(tuple[EntityT, ...], tuple(self._table().values()))

    def __len__(self) -> int:
        return len(self._table())

    def _table(self) -> dict[object, object]:
        return self._session._table(self._name)
