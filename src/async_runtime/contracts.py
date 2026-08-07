"""PROJECT SARATHI Async Service Contracts & Lifecycle Protocols."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class IAsyncInitializer(Protocol):
    """Protocol for services requiring asynchronous initialization."""

    async def initialize(self) -> None: ...


@runtime_checkable
class IAsyncDisposable(Protocol):
    """Protocol for services requiring asynchronous cleanup/disposal."""

    async def dispose(self) -> None: ...
