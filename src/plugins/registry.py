"""Validated plugin registry with enable policy and isolated lifecycle."""

from __future__ import annotations

from collections.abc import Mapping

from .model import (
    PluginContext,
    PluginManifest,
    PluginOperation,
    PluginReport,
    PluginState,
    version_tuple,
)
from .plugin import Plugin
from .registration import DynamicRegistrationManager


class PluginRegistry:
    def __init__(self) -> None:
        self._plugins: dict[str, Plugin] = {}
        self._states: dict[str, PluginState] = {}
        self._registration_manager: DynamicRegistrationManager | None = None

    def register(self, plugin: Plugin) -> None:
        if not isinstance(plugin, Plugin):
            raise TypeError("Registered plugins must implement Plugin.")
        manifest = plugin.manifest
        if not isinstance(manifest, PluginManifest):
            raise TypeError("Plugin manifest must be a PluginManifest.")
        if manifest.name in self._plugins:
            raise ValueError(f"Plugin already registered: {manifest.name}")
        self._plugins[manifest.name] = plugin
        self._states[manifest.name] = PluginState.REGISTERED

    def manifests(self) -> tuple[PluginManifest, ...]:
        return tuple(self._plugins[name].manifest for name in sorted(self._plugins))

    def state(self, name: str) -> PluginState:
        return self._states[name]

    def validate(self, framework_version: str, capabilities: frozenset[str] = frozenset()) -> tuple[str, ...]:
        return self._validate_plugins(
            framework_version,
            capabilities,
            tuple(sorted(self._plugins)),
        )

    def _validate_plugins(
        self,
        framework_version: str,
        capabilities: frozenset[str],
        names: tuple[str, ...],
    ) -> tuple[str, ...]:
        current = version_tuple(framework_version)
        available = set(capabilities)
        manifests = tuple(self._plugins[name].manifest for name in names)
        for manifest in manifests:
            available.update(manifest.provided_capabilities)
        errors: list[str] = []
        for manifest in manifests:
            if current < version_tuple(manifest.minimum_framework_version):
                errors.append(f"{manifest.name}: requires framework >= {manifest.minimum_framework_version}")
            if manifest.maximum_framework_version and current > version_tuple(manifest.maximum_framework_version):
                errors.append(f"{manifest.name}: requires framework <= {manifest.maximum_framework_version}")
            missing = sorted(manifest.required_capabilities - available)
            if missing:
                errors.append(f"{manifest.name}: missing capabilities {', '.join(missing)}")
        return tuple(errors)

    def start_all(
        self,
        context: PluginContext,
        enabled: Mapping[str, bool] | None = None,
        registration_manager: DynamicRegistrationManager | None = None,
    ) -> PluginReport:
        if registration_manager is not None:
            self._registration_manager = registration_manager
        policy = dict(enabled or {})
        active_names = tuple(
            name
            for name in sorted(self._plugins)
            if policy.get(name, self._plugins[name].manifest.enabled_by_default)
        )
        validation = self._validate_plugins(
            context.framework_version,
            context.capabilities,
            active_names,
        )
        invalid = {message.split(":", 1)[0]: message for message in validation}
        available = set(context.capabilities)
        for name in active_names:
            available.update(self._plugins[name].manifest.provided_capabilities)
        plugin_context = PluginContext(
            framework_version=context.framework_version,
            configuration=context.configuration,
            capabilities=frozenset(available),
        )
        operations: list[PluginOperation] = []
        for name in sorted(self._plugins):
            plugin = self._plugins[name]
            active = policy.get(name, plugin.manifest.enabled_by_default)
            if not active:
                self._states[name] = PluginState.DISABLED
                operations.append(PluginOperation(name, PluginState.DISABLED, "Plugin is disabled."))
                continue
            if name in invalid:
                self._states[name] = PluginState.FAILED
                operations.append(PluginOperation(name, PluginState.FAILED, invalid[name]))
                continue
            try:
                if registration_manager is not None:
                    scope = registration_manager.open_scope(name)
                    plugin.register(scope)
                    scope.freeze()
                plugin.configure(plugin_context)
                plugin.start(plugin_context)
                self._states[name] = PluginState.STARTED
                operations.append(PluginOperation(name, PluginState.STARTED, "Plugin started."))
            except Exception as error:
                cleanup_message = ""
                if registration_manager is not None and registration_manager.has_scope(name):
                    cleanup = registration_manager.unload(name)
                    if cleanup.failures:
                        cleanup_message = f"; cleanup failures: {len(cleanup.failures)}"
                self._states[name] = PluginState.FAILED
                operations.append(
                    PluginOperation(
                        name,
                        PluginState.FAILED,
                        f"{type(error).__name__}: {error}{cleanup_message}",
                    )
                )
        return PluginReport(tuple(operations))

    def stop_all(
        self,
        context: PluginContext,
        registration_manager: DynamicRegistrationManager | None = None,
    ) -> PluginReport:
        manager = registration_manager or self._registration_manager
        operations: list[PluginOperation] = []
        for name in sorted(self._plugins, reverse=True):
            if self._states[name] is not PluginState.STARTED:
                continue
            failure: str | None = None
            try:
                self._plugins[name].stop(context)
            except Exception as error:
                failure = f"{type(error).__name__}: {error}"
            if manager is not None and manager.has_scope(name):
                cleanup = manager.unload(name)
                if cleanup.failures:
                    cleanup_message = f"cleanup failures: {len(cleanup.failures)}"
                    failure = f"{failure}; {cleanup_message}" if failure else cleanup_message
            if failure is None:
                self._states[name] = PluginState.STOPPED
                operations.append(PluginOperation(name, PluginState.STOPPED, "Plugin stopped and unloaded."))
            else:
                self._states[name] = PluginState.FAILED
                operations.append(PluginOperation(name, PluginState.FAILED, failure))
        return PluginReport(tuple(operations))
