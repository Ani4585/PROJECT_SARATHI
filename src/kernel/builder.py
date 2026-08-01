"""Composition builder for the integrated platform kernel."""

from __future__ import annotations

from collections.abc import Callable

from src.application.messaging import MessageBus
from src.container import ServiceContainer, bootstrap_container
from src.domain.events import EventBus
from src.jobs import JobScheduler
from src.lifecycle import LifecycleManager
from src.metrics import MetricsRegistry
from src.modules import Module, ModuleRegistry, ModuleRuntime

from .kernel import PlatformKernel


class PlatformKernelBuilder:
    """Build a kernel and register all M13-M20 runtime services in DI."""

    def __init__(
        self,
        container_factory: Callable[[], ServiceContainer] = bootstrap_container,
    ) -> None:
        self._container_factory = container_factory
        self._modules: list[Module] = []

    def add_module(self, module: Module) -> PlatformKernelBuilder:
        self._modules.append(module)
        return self

    def build(self) -> PlatformKernel:
        container = self._container_factory()
        lifecycle = container.resolve("lifecycle")
        events = EventBus()
        messages = MessageBus()
        jobs = JobScheduler()
        metrics = MetricsRegistry()
        registry = ModuleRegistry()
        for module in self._modules:
            registry.register(module)
        modules = ModuleRuntime(registry)

        services = {
            "events": events,
            "messages": messages,
            "modules": modules,
            "jobs": jobs,
            "metrics": metrics,
        }
        for name, service in services.items():
            container.register_instance(name, service)
            container.register_type(type(service), service)

        modules.configure(container)
        kernel = PlatformKernel(
            container=container,
            lifecycle=lifecycle,
            events=events,
            messages=messages,
            modules=modules,
            jobs=jobs,
            metrics=metrics,
        )
        container.register_instance("kernel", kernel)
        container.register_type(PlatformKernel, kernel)
        return kernel
