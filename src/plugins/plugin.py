"""Framework plugin lifecycle contract."""

from __future__ import annotations

from abc import ABC

from .model import PluginContext, PluginManifest
from .registration import RegistrationScope


class Plugin(ABC):
    @property
    def manifest(self) -> PluginManifest:
        raise NotImplementedError

    def configure(self, context: PluginContext) -> None:
        del context

    def register(self, registrations: RegistrationScope) -> None:
        """Contribute owned services, commands, hooks, or extensions."""

        del registrations

    def start(self, context: PluginContext) -> None:
        del context

    def stop(self, context: PluginContext) -> None:
        del context
