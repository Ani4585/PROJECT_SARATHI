"""PROJECT SARATHI Cancellation Tokens and Timeout Utilities."""

from __future__ import annotations

import asyncio
from typing import Any, Awaitable, TypeVar

T = TypeVar("T")


class CancellationToken:
    """Cooperative cancellation token for async tasks."""

    def __init__(self) -> None:
        self._event = asyncio.Event()

    @property
    def is_cancellation_requested(self) -> bool:
        return self._event.is_set()

    def cancel(self) -> None:
        self._event.set()

    def throwIfCancellationRequested(self) -> None:
        if self.is_cancellation_requested:
            raise asyncio.CancelledError("Operation was cancelled via CancellationToken.")


async def with_timeout(coro_or_future: Awaitable[T], timeout_seconds: float) -> T:
    """Execute an async operation with a strict timeout in seconds."""
    try:
        return await asyncio.wait_for(coro_or_future, timeout=timeout_seconds)
    except asyncio.TimeoutError as err:
        raise TimeoutError(f"Operation timed out after {timeout_seconds} seconds.") from err
