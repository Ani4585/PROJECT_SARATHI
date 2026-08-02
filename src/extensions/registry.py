"""Deterministic typed extension registry."""

from __future__ import annotations

from typing import Any, cast

from .errors import ExtensionConflictError, ExtensionTypeError, UnknownExtensionPointError
from .model import (
    ExtensionDiagnostics,
    ExtensionPoint,
    ExtensionPointDiagnostic,
    ExtensionPolicy,
    ExtensionRegistration,
    ExtensionValue,
)


class ExtensionRegistry:
    """Define extension points and resolve their typed registrations."""

    def __init__(self) -> None:
        self._points: dict[str, ExtensionPoint[Any]] = {}
        self._registrations: dict[str, dict[str, ExtensionRegistration[Any]]] = {}

    def define(self, point: ExtensionPoint[ExtensionValue]) -> None:
        existing = self._points.get(point.name)
        if existing is not None:
            if existing == point:
                raise ExtensionConflictError(f"Extension point already defined: {point.name}")
            raise ExtensionConflictError(f"Conflicting extension-point definition: {point.name}")
        self._points[point.name] = point
        self._registrations[point.name] = {}

    def point(self, name: str) -> ExtensionPoint[Any]:
        try:
            return self._points[name]
        except KeyError as error:
            raise UnknownExtensionPointError(f"Unknown extension point: {name}") from error

    def points(self) -> tuple[ExtensionPoint[Any], ...]:
        return tuple(self._points[name] for name in sorted(self._points))

    def register(
        self,
        point_name: str,
        value: ExtensionValue,
        *,
        owner: str,
        priority: int = 0,
    ) -> ExtensionRegistration[ExtensionValue]:
        point = self.point(point_name)
        if not isinstance(value, point.contract):
            expected = f"{point.contract.__module__}.{point.contract.__qualname__}"
            raise ExtensionTypeError(
                f"Extension for {point_name} must implement {expected}."
            )
        registration = ExtensionRegistration(point_name, owner, value, priority)
        registrations = self._registrations[point_name]
        if registration.owner in registrations:
            raise ExtensionConflictError(
                f"Owner {registration.owner!r} already registered at {point_name}."
            )
        if point.policy is ExtensionPolicy.SINGLE and registrations:
            current_owner = next(iter(registrations))
            raise ExtensionConflictError(
                f"Single extension point {point_name} is already owned by {current_owner!r}."
            )
        registrations[registration.owner] = registration
        return registration

    def registrations(self, point_name: str) -> tuple[ExtensionRegistration[Any], ...]:
        self.point(point_name)
        return tuple(
            sorted(
                self._registrations[point_name].values(),
                key=lambda item: (-item.priority, item.owner),
            )
        )

    def unregister(self, point_name: str, owner: str) -> bool:
        """Remove one owner registration without removing the extension point."""

        self.point(point_name)
        registrations = self._registrations[point_name]
        if owner not in registrations:
            return False
        del registrations[owner]
        return True

    def resolve(self, point_name: str) -> object | tuple[object, ...] | None:
        point = self.point(point_name)
        registrations = self.registrations(point_name)
        if point.policy is ExtensionPolicy.COMPOSE:
            return tuple(item.value for item in registrations)
        if not registrations:
            return None
        return registrations[0].value

    def resolve_typed(self, point: ExtensionPoint[ExtensionValue]) -> ExtensionValue | tuple[ExtensionValue, ...] | None:
        defined = self.point(point.name)
        if defined.contract is not point.contract or defined.policy is not point.policy:
            raise ExtensionConflictError(f"Extension point definition does not match: {point.name}")
        return cast(ExtensionValue | tuple[ExtensionValue, ...] | None, self.resolve(point.name))

    def diagnostics(self) -> ExtensionDiagnostics:
        details: list[ExtensionPointDiagnostic] = []
        for point in self.points():
            registrations = self.registrations(point.name)
            owners = tuple(item.owner for item in registrations)
            if point.policy is ExtensionPolicy.COMPOSE:
                active = owners
                shadowed: tuple[str, ...] = ()
            elif owners:
                active = owners[:1]
                shadowed = owners[1:]
            else:
                active = ()
                shadowed = ()
            contract = f"{point.contract.__module__}.{point.contract.__qualname__}"
            details.append(
                ExtensionPointDiagnostic(
                    name=point.name,
                    contract=contract,
                    policy=point.policy,
                    registrations=len(registrations),
                    active_owners=active,
                    shadowed_owners=shadowed,
                )
            )
        return ExtensionDiagnostics(tuple(details))
