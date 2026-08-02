"""Installed and local-development plugin package discovery."""

from __future__ import annotations

import json
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from importlib import metadata, util
from pathlib import Path
from types import ModuleType
from typing import Any, Protocol

from src.core.version import VERSION

from .model import PluginManifest, version_tuple
from .plugin import Plugin


PLUGIN_ENTRY_POINT_GROUP = "project_sarathi.plugins"
LOCAL_MANIFEST_NAME = "sarathi-plugin.json"


class PluginEntryPoint(Protocol):
    name: str
    value: str

    def load(self) -> object: ...


class DiscoveryStatus(StrEnum):
    DISCOVERED = "discovered"
    INCOMPATIBLE = "incompatible"
    BROKEN = "broken"


@dataclass(frozen=True, slots=True)
class DiscoveredPlugin:
    source: str
    status: DiscoveryStatus
    manifest: PluginManifest | None = None
    plugin: Plugin | None = None
    message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        manifest = self.manifest
        return {
            "source": self.source,
            "status": self.status.value,
            "name": manifest.name if manifest else None,
            "version": manifest.version if manifest else None,
            "message": self.message,
        }


@dataclass(frozen=True, slots=True)
class PluginDiscoveryReport:
    results: tuple[DiscoveredPlugin, ...]
    cached: bool = False

    @property
    def discovered(self) -> int:
        return sum(item.status is DiscoveryStatus.DISCOVERED for item in self.results)

    @property
    def incompatible(self) -> int:
        return sum(item.status is DiscoveryStatus.INCOMPATIBLE for item in self.results)

    @property
    def broken(self) -> int:
        return sum(item.status is DiscoveryStatus.BROKEN for item in self.results)

    @property
    def passed(self) -> bool:
        return self.broken == 0 and self.incompatible == 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "group": PLUGIN_ENTRY_POINT_GROUP,
            "cached": self.cached,
            "summary": {
                "discovered": self.discovered,
                "incompatible": self.incompatible,
                "broken": self.broken,
                "passed": self.passed,
            },
            "plugins": [item.to_dict() for item in self.results],
        }


def _default_entry_points() -> Iterable[PluginEntryPoint]:
    entries = metadata.entry_points()
    if hasattr(entries, "select"):
        return entries.select(group=PLUGIN_ENTRY_POINT_GROUP)
    return tuple(item for item in entries if item.group == PLUGIN_ENTRY_POINT_GROUP)


def manifest_from_mapping(document: Mapping[str, object]) -> PluginManifest:
    """Parse and validate a plugin manifest document."""

    required = ("name", "version", "description")
    missing = [key for key in required if key not in document]
    if missing:
        raise ValueError(f"Plugin manifest is missing: {', '.join(missing)}")
    invalid = [key for key in required if not isinstance(document[key], str)]
    if invalid:
        raise TypeError(f"Plugin manifest fields must be strings: {', '.join(invalid)}")

    def strings(key: str) -> frozenset[str]:
        value = document.get(key, ())
        if isinstance(value, str) or not isinstance(value, (list, tuple, set, frozenset)):
            raise TypeError(f"Plugin manifest field {key!r} must be a sequence of strings.")
        if not all(isinstance(item, str) for item in value):
            raise TypeError(f"Plugin manifest field {key!r} must contain only strings.")
        return frozenset(value)

    maximum = document.get("maximum_framework_version")
    if maximum is not None and not isinstance(maximum, str):
        raise TypeError("maximum_framework_version must be a string or null.")
    enabled = document.get("enabled_by_default", True)
    if not isinstance(enabled, bool):
        raise TypeError("enabled_by_default must be a boolean.")
    return PluginManifest(
        name=document["name"],
        version=document["version"],
        description=document["description"],
        minimum_framework_version=str(document.get("minimum_framework_version", "0.0.0")),
        maximum_framework_version=maximum,
        required_capabilities=strings("required_capabilities"),
        provided_capabilities=strings("provided_capabilities"),
        enabled_by_default=enabled,
    )


def compatibility_errors(
    manifest: PluginManifest,
    framework_version: str,
    capabilities: frozenset[str],
) -> tuple[str, ...]:
    current = version_tuple(framework_version)
    errors: list[str] = []
    if current < version_tuple(manifest.minimum_framework_version):
        errors.append(f"requires framework >= {manifest.minimum_framework_version}")
    if manifest.maximum_framework_version and current > version_tuple(manifest.maximum_framework_version):
        errors.append(f"requires framework <= {manifest.maximum_framework_version}")
    missing = sorted(manifest.required_capabilities - capabilities)
    if missing:
        errors.append(f"missing capabilities {', '.join(missing)}")
    return tuple(errors)


def _resolve_plugin(candidate: object) -> Plugin:
    if isinstance(candidate, Plugin):
        return candidate
    if isinstance(candidate, type) and issubclass(candidate, Plugin):
        return candidate()
    if callable(candidate):
        resolved = candidate()
        if isinstance(resolved, Plugin):
            return resolved
    raise TypeError("Plugin target must expose a Plugin instance, class, or zero-argument factory.")


