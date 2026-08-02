"""Bounded thread-safe resource pool with leak detection."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from threading import Condition, RLock
from time import monotonic
from typing import Generic, TypeVar, cast

from .errors import (
    ResourceAcquisitionError,
    ResourceCleanupError,
    ResourceLeakError,
    ResourceUnavailableError,
)


T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class ResourcePoolSnapshot:
    created: int
    available: int
    in_use: int
    maximum: int
    open: bool


class ResourceLease(Generic[T]):
    __slots__ = ("_pool", "_token", "_value", "_released", "_discard")

    def __init__(self, pool: "ResourcePool[T]", token: int, value: T) -> None:
        self._pool = pool
        self._token = token
        self._value = value
        self._released = False
        self._discard = False

    @property
    def value(self) -> T:
        if self._released:
            raise ResourceUnavailableError("Resource lease has already been released.")
        return self._value

    def invalidate(self) -> None:
        if self._released:
            raise ResourceUnavailableError("Resource lease has already been released.")
        self._discard = True

    def release(self) -> None:
        if self._released:
            return
        self._released = True
        self._pool._return(self._token, discard=self._discard)

    def __enter__(self) -> T:
        return self.value

    def __exit__(self, exc_type, exc, traceback) -> bool:
        del exc_type, exc, traceback
        self.release()
        return False


class ResourcePool(Generic[T]):
    def __init__(
        self,
        factory: Callable[[], T],
        releaser: Callable[[T], None] | None = None,
        *,
        max_size: int = 10,
        min_size: int = 0,
    ) -> None:
        if not callable(factory):
            raise TypeError("Pool resource factory must be callable.")
        if releaser is not None and not callable(releaser):
            raise TypeError("Pool resource releaser must be callable.")
        if not isinstance(max_size, int) or isinstance(max_size, bool) or max_size <= 0:
            raise ValueError("Pool maximum size must be a positive integer.")
        if (
            not isinstance(min_size, int)
            or isinstance(min_size, bool)
            or min_size < 0
            or min_size > max_size
        ):
            raise ValueError("Pool minimum size must be between zero and maximum size.")
        self._factory = factory
        self._releaser = releaser
        self._max_size = max_size
        self._min_size = min_size
        self._available: list[T] = []
        self._in_use: dict[int, T] = {}
        self._created = 0
        self._next_token = 1
        self._open = False
        self._condition = Condition(RLock())

    def open(self) -> "ResourcePool[T]":
        with self._condition:
            if self._open:
                return self
            created: list[T] = []
            try:
                for _ in range(self._min_size):
                    created.append(self._factory())
            except Exception as error:
                cleanup_errors = self._release_many(reversed(created))
                message = f"Pool warm-up failed: {type(error).__name__}: {error}"
                if cleanup_errors:
                    message += "; cleanup: " + "; ".join(cleanup_errors)
                raise ResourceAcquisitionError(message) from error
            self._available.extend(created)
            self._created = len(created)
            self._open = True
            return self

    def acquire(self, timeout: float | None = None) -> ResourceLease[T]:
        if timeout is not None and timeout < 0:
            raise ValueError("Pool acquisition timeout must not be negative.")
        deadline = None if timeout is None else monotonic() + timeout
        with self._condition:
            if not self._open:
                raise ResourceUnavailableError("Resource pool is not open.")
            while True:
                if self._available:
                    value = self._available.pop()
                    break
                if self._created < self._max_size:
                    try:
                        value = self._factory()
                    except Exception as error:
                        raise ResourceAcquisitionError(
                            f"Pooled resource acquisition failed: {type(error).__name__}: {error}"
                        ) from error
                    self._created += 1
                    break
                remaining = None if deadline is None else deadline - monotonic()
                if remaining is not None and remaining <= 0:
                    raise ResourceAcquisitionError(
                        "Timed out waiting for a pooled resource."
                    )
                self._condition.wait(remaining)
                if not self._open:
                    raise ResourceUnavailableError("Resource pool closed while waiting.")
            token = self._next_token
            self._next_token += 1
            self._in_use[token] = value
            return ResourceLease(self, token, value)

    def close(self) -> None:
        with self._condition:
            if not self._open:
                return
            if self._in_use:
                raise ResourceLeakError(
                    f"Resource pool has {len(self._in_use)} unreleased lease(s).",
                    details={"in_use": len(self._in_use)},
                )
            self._open = False
            values = tuple(reversed(self._available))
            self._available.clear()
            self._created = 0
            self._condition.notify_all()
        failures = self._release_many(values)
        if failures:
            raise ResourceCleanupError(
                "Pooled resource cleanup failed: " + "; ".join(failures)
            )

    def snapshot(self) -> ResourcePoolSnapshot:
        with self._condition:
            return ResourcePoolSnapshot(
                self._created,
                len(self._available),
                len(self._in_use),
                self._max_size,
                self._open,
            )

    def _return(self, token: int, *, discard: bool) -> None:
        with self._condition:
            try:
                value = self._in_use.pop(token)
            except KeyError as error:
                raise ResourceUnavailableError("Resource lease is not active.") from error
            if discard or not self._open:
                self._created -= 1
                release = True
            else:
                self._available.append(value)
                release = False
            self._condition.notify()
        if release:
            failures = self._release_many((value,))
            if failures:
                raise ResourceCleanupError(failures[0])

    def _release_many(self, values) -> list[str]:
        failures: list[str] = []
        for value in values:
            try:
                if self._releaser is not None:
                    self._releaser(cast(T, value))
                else:
                    close = getattr(value, "close", None)
                    if callable(close):
                        close()
            except Exception as error:
                failures.append(f"{type(error).__name__}: {error}")
        return failures

    def __enter__(self) -> "ResourcePool[T]":
        return self.open()

    def __exit__(self, exc_type, exc, traceback) -> bool:
        del exc_type, exc, traceback
        self.close()
        return False
