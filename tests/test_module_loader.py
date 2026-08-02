"""Tests for the official M23 module loader."""

from __future__ import annotations

import pytest

from src.modules import (
    BaseModule,
    ModuleDescriptor,
    ModuleLoader,
    ModuleRegistry,
    ModuleReloadError,
    ModuleReloadPolicy,
    ModuleRuntimeState,
)


class DescribedModule(BaseModule):
    def __init__(
        self,
        name: str,
        dependencies: tuple[str, ...] = (),
        *,
        reload_policy: ModuleReloadPolicy = ModuleReloadPolicy.NEVER,
        calls: list[str] | None = None,
    ) -> None:
        self.name = name
        self.version = "1.0.0"
        self.description = f"Module {name}"
        self.dependencies = dependencies
        self.reload_policy = reload_policy
        self.calls = calls if calls is not None else []

    def configure(self, container: object) -> None:
        self.calls.append(f"configure:{self.name}:{container}")

    def start(self, context: object) -> None:
        self.calls.append(f"start:{self.name}:{context}")

    def stop(self, context: object) -> None:
        self.calls.append(f"stop:{self.name}:{context}")


def test_descriptor_validates_and_normalizes_metadata() -> None:
    descriptor = ModuleDescriptor(
        " sample ",
        "1.2.3",
        " Sample module ",
        (" core ",),
        ModuleReloadPolicy.DEVELOPMENT,
    )
    assert descriptor.name == "sample"
    assert descriptor.description == "Sample module"
    assert descriptor.dependencies == ("core",)
    with pytest.raises(ValueError, match="semantic version"):
        ModuleDescriptor("bad", "latest", "Bad version")
    with pytest.raises(ValueError, match="cannot depend on itself"):
        ModuleDescriptor("self", "1.0.0", "Self cycle", ("self",))


def test_registry_exposes_validated_descriptor() -> None:
    registry = ModuleRegistry()
    module = DescribedModule("core", reload_policy=ModuleReloadPolicy.DEVELOPMENT)
    registry.register(module)
    assert registry.descriptor("core") == module.descriptor


def test_plan_is_deterministic_independent_of_registration_order() -> None:
    first = ModuleRegistry()
    second = ModuleRegistry()
    for name in ("zulu", "alpha", "middle"):
        first.register(DescribedModule(name))
    for name in ("middle", "zulu", "alpha"):
        second.register(DescribedModule(name))
    assert tuple(module.name for module in first.plan()) == ("alpha", "middle", "zulu")
    assert tuple(module.name for module in second.plan()) == ("alpha", "middle", "zulu")


def test_replace_revalidates_graph_and_rolls_back_on_failure() -> None:
    registry = ModuleRegistry()
    original = DescribedModule("core")
    registry.register(original)
    with pytest.raises(Exception):
        registry.replace("core", DescribedModule("core", ("missing",)))
    assert registry.get("core") is original
    assert registry.plan() == (original,)


def test_loader_coordinates_dependency_ordered_lifecycle() -> None:
    calls: list[str] = []
    loader = ModuleLoader()
    loader.add(DescribedModule("api", ("core",), calls=calls))
    loader.add(DescribedModule("core", calls=calls))
    assert loader.configure("container").names == ("core", "api")
    loader.start("context")
    assert loader.state is ModuleRuntimeState.RUNNING
    loader.stop("context")
    assert calls == [
        "configure:core:container",
        "configure:api:container",
        "start:core:context",
        "start:api:context",
        "stop:api:context",
        "stop:core:context",
    ]


def test_reload_requires_development_mode_and_module_policy() -> None:
    reloadable = DescribedModule("core", reload_policy=ModuleReloadPolicy.DEVELOPMENT)
    production = ModuleLoader()
    production.add(reloadable)
    with pytest.raises(ModuleReloadError, match="development mode is disabled"):
        production.reload("core", DescribedModule("core"))

    development = ModuleLoader(development=True)
    development.add(DescribedModule("fixed"))
    with pytest.raises(ModuleReloadError, match="policy is never"):
        development.reload("fixed", DescribedModule("fixed"))


def test_reload_is_rejected_while_runtime_is_active() -> None:
    loader = ModuleLoader(development=True)
    loader.add(DescribedModule("core", reload_policy=ModuleReloadPolicy.DEVELOPMENT))
    loader.configure("container")
    with pytest.raises(ModuleReloadError, match="runtime state is CONFIGURED"):
        loader.reload("core", DescribedModule("core"))


def test_stopped_development_module_can_reload_and_restart() -> None:
    original_calls: list[str] = []
    replacement_calls: list[str] = []
    loader = ModuleLoader(development=True)
    loader.add(
        DescribedModule(
            "core",
            reload_policy=ModuleReloadPolicy.DEVELOPMENT,
            calls=original_calls,
        )
    )
    loader.configure("first-container")
    loader.start("first-context")
    loader.stop("first-context")

    replacement = DescribedModule(
        "core",
        reload_policy=ModuleReloadPolicy.DEVELOPMENT,
        calls=replacement_calls,
    )
    assert loader.reload("core", replacement).names == ("core",)
    assert loader.state is ModuleRuntimeState.NEW
    loader.configure("second-container")
    loader.start("second-context")
    loader.stop("second-context")
    assert original_calls[-1] == "stop:core:first-context"
    assert replacement_calls == [
        "configure:core:second-container",
        "start:core:second-context",
        "stop:core:second-context",
    ]
