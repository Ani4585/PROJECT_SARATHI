"""Reloadable configuration state and change notifications."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from threading import RLock

from .configuration import Configuration, ValueProvenance
from .loader import ConfigurationLoader


class ConfigurationChangeKind(StrEnum):
    ADDED = "added"
    UPDATED = "updated"
    REMOVED = "removed"


@dataclass(frozen=True, slots=True)
class ConfigurationChange:
    key: str
    kind: ConfigurationChangeKind
    previous_value: object | None
    current_value: object | None
    previous_provenance: ValueProvenance | None
    current_provenance: ValueProvenance | None


@dataclass(frozen=True, slots=True)
class ConfigurationChangeSet:
    previous: Configuration
    current: Configuration
    changes: tuple[ConfigurationChange, ...]

    @property
    def changed(self) -> bool:
        return bool(self.changes)


@dataclass(frozen=True, slots=True)
class NotificationFailure:
    listener: str
    message: str


@dataclass(frozen=True, slots=True)
class ConfigurationReloadReport:
    change_set: ConfigurationChangeSet
    notification_failures: tuple[NotificationFailure, ...] = ()

    @property
    def configuration(self) -> Configuration:
        return self.change_set.current

    @property
    def changed(self) -> bool:
        return self.change_set.changed

    @property
    def passed(self) -> bool:
        return not self.notification_failures


ConfigurationListener = Callable[[ConfigurationChangeSet], None]


def compare_configurations(
    previous: Configuration,
    current: Configuration,
) -> tuple[ConfigurationChange, ...]:
    """Return deterministic value or provenance changes."""

    changes: list[ConfigurationChange] = []
    keys = sorted(set(previous) | set(current))
    for key in keys:
        in_previous = key in previous
        in_current = key in current
        previous_value = previous[key] if in_previous else None
        current_value = current[key] if in_current else None
        previous_provenance = previous.provenance(key) if in_previous else None
        current_provenance = current.provenance(key) if in_current else None
        if not in_previous:
            kind = ConfigurationChangeKind.ADDED
        elif not in_current:
            kind = ConfigurationChangeKind.REMOVED
        elif previous_value != current_value or previous_provenance != current_provenance:
            kind = ConfigurationChangeKind.UPDATED
        else:
            continue
        changes.append(
            ConfigurationChange(
                key,
                kind,
                previous_value,
                current_value,
                previous_provenance,
                current_provenance,
            )
        )
    return tuple(changes)


class ConfigurationManager:
    """Own the current layered configuration and publish reload changes."""

    def __init__(self, loader: ConfigurationLoader) -> None:
        self._loader = loader
        self._current: Configuration | None = None
        self._listeners: list[ConfigurationListener] = []
        self._lock = RLock()

    @property
    def current(self) -> Configuration:
        with self._lock:
            if self._current is None:
                raise RuntimeError("Configuration has not been loaded.")
            return self._current

    def load(self) -> Configuration:
        """Load initial state without emitting a change notification."""

        with self._lock:
            configuration = self._loader.load()
            self._current = configuration
        return configuration

    def subscribe(self, listener: ConfigurationListener) -> Callable[[], None]:
        if not callable(listener):
            raise TypeError("Configuration listener must be callable.")
        with self._lock:
            self._listeners.append(listener)

        def unsubscribe() -> None:
            with self._lock:
                if listener in self._listeners:
                    self._listeners.remove(listener)

        return unsubscribe

    def reload(self) -> ConfigurationReloadReport:
        with self._lock:
            if self._current is None:
                raise RuntimeError("Configuration must be loaded before reload.")
            previous = self._current
            current = self._loader.load()
            change_set = ConfigurationChangeSet(
                previous,
                current,
                compare_configurations(previous, current),
            )
            self._current = current
            listeners = tuple(self._listeners)
        failures: list[NotificationFailure] = []
        if change_set.changed:
            for listener in listeners:
                try:
                    listener(change_set)
                except Exception as error:
                    name = getattr(listener, "__name__", type(listener).__name__)
                    failures.append(
                        NotificationFailure(
                            name,
                            f"{type(error).__name__}: {error}",
                        )
                    )
        return ConfigurationReloadReport(change_set, tuple(failures))


ReloadableConfiguration = ConfigurationManager