def _load_module(path: Path, identity: str) -> ModuleType:
    spec = util.spec_from_file_location(identity, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load local plugin module: {path}")
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_local_plugin(directory: Path, document: Mapping[str, object]) -> Plugin:
    entry = document.get("entry")
    if not isinstance(entry, str) or ":" not in entry:
        raise ValueError("Local plugin manifest entry must use 'relative-file.py:attribute'.")
    relative_file, attribute = (part.strip() for part in entry.split(":", 1))
    if not relative_file or not attribute:
        raise ValueError("Local plugin manifest entry must include a file and attribute.")
    module_path = (directory / relative_file).resolve()
    try:
        module_path.relative_to(directory.resolve())
    except ValueError as error:
        raise ValueError("Local plugin entry must remain inside its plugin directory.") from error
    if not module_path.is_file():
        raise FileNotFoundError(f"Local plugin module not found: {module_path}")
    identity = f"_sarathi_local_plugin_{abs(hash(str(module_path)))}"
    module = _load_module(module_path, identity)
    try:
        target = getattr(module, attribute)
    except AttributeError as error:
        raise AttributeError(f"Local plugin target not found: {attribute}") from error
    return _resolve_plugin(target)


class PluginDiscovery:
    """Discover plugin packages with deterministic caching and diagnostics."""

    def __init__(
        self,
        *,
        framework_version: str = VERSION,
        capabilities: frozenset[str] = frozenset(),
        local_paths: Iterable[Path] = (),
        entry_points: Callable[[], Iterable[PluginEntryPoint]] = _default_entry_points,
    ) -> None:
        version_tuple(framework_version)
        self._framework_version = framework_version
        self._capabilities = frozenset(capabilities)
        self._local_paths = tuple(sorted((Path(path).resolve() for path in local_paths), key=str))
        self._entry_points = entry_points
        self._cache: PluginDiscoveryReport | None = None

    def invalidate(self) -> None:
        self._cache = None

    def discover(self, *, refresh: bool = False) -> PluginDiscoveryReport:
        if self._cache is not None and not refresh:
            return PluginDiscoveryReport(self._cache.results, cached=True)
        results: list[DiscoveredPlugin] = []
        names: set[str] = set()
        try:
            entries = tuple(sorted(self._entry_points(), key=lambda item: (item.name, item.value)))
        except Exception as error:
            entries = ()
            results.append(self._broken("entry-points", error))
        for entry in entries:
            source = f"entry-point:{entry.name}={entry.value}"
            try:
                plugin = _resolve_plugin(entry.load())
                results.append(self._evaluate(source, plugin, plugin.manifest, names))
            except Exception as error:
                results.append(self._broken(source, error))
        for directory in self._local_paths:
            source = f"local:{directory}"
            try:
                document = json.loads((directory / LOCAL_MANIFEST_NAME).read_text(encoding="utf-8"))
                if not isinstance(document, dict):
                    raise TypeError("Local plugin manifest must contain a JSON object.")
                declared = manifest_from_mapping(document)
                plugin = _load_local_plugin(directory, document)
                if plugin.manifest != declared:
                    raise ValueError("Loaded plugin manifest does not match its local manifest file.")
                results.append(self._evaluate(source, plugin, declared, names))
            except Exception as error:
                results.append(self._broken(source, error))
        self._cache = PluginDiscoveryReport(tuple(results))
        return self._cache

    def _evaluate(
        self,
        source: str,
        plugin: Plugin,
        manifest: PluginManifest,
        names: set[str],
    ) -> DiscoveredPlugin:
        if not isinstance(manifest, PluginManifest):
            raise TypeError("Discovered plugin manifest must be a PluginManifest.")
        if manifest.name in names:
            raise ValueError(f"Duplicate discovered plugin name: {manifest.name}")
        names.add(manifest.name)
        errors = compatibility_errors(manifest, self._framework_version, self._capabilities)
        if errors:
            return DiscoveredPlugin(
                source,
                DiscoveryStatus.INCOMPATIBLE,
                manifest=manifest,
                plugin=plugin,
                message="; ".join(errors),
            )
        return DiscoveredPlugin(source, DiscoveryStatus.DISCOVERED, manifest=manifest, plugin=plugin)

    @staticmethod
    def _broken(source: str, error: Exception) -> DiscoveredPlugin:
        return DiscoveredPlugin(
            source,
            DiscoveryStatus.BROKEN,
            message=f"{type(error).__name__}: {error}",
        )


def render_discovery_report(report: PluginDiscoveryReport) -> str:
    lines = ["PROJECT SARATHI Plugin Discovery", "================================"]
    if not report.results:
        lines.append("No plugin packages were discovered.")
    for item in report.results:
        name = item.manifest.name if item.manifest else item.source
        lines.append(f"[{item.status.value.upper()}] {name}")
        lines.append(f"  Source: {item.source}")
        if item.message:
            lines.append(f"  {item.message}")
    lines.extend(
        (
            "",
            f"Summary: {report.discovered} discovered | {report.incompatible} incompatible | {report.broken} broken",
            "Overall: PASS" if report.passed else "Overall: ATTENTION",
        )
    )
    return "\n".join(lines)
