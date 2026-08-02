"""Dependency-aware context-managed resource registry."""

from __future__ import annotations

from collections.abc import Callable
from threading import RLock

from .errors import (
    ResourceAcquisitionError,
    ResourceCleanupError,
    ResourceRegistrationError,
    ResourceUnavailableError,
)
from .model import (
    ResourceCleanupFailure,
    ResourceCloseReport,
    ResourceDefinition,
    ResourceRegistrySnapshot,
    ResourceRegistryState,
    ResourceState,
)


class ResourceRegistry:
    """Acquire resources in dependency order and release them in reverse order."""

    def __init__(self) -> None:
        self._definitions: dict[str, ResourceDefinition] = {}
        self._states: dict[str, ResourceState] = {}
        self._values: dict[str, object] = {}
        self._cleanup: dict[str, Callable[[], None]] = {}
        self._acquisition_order: list[str] = []
        self._state = ResourceRegistryState.NEW
        self._last_close_report: ResourceCloseReport | None = None
        self._lock = RLock()

    @property
    def state(self) -> ResourceRegistryState:
        with self._lock:
            return self._state

    @property
    def last_close_report(self) -> ResourceCloseReport | None:
        with self._lock:
            return self._last_close_report

    def register(self, definition: ResourceDefinition) -> None:
        with self._lock:
            if self._state is not ResourceRegistryState.NEW:
                raise ResourceRegistrationError(
                    "Resources cannot be registered after the registry starts opening."
                )
            if definition.name in self._definitions:
                raise ResourceRegistrationError(
                    f"Resource is already registered: {definition.name}"
                )
            self._definitions[definition.name] = definition
            self._states[definition.name] = ResourceState.REGISTERED

    def add(
        self,
        name: str,
        factory: Callable[[], object],
        *,
        releaser: Callable[[object], None] | None = None,
        dependencies: tuple[str, ...] = (),
        lazy: bool = False,
    ) -> None:
        self.register(ResourceDefinition(name, factory, releaser, dependencies, lazy))

    def plan(self) -> tuple[str, ...]:
        with self._lock:
            definitions = dict(self._definitions)
        ordered: list[str] = []
        visiting: list[str] = []
        visited: set[str] = set()

        def visit(name: str) -> None:
            if name in visiting:
                cycle = " -> ".join((*visiting[visiting.index(name) :], name))
                raise ResourceRegistrationError(
                    f"Resource dependency cycle detected: {cycle}"
                )
            if name in visited:
                return
            definition = definitions[name]
            missing = tuple(
                dependency
                for dependency in definition.dependencies
                if dependency not in definitions
            )
            if missing:
                raise ResourceRegistrationError(
                    f"Resource {name!r} has missing dependencies: {', '.join(missing)}"
                )
            visiting.append(name)
            for dependency in sorted(definition.dependencies):
                visit(dependency)
            visiting.pop()
            visited.add(name)
            ordered.append(name)

        for name in sorted(definitions):
            visit(name)
        return tuple(ordered)

    def open(self) -> "ResourceRegistry":
        with self._lock:
            if self._state is ResourceRegistryState.OPEN:
                return self
            if self._state is not ResourceRegistryState.NEW:
                raise ResourceUnavailableError(
                    f"Resource registry cannot open from state {self._state.value}."
                )
            plan = self.plan()
            self._state = ResourceRegistryState.OPENING
            try:
                for name in plan:
                    if not self._definitions[name].lazy:
                        self._acquire(name)
            except Exception as error:
                report = self._release_all()
                self._last_close_report = report
                self._state = ResourceRegistryState.FAILED
                details = {
                    "cleanup_failures": tuple(
                        failure.message for failure in report.failures
                    )
                }
                if isinstance(error, ResourceAcquisitionError):
                    raise ResourceAcquisitionError(str(error), details=details) from error
                raise ResourceAcquisitionError(
                    f"Resource registry failed while opening: {type(error).__name__}: {error}",
                    details=details,
                ) from error
            self._state = ResourceRegistryState.OPEN
            return self

    def get(self, name: str) -> object:
        normalized = name.strip()
        with self._lock:
            if normalized not in self._definitions:
                raise ResourceUnavailableError(f"Resource is not registered: {normalized}")
            if self._state not in (
                ResourceRegistryState.OPEN,
                ResourceRegistryState.OPENING,
            ):
                raise ResourceUnavailableError(
                    f"Resource registry is not open: {self._state.value}"
                )
            return self._acquire(normalized)

    def close(self) -> ResourceCloseReport:
        with self._lock:
            if self._state is ResourceRegistryState.CLOSED:
                return self._last_close_report or ResourceCloseReport(())
            if self._state is ResourceRegistryState.NEW:
                self._state = ResourceRegistryState.CLOSED
                self._last_close_report = ResourceCloseReport(())
                return self._last_close_report
            if self._state is ResourceRegistryState.CLOSING:
                raise ResourceUnavailableError("Resource registry is already closing.")
            self._state = ResourceRegistryState.CLOSING
            report = self._release_all()
            self._state = ResourceRegistryState.CLOSED
            self._last_close_report = report
            return report

    def snapshot(self) -> ResourceRegistrySnapshot:
        with self._lock:
            resources = tuple(
                (
                    name,
                    self._states[name],
                    self._definitions[name].lazy,
                )
                for name in sorted(self._definitions)
            )
            return ResourceRegistrySnapshot(
                self._state,
                resources,
                tuple(self._acquisition_order),
            )

    def _acquire(self, name: str) -> object:
        state = self._states[name]
        if state is ResourceState.READY:
            return self._values[name]
        if state is ResourceState.ACQUIRING:
            raise ResourceAcquisitionError(
                f"Re-entrant resource acquisition detected: {name}"
            )
        if state is not ResourceState.REGISTERED:
            raise ResourceUnavailableError(
                f"Resource {name!r} is unavailable in state {state.value}."
            )
        definition = self._definitions[name]
        self._states[name] = ResourceState.ACQUIRING
        try:
            for dependency in definition.dependencies:
                self._acquire(dependency)
            candidate = definition.factory()
            value, cleanup = self._prepare(candidate, definition.releaser)
        except Exception as error:
            self._states[name] = ResourceState.FAILED
            if isinstance(error, ResourceAcquisitionError):
                raise
            raise ResourceAcquisitionError(
                f"Resource {name!r} acquisition failed: {type(error).__name__}: {error}"
            ) from error
        self._values[name] = value
        if cleanup is not None:
            self._cleanup[name] = cleanup
        self._acquisition_order.append(name)
        self._states[name] = ResourceState.READY
        return value

    @staticmethod
    def _prepare(
        candidate: object,
        releaser: Callable[[object], None] | None,
    ) -> tuple[object, Callable[[], None] | None]:
        enter = getattr(candidate, "__enter__", None)
        exit_context = getattr(candidate, "__exit__", None)
        if callable(enter) and callable(exit_context):
            value = enter()
            return value, lambda: exit_context(None, None, None)
        if releaser is not None:
            return candidate, lambda: releaser(candidate)
        close = getattr(candidate, "close", None)
        if callable(close):
            return candidate, close
        return candidate, None

    def _release_all(self) -> ResourceCloseReport:
        released: list[str] = []
        failures: list[ResourceCleanupFailure] = []
        for name in reversed(self._acquisition_order):
            self._states[name] = ResourceState.RELEASING
            cleanup = self._cleanup.get(name)
            try:
                if cleanup is not None:
                    cleanup()
            except Exception as error:
                self._states[name] = ResourceState.FAILED
                failures.append(
                    ResourceCleanupFailure(
                        name,
                        f"{type(error).__name__}: {error}",
                    )
                )
            else:
                self._states[name] = ResourceState.RELEASED
                released.append(name)
            self._values.pop(name, None)
            self._cleanup.pop(name, None)
        self._acquisition_order.clear()
        return ResourceCloseReport(tuple(released), tuple(failures))

    def __enter__(self) -> "ResourceRegistry":
        return self.open()

    def __exit__(self, exc_type, exc, traceback) -> bool:
        del exc, traceback
        report = self.close()
        if report.failures and exc_type is None:
            failures = "; ".join(
                f"{failure.resource}: {failure.message}" for failure in report.failures
            )
            raise ResourceCleanupError(f"Resource cleanup failed: {failures}")
        return False
