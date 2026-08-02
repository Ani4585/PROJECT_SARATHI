"""Thread-safe independently managed lazy resource."""

from __future__ import annotations

from collections.abc import Callable
from threading import RLock
from typing import Generic, TypeVar, cast

from .errors import ResourceAcquisitionError, ResourceCleanupError, ResourceUnavailableError
from .model import ResourceState


T = TypeVar("T")


class LazyResource(Generic[T]):
    def __init__(
        self,
        factory: Callable[[], T],
        releaser: Callable[[T], None] | None = None,
    ) -> None:
        if not callable(factory):
            raise TypeError("Lazy resource factory must be callable.")
        if releaser is not None and not callable(releaser):
            raise TypeError("Lazy resource releaser must be callable.")
        self._factory = factory
        self._releaser = releaser
        self._value: T | None = None
        self._state = ResourceState.REGISTERED
        self._lock = RLock()

    @property
    def state(self) -> ResourceState:
        with self._lock:
            return self._state

    @property
    def initialized(self) -> bool:
        return self.state is ResourceState.READY

    def get(self) -> T:
        with self._lock:
            if self._state is ResourceState.READY:
                return cast(T, self._value)
            if self._state is ResourceState.ACQUIRING:
                raise ResourceAcquisitionError("Re-entrant lazy resource acquisition detected.")
            if self._state is not ResourceState.REGISTERED:
                raise ResourceUnavailableError(
                    f"Lazy resource is unavailable in state {self._state.value}."
                )
            self._state = ResourceState.ACQUIRING
            try:
                self._value = self._factory()
            except Exception as error:
                self._state = ResourceState.FAILED
                raise ResourceAcquisitionError(
                    f"Lazy resource acquisition failed: {type(error).__name__}: {error}"
                ) from error
            self._state = ResourceState.READY
            return self._value

    def close(self) -> None:
        with self._lock:
            if self._state in (ResourceState.REGISTERED, ResourceState.RELEASED):
                self._state = ResourceState.RELEASED
                return
            if self._state is not ResourceState.READY:
                raise ResourceUnavailableError(
                    f"Lazy resource cannot close from state {self._state.value}."
                )
            self._state = ResourceState.RELEASING
            value = cast(T, self._value)
            try:
                if self._releaser is not None:
                    self._releaser(value)
                else:
                    close = getattr(value, "close", None)
                    if callable(close):
                        close()
            except Exception as error:
                self._state = ResourceState.FAILED
                raise ResourceCleanupError(
                    f"Lazy resource cleanup failed: {type(error).__name__}: {error}"
                ) from error
            finally:
                self._value = None
            self._state = ResourceState.RELEASED

    def __enter__(self) -> T:
        return self.get()

    def __exit__(self, exc_type, exc, traceback) -> bool:
        del exc_type, exc, traceback
        self.close()
        return False
