"""Owned, conditional, reversible plugin registrations."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from src.container import ServiceContainer, ServiceLifetime
from src.extensions import ExtensionRegistry
from src.hooks import HookRegistry


class CommandRegistryPort(Protocol):
    def register(self, command: object) -> None: ...

    def unregister(self, name: str) -> object: ...


class RegistrationState(StrEnum):
    OPEN = "open"
    FROZEN = "frozen"
    CLOSED = "closed"


class RegistrationKind(StrEnum):
    SERVICE = "service"
    TYPED_SERVICE = "typed-service"
    COMMAND = "command"
    HOOK = "hook"
    EXTENSION = "extension"
    CLEANUP = "cleanup"


class DynamicRegistrationError(Exception):
    """Base dynamic-registration error."""


class LateRegistrationError(DynamicRegistrationError):
    """Raised when a frozen or closed scope is mutated."""


@dataclass(frozen=True, slots=True)
class RegistrationRecord:
    owner: str
    kind: RegistrationKind
    key: str


@dataclass(frozen=True, slots=True)
class UnloadFailure:
    record: RegistrationRecord
    message: str


@dataclass(frozen=True, slots=True)
class UnloadReport:
    owner: str
    removed: tuple[RegistrationRecord, ...]
    failures: tuple[UnloadFailure, ...]

    @property
    def passed(self) -> bool:
        return not self.failures


Condition = bool | Callable[[], bool]


class RegistrationScope:
    """Record all contributions owned by one plugin and undo them safely."""

    def __init__(
        self,
        owner: str,
        *,
        services: ServiceContainer,
        commands: CommandRegistryPort | None,
        hooks: HookRegistry,
        extensions: ExtensionRegistry,
    ) -> None:
        owner = owner.strip()
        if not owner:
            raise ValueError("Registration owner must not be blank.")
        self._owner = owner
        self._services = services
        self._commands = commands
        self._hooks = hooks
        self._extensions = extensions
        self._state = RegistrationState.OPEN
        self._entries: list[tuple[RegistrationRecord, Callable[[], None]]] = []

    @property
    def owner(self) -> str:
        return self._owner

    @property
    def state(self) -> RegistrationState:
        return self._state

    @property
    def records(self) -> tuple[RegistrationRecord, ...]:
        return tuple(record for record, cleanup in self._entries)

    def freeze(self) -> None:
        self._ensure_open()
        self._state = RegistrationState.FROZEN

    def register_service(
        self,
        name: str,
        instance: object,
        *,
        condition: Condition = True,
        on_unload: Callable[[object], None] | None = None,
    ) -> bool:
        self._ensure_open()
        if not self._selected(condition):
            return False
        self._services.register_instance(name, instance)

        def cleanup() -> None:
            failure: Exception | None = None
            try:
                if on_unload is not None:
                    on_unload(instance)
            except Exception as error:
                failure = error
            finally:
                self._services.unregister(name)
            if failure is not None:
                raise failure

        self._remember(RegistrationKind.SERVICE, name, cleanup)
        return True

    def register_factory(
        self,
        name: str,
        factory: Callable[[], object],
        *,
        lifetime: ServiceLifetime = ServiceLifetime.SINGLETON,
        condition: Condition = True,
        on_unload: Callable[[], None] | None = None,
    ) -> bool:
        self._ensure_open()
        if not self._selected(condition):
            return False
        self._services.register_factory(name, factory, lifetime)

        def cleanup() -> None:
            failure: Exception | None = None
            try:
                if on_unload is not None:
                    on_unload()
            except Exception as error:
                failure = error
            finally:
                self._services.unregister(name)
            if failure is not None:
                raise failure

        self._remember(RegistrationKind.SERVICE, name, cleanup)
        return True

    def register_typed_service(
        self,
        service_type: type,
        instance: object,
        *,
        condition: Condition = True,
    ) -> bool:
        self._ensure_open()
        if not self._selected(condition):
            return False
        self._services.register_type(service_type, instance)
        key = f"{service_type.__module__}.{service_type.__qualname__}"
        self._remember(
            RegistrationKind.TYPED_SERVICE,
            key,
            lambda: self._services.unregister_type(service_type),
        )
        return True

    def register_command(self, command: object, *, condition: Condition = True) -> bool:
        self._ensure_open()
        if not self._selected(condition):
            return False
        if self._commands is None:
            raise DynamicRegistrationError("No command registry is available.")
        name = getattr(command, "name", None)
        if not isinstance(name, str) or not name:
            raise TypeError("Plugin command must expose a non-empty name.")
        self._commands.register(command)
        self._remember(
            RegistrationKind.COMMAND,
            name,
            lambda: self._commands.unregister(name),
        )
        return True

    def register_hook(
        self,
        hook: str,
        handler: Callable,
        *,
        priority: int = 0,
        predicate: Callable | None = None,
        condition: Condition = True,
    ) -> bool:
        self._ensure_open()
        if not self._selected(condition):
            return False
        self._hooks.register(
            hook,
            handler,
            owner=self.owner,
            priority=priority,
            predicate=predicate,
        )
        self._remember(
            RegistrationKind.HOOK,
            hook,
            lambda: self._hooks.unregister(hook, self.owner),
        )
        return True

    def register_extension(
        self,
        point_name: str,
        value: object,
        *,
        priority: int = 0,
        condition: Condition = True,
    ) -> bool:
        self._ensure_open()
        if not self._selected(condition):
            return False
        self._extensions.register(point_name, value, owner=self.owner, priority=priority)
        self._remember(
            RegistrationKind.EXTENSION,
            point_name,
            lambda: self._extensions.unregister(point_name, self.owner),
        )
        return True

    def add_cleanup(
        self,
        key: str,
        callback: Callable[[], None],
        *,
        condition: Condition = True,
    ) -> bool:
        self._ensure_open()
        if not self._selected(condition):
            return False
        if not callable(callback):
            raise TypeError("Cleanup callback must be callable.")
        self._remember(RegistrationKind.CLEANUP, key, callback)
        return True

    def close(self) -> UnloadReport:
        if self._state is RegistrationState.CLOSED:
            return UnloadReport(self.owner, (), ())
        removed: list[RegistrationRecord] = []
        failures: list[UnloadFailure] = []
        for record, cleanup in reversed(self._entries):
            try:
                cleanup()
                removed.append(record)
            except Exception as error:
                failures.append(
                    UnloadFailure(record, f"{type(error).__name__}: {error}")
                )
        self._entries.clear()
        self._state = RegistrationState.CLOSED
        return UnloadReport(self.owner, tuple(removed), tuple(failures))

    def _ensure_open(self) -> None:
        if self._state is not RegistrationState.OPEN:
            raise LateRegistrationError(
                f"Registration scope for {self.owner!r} is {self._state.value}."
            )

    @staticmethod
    def _selected(condition: Condition) -> bool:
        result = condition() if callable(condition) else condition
        if not isinstance(result, bool):
            raise TypeError("Registration condition must produce a boolean.")
        return result

    def _remember(
        self,
        kind: RegistrationKind,
        key: str,
        cleanup: Callable[[], None],
    ) -> None:
        self._entries.append((RegistrationRecord(self.owner, kind, key), cleanup))


class DynamicRegistrationManager:
    """Create, inspect, freeze, and unload plugin-owned registration scopes."""

    def __init__(
        self,
        services: ServiceContainer,
        *,
        commands: CommandRegistryPort | None = None,
        hooks: HookRegistry | None = None,
        extensions: ExtensionRegistry | None = None,
    ) -> None:
        self.services = services
        self.commands = commands
        self.hooks = hooks or HookRegistry()
        self.extensions = extensions or ExtensionRegistry()
        self._scopes: dict[str, RegistrationScope] = {}
        self._order: list[str] = []

    def open_scope(self, owner: str) -> RegistrationScope:
        owner = owner.strip()
        if owner in self._scopes:
            raise DynamicRegistrationError(f"Registration scope already exists: {owner}")
        scope = RegistrationScope(
            owner,
            services=self.services,
            commands=self.commands,
            hooks=self.hooks,
            extensions=self.extensions,
        )
        self._scopes[owner] = scope
        self._order.append(owner)
        return scope

    def has_scope(self, owner: str) -> bool:
        return owner in self._scopes

    def scope(self, owner: str) -> RegistrationScope:
        try:
            return self._scopes[owner]
        except KeyError as error:
            raise KeyError(f"Registration scope not found: {owner}") from error

    def freeze(self, owner: str) -> None:
        self.scope(owner).freeze()

    def records(self, owner: str | None = None) -> tuple[RegistrationRecord, ...]:
        scopes = (self.scope(owner),) if owner is not None else tuple(
            self._scopes[name] for name in self._order
        )
        return tuple(record for scope in scopes for record in scope.records)

    def unload(self, owner: str) -> UnloadReport:
        scope = self.scope(owner)
        report = scope.close()
        del self._scopes[owner]
        self._order.remove(owner)
        return report

    def unload_all(self) -> tuple[UnloadReport, ...]:
        return tuple(self.unload(owner) for owner in tuple(reversed(self._order)))
