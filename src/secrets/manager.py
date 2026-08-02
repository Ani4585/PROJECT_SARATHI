"""Layered secret resolution, rotation, and change notifications."""

from __future__ import annotations

from collections.abc import Callable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from threading import RLock
from types import MappingProxyType

from src.configuration.keys import normalize_key

from .errors import MissingSecretError, SecretProviderError
from .providers import SecretProvider
from .value import SecretValue


@dataclass(frozen=True, slots=True)
class SecretProvenance:
    provider: str
    priority: int


class SecretChangeKind(StrEnum):
    ADDED = "added"
    ROTATED = "rotated"
    REMOVED = "removed"


@dataclass(frozen=True, slots=True)
class SecretChange:
    key: str
    kind: SecretChangeKind
    previous_provenance: SecretProvenance | None
    current_provenance: SecretProvenance | None


@dataclass(frozen=True, slots=True)
class SecretChangeSet:
    changes: tuple[SecretChange, ...]

    @property
    def changed(self) -> bool:
        return bool(self.changes)


@dataclass(frozen=True, slots=True)
class SecretNotificationFailure:
    listener: str
    message: str


@dataclass(frozen=True, slots=True)
class SecretReloadReport:
    snapshot: "SecretSnapshot"
    change_set: SecretChangeSet
    notification_failures: tuple[SecretNotificationFailure, ...] = ()

    @property
    def changed(self) -> bool:
        return self.change_set.changed

    @property
    def passed(self) -> bool:
        return not self.notification_failures


class SecretSnapshot(Mapping[str, SecretValue]):
    """Immutable view of the active secret set."""

    __slots__ = ("_values", "_provenance")
    __sarathi_secret__ = True

    def __init__(
        self,
        values: Mapping[str, SecretValue],
        provenance: Mapping[str, SecretProvenance],
    ) -> None:
        self._values = MappingProxyType(dict(values))
        self._provenance = MappingProxyType(dict(provenance))

    def __getitem__(self, key: str) -> SecretValue:
        return self._values[normalize_key(key)]

    def __iter__(self) -> Iterator[str]:
        return iter(self._values)

    def __len__(self) -> int:
        return len(self._values)

    def require(self, key: str) -> SecretValue:
        normalized = normalize_key(key)
        try:
            return self._values[normalized]
        except KeyError as error:
            raise MissingSecretError(normalized) from error

    def provenance(self, key: str) -> SecretProvenance:
        normalized = normalize_key(key)
        if normalized not in self._values:
            raise MissingSecretError(normalized)
        return self._provenance[normalized]

    def safe_summary(self) -> dict[str, object]:
        return {
            "count": len(self),
            "keys": tuple(sorted(self)),
            "providers": tuple(
                sorted({provenance.provider for provenance in self._provenance.values()})
            ),
        }


SecretListener = Callable[[SecretChangeSet], None]


class SecretManager:
    """Resolve layered providers atomically and invalidate rotated handles."""

    def __init__(self, providers: Sequence[SecretProvider]) -> None:
        if not providers:
            raise ValueError("At least one secret provider is required.")
        names: set[str] = set()
        normalized: list[tuple[int, SecretProvider]] = []
        for index, provider in enumerate(providers):
            name = provider.name.strip()
            if not name:
                raise ValueError("Secret provider names must not be blank.")
            if name in names:
                raise ValueError(f"Duplicate secret provider name: {name}")
            if not isinstance(provider.priority, int) or isinstance(provider.priority, bool):
                raise TypeError("Secret provider priority must be an integer.")
            names.add(name)
            normalized.append((index, provider))
        self._providers = tuple(
            provider
            for _, provider in sorted(
                normalized,
                key=lambda item: (item[1].priority, item[0]),
            )
        )
        self._current: SecretSnapshot | None = None
        self._listeners: list[SecretListener] = []
        self._lock = RLock()

    @property
    def current(self) -> SecretSnapshot:
        with self._lock:
            if self._current is None:
                raise RuntimeError("Secrets have not been loaded.")
            return self._current

    def subscribe(self, listener: SecretListener) -> Callable[[], None]:
        if not callable(listener):
            raise TypeError("Secret listener must be callable.")
        with self._lock:
            self._listeners.append(listener)

        def unsubscribe() -> None:
            with self._lock:
                if listener in self._listeners:
                    self._listeners.remove(listener)

        return unsubscribe

    def load(self) -> SecretSnapshot:
        with self._lock:
            if self._current is not None:
                raise RuntimeError("Secrets are already loaded; use reload().")
            raw, provenance = self._resolve()
            snapshot = SecretSnapshot(
                {key: SecretValue(value) for key, value in raw.items()},
                provenance,
            )
            self._current = snapshot
            return snapshot

    def reload(self) -> SecretReloadReport:
        with self._lock:
            if self._current is None:
                raise RuntimeError("Secrets must be loaded before reload.")
            previous = self._current
            raw, provenance = self._resolve()
            values: dict[str, SecretValue] = {}
            changes: list[SecretChange] = []
            invalidated: list[SecretValue] = []
            for key in sorted(set(previous) | set(raw)):
                old_exists = key in previous
                new_exists = key in raw
                old_provenance = previous.provenance(key) if old_exists else None
                new_provenance = provenance.get(key)
                if not old_exists:
                    values[key] = SecretValue(raw[key])
                    changes.append(
                        SecretChange(key, SecretChangeKind.ADDED, None, new_provenance)
                    )
                elif not new_exists:
                    invalidated.append(previous[key])
                    changes.append(
                        SecretChange(
                            key,
                            SecretChangeKind.REMOVED,
                            old_provenance,
                            None,
                        )
                    )
                elif previous[key].matches(raw[key]) and old_provenance == new_provenance:
                    values[key] = previous[key]
                else:
                    invalidated.append(previous[key])
                    values[key] = SecretValue(raw[key])
                    changes.append(
                        SecretChange(
                            key,
                            SecretChangeKind.ROTATED,
                            old_provenance,
                            new_provenance,
                        )
                    )
            current = SecretSnapshot(values, provenance)
            self._current = current
            for secret in invalidated:
                secret._invalidate()
            change_set = SecretChangeSet(tuple(changes))
            listeners = tuple(self._listeners)

        failures: list[SecretNotificationFailure] = []
        if change_set.changed:
            for listener in listeners:
                try:
                    listener(change_set)
                except Exception as error:
                    failures.append(
                        SecretNotificationFailure(
                            getattr(listener, "__name__", type(listener).__name__),
                            f"{type(error).__name__}: {error}",
                        )
                    )
        return SecretReloadReport(current, change_set, tuple(failures))

    def _resolve(self) -> tuple[dict[str, str], dict[str, SecretProvenance]]:
        values: dict[str, str] = {}
        provenance: dict[str, SecretProvenance] = {}
        for provider in self._providers:
            try:
                supplied = provider.load()
            except Exception as error:
                if isinstance(error, (FileNotFoundError, SecretProviderError)):
                    raise
                raise SecretProviderError(
                    f"Secret provider {provider.name!r} failed to load."
                ) from error
            if not isinstance(supplied, Mapping):
                raise SecretProviderError(
                    f"Secret provider {provider.name!r} must return a mapping."
                )
            for raw_key, raw_value in supplied.items():
                if not isinstance(raw_key, str) or not isinstance(raw_value, str):
                    raise SecretProviderError(
                        f"Secret provider {provider.name!r} returned an invalid entry."
                    )
                key = normalize_key(raw_key)
                values[key] = raw_value
                provenance[key] = SecretProvenance(provider.name, provider.priority)
        return values, provenance
