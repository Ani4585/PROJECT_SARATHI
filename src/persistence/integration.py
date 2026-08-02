"""Dependency-injection and resource-management persistence wiring."""

from __future__ import annotations

from src.container import ServiceContainer
from src.container.lifetimes import ServiceLifetime
from src.resources import ResourceDefinition

from .configuration import PersistenceSettings
from .database import InMemoryDatabase
from .runtime import PersistenceRuntime, create_persistence_runtime


def register_persistence(
    container: ServiceContainer,
    configuration: PersistenceSettings | object | None = None,
) -> PersistenceRuntime:
    runtime = create_persistence_runtime(configuration)
    container.register_type(PersistenceSettings, runtime.settings)
    container.register_type(PersistenceRuntime, runtime)
    container.register_type(InMemoryDatabase, runtime.database)
    container.register_instance("persistence.runtime", runtime)
    container.register_factory(
        "persistence.unit_of_work",
        runtime.unit_of_work,
        ServiceLifetime.TRANSIENT,
    )
    return runtime


def persistence_resource(
    configuration: PersistenceSettings | object | None = None,
) -> ResourceDefinition:
    runtime = create_persistence_runtime(configuration)
    return ResourceDefinition(
        "persistence",
        runtime.open,
        releaser=lambda value: value.close(),
    )
