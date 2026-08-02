"""Structured diagnostic events with isolated in-process publication."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from threading import RLock


@dataclass(frozen=True, slots=True)
class DiagnosticEvent:
    name: str
    occurred_at: datetime
    attributes: tuple[tuple[str, str], ...] = ()
    correlation_id: str | None = None

    @classmethod
    def create(
        cls,
        name: str,
        attributes: Mapping[str, object] | None = None,
        correlation_id: str | None = None,
        clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    ) -> "DiagnosticEvent":
        normalized = name.strip()
        if not normalized:
            raise ValueError("Diagnostic event name must not be blank.")
        occurred_at = clock()
        if occurred_at.tzinfo is None:
            raise ValueError("Diagnostic event timestamps must be timezone-aware.")
        return cls(
            normalized,
            occurred_at,
            tuple(sorted((str(key).strip(), str(value)) for key, value in (attributes or {}).items())),
            correlation_id,
        )


@dataclass(frozen=True, slots=True)
class EventPublication:
    attempted: int
    delivered: int
    failures: tuple[str, ...] = ()

    @property
    def passed(self) -> bool:
        return not self.failures


class DiagnosticEventPublisher:
    """Publish events in subscription order while isolating handler failures."""

    def __init__(self) -> None:
        self._handlers: list[Callable[[DiagnosticEvent], None]] = []
        self._lock = RLock()

    def subscribe(self, handler: Callable[[DiagnosticEvent], None]) -> Callable[[], None]:
        with self._lock:
            self._handlers.append(handler)

        def unsubscribe() -> None:
            with self._lock:
                if handler in self._handlers:
                    self._handlers.remove(handler)

        return unsubscribe

    def publish(self, event: DiagnosticEvent) -> EventPublication:
        with self._lock:
            handlers = tuple(self._handlers)
        delivered = 0
        failures: list[str] = []
        for handler in handlers:
            try:
                handler(event)
                delivered += 1
            except Exception as error:
                failures.append(f"{type(error).__name__}: {error}")
        return EventPublication(len(handlers), delivered, tuple(failures))


class NoOpEventPublisher:
    """Discard diagnostic events safely."""

    def publish(self, event: DiagnosticEvent) -> EventPublication:
        del event
        return EventPublication(0, 0)
