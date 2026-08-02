"""Connection and session contracts for persistence adapters."""

from __future__ import annotations

from typing import Protocol, Self, TypeVar, runtime_checkable

from .repository import Repository


EntityT = TypeVar("EntityT")
IdentifierT = TypeVar("IdentifierT")


@runtime_checkable
class PersistenceSession(Protocol):
    def begin(self) -> None: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...

    def repository(
        self,
        name: str,
        identity,
    ) -> Repository: ...

    def close(self) -> None: ...

    def __enter__(self) -> Self: ...

    def __exit__(self, exc_type, exc, traceback) -> bool: ...


@runtime_checkable
class SessionFactory(Protocol):
    def open_session(self) -> PersistenceSession: ...


@runtime_checkable
class PersistenceConnection(SessionFactory, Protocol):
    @property
    def healthy(self) -> bool: ...

    def close(self) -> None: ...
