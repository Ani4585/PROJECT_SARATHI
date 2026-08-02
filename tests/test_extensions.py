"""Tests for the official M20 extension framework."""

from __future__ import annotations

from abc import ABC, abstractmethod

import pytest

from src.extensions import (
    ExtensionConflictError,
    ExtensionPoint,
    ExtensionPolicy,
    ExtensionRegistry,
    ExtensionTypeError,
    UnknownExtensionPointError,
    extension_diagnostics_to_dict,
    render_extension_diagnostics,
)


class Formatter(ABC):
    @abstractmethod
    def format(self, value: str) -> str:
        raise NotImplementedError


class UpperFormatter(Formatter):
    def format(self, value: str) -> str:
        return value.upper()


class PrefixFormatter(Formatter):
    def __init__(self, prefix: str) -> None:
        self.prefix = prefix

    def format(self, value: str) -> str:
        return f"{self.prefix}{value}"


def test_extension_point_validates_name_and_contract() -> None:
    with pytest.raises(ValueError, match="contain no whitespace"):
        ExtensionPoint("bad name", Formatter)
    with pytest.raises(TypeError, match="runtime-checkable"):
        ExtensionPoint("bad", object())  # type: ignore[arg-type]


def test_registry_defines_and_lists_points_deterministically() -> None:
    registry = ExtensionRegistry()
    registry.define(ExtensionPoint("zulu", Formatter))
    registry.define(ExtensionPoint("alpha", Formatter, ExtensionPolicy.SINGLE))
    assert tuple(point.name for point in registry.points()) == ("alpha", "zulu")
    with pytest.raises(ExtensionConflictError, match="already defined"):
        registry.define(ExtensionPoint("alpha", Formatter, ExtensionPolicy.SINGLE))


def test_unknown_extension_point_is_reported() -> None:
    with pytest.raises(UnknownExtensionPointError, match="Unknown extension point"):
        ExtensionRegistry().resolve("missing")


def test_registration_enforces_runtime_contract() -> None:
    registry = ExtensionRegistry()
    registry.define(ExtensionPoint("formatter", Formatter))
    with pytest.raises(ExtensionTypeError, match="must implement"):
        registry.register("formatter", object(), owner="broken")


def test_composition_orders_by_priority_then_owner() -> None:
    point = ExtensionPoint("formatter", Formatter, ExtensionPolicy.COMPOSE)
    registry = ExtensionRegistry()
    registry.define(point)
    low = PrefixFormatter("low:")
    beta = PrefixFormatter("beta:")
    alpha = UpperFormatter()
    registry.register(point.name, low, owner="low", priority=1)
    registry.register(point.name, beta, owner="beta", priority=10)
    registry.register(point.name, alpha, owner="alpha", priority=10)
    assert registry.resolve_typed(point) == (alpha, beta, low)


def test_duplicate_owner_is_a_conflict() -> None:
    registry = ExtensionRegistry()
    registry.define(ExtensionPoint("formatter", Formatter))
    registry.register("formatter", UpperFormatter(), owner="plugin")
    with pytest.raises(ExtensionConflictError, match="already registered"):
        registry.register("formatter", UpperFormatter(), owner="plugin")


def test_single_policy_rejects_a_second_registration() -> None:
    registry = ExtensionRegistry()
    registry.define(ExtensionPoint("formatter", Formatter, ExtensionPolicy.SINGLE))
    selected = UpperFormatter()
    registry.register("formatter", selected, owner="first")
    with pytest.raises(ExtensionConflictError, match="already owned"):
        registry.register("formatter", PrefixFormatter("x"), owner="second")
    assert registry.resolve("formatter") is selected


def test_replace_policy_selects_highest_priority_deterministically() -> None:
    point = ExtensionPoint("formatter", Formatter, ExtensionPolicy.REPLACE)
    registry = ExtensionRegistry()
    registry.define(point)
    beta = PrefixFormatter("beta:")
    alpha = UpperFormatter()
    low = PrefixFormatter("low:")
    registry.register(point.name, low, owner="low", priority=1)
    registry.register(point.name, beta, owner="beta", priority=10)
    registry.register(point.name, alpha, owner="alpha", priority=10)
    assert registry.resolve_typed(point) is alpha


def test_empty_resolution_matches_policy() -> None:
    registry = ExtensionRegistry()
    registry.define(ExtensionPoint("many", Formatter, ExtensionPolicy.COMPOSE))
    registry.define(ExtensionPoint("one", Formatter, ExtensionPolicy.SINGLE))
    assert registry.resolve("many") == ()
    assert registry.resolve("one") is None


def test_typed_resolution_rejects_mismatched_point_definition() -> None:
    registry = ExtensionRegistry()
    registry.define(ExtensionPoint("formatter", Formatter, ExtensionPolicy.COMPOSE))
    with pytest.raises(ExtensionConflictError, match="does not match"):
        registry.resolve_typed(ExtensionPoint("formatter", Formatter, ExtensionPolicy.REPLACE))


def test_diagnostics_expose_active_and_shadowed_registrations() -> None:
    registry = ExtensionRegistry()
    registry.define(ExtensionPoint("formatter", Formatter, ExtensionPolicy.REPLACE))
    registry.register("formatter", PrefixFormatter("low:"), owner="low", priority=1)
    registry.register("formatter", UpperFormatter(), owner="active", priority=10)
    report = registry.diagnostics()
    assert report.total_points == 1
    assert report.total_registrations == 2
    assert report.shadowed_registrations == 1
    assert report.points[0].active_owners == ("active",)
    assert report.points[0].shadowed_owners == ("low",)
    assert extension_diagnostics_to_dict(report)["points"][0]["policy"] == "replace"
    rendered = render_extension_diagnostics(report)
    assert "[REPLACE] formatter" in rendered
    assert "Shadowed: low" in rendered
