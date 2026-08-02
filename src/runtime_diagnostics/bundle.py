"""Safe-share runtime diagnostic bundle collection and persistence."""

from __future__ import annotations

import json
import os
import platform
import re
import sys
from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass, is_dataclass
from enum import StrEnum
from pathlib import Path


REDACTED = "********"
_SENSITIVE_KEY = re.compile(r"password|secret|token|api[_-]?key|credential|authorization", re.IGNORECASE)


class DiagnosticSectionStatus(StrEnum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class DiagnosticSection:
    name: str
    status: DiagnosticSectionStatus
    data: Mapping[str, object]
    error: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {"name": self.name, "status": self.status.value, "data": dict(self.data), "error": self.error}


@dataclass(frozen=True, slots=True)
class DiagnosticBundle:
    sections: tuple[DiagnosticSection, ...]
    safe_to_share: bool = True

    @property
    def failures(self) -> int:
        return sum(section.status is DiagnosticSectionStatus.FAILED for section in self.sections)

    @property
    def partial(self) -> int:
        return sum(section.status is DiagnosticSectionStatus.PARTIAL for section in self.sections)

    def to_dict(self) -> dict[str, object]:
        return {
            "title": "PROJECT SARATHI Runtime Diagnostic Bundle",
            "safe_to_share": self.safe_to_share,
            "summary": {"sections": len(self.sections), "partial": self.partial, "failures": self.failures},
            "sections": [section.to_dict() for section in self.sections],
        }


class SafeShareRedactor:
    """Recursively redact secret-like keys and local home-directory paths."""

    def __init__(self, home: Path | None = None) -> None:
        self._home = str((home or Path.home()).resolve())

    def redact(self, value: object, key: str = "") -> object:
        if _SENSITIVE_KEY.search(key):
            return REDACTED
        if getattr(value, "__sarathi_secret__", False) is True:
            return REDACTED
        if isinstance(value, Mapping):
            return {str(item_key): self.redact(item_value, str(item_key)) for item_key, item_value in value.items()}
        if isinstance(value, (list, tuple, set, frozenset)):
            return [self.redact(item) for item in value]
        if isinstance(value, Path):
            value = str(value)
        if isinstance(value, str):
            return value.replace(self._home, "<HOME>")
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value
        return repr(value)


class RuntimeDiagnosticCollector:
    """Collect independent diagnostic sections with partial-failure isolation."""

    def __init__(self, redactor: SafeShareRedactor | None = None) -> None:
        self._redactor = redactor or SafeShareRedactor()

    def collect(self, *, configuration=None, container=None, secrets=None) -> DiagnosticBundle:
        collectors: tuple[tuple[str, Callable[[], Mapping[str, object]]], ...] = (
            ("runtime", self._runtime),
            ("environment", self._environment),
            ("services", lambda: self._services(container)),
            ("dependency_traces", lambda: self._dependencies(container)),
            ("configuration", lambda: self._configuration(configuration)),
            ("secrets", lambda: self._secrets(secrets)),
        )
        sections: list[DiagnosticSection] = []
        for name, collector in collectors:
            try:
                data = collector()
                status = DiagnosticSectionStatus.COMPLETE if data else DiagnosticSectionStatus.PARTIAL
                sections.append(DiagnosticSection(name, status, self._redactor.redact(data)))
            except Exception as error:
                sections.append(
                    DiagnosticSection(
                        name,
                        DiagnosticSectionStatus.FAILED,
                        {},
                        f"{type(error).__name__}: {error}",
                    )
                )
        return DiagnosticBundle(tuple(sections))

    @staticmethod
    def _runtime() -> Mapping[str, object]:
        return {
            "python": platform.python_version(),
            "implementation": platform.python_implementation(),
            "executable": sys.executable,
            "prefix": sys.prefix,
            "virtual_environment": sys.prefix != sys.base_prefix,
        }

    @staticmethod
    def _environment() -> Mapping[str, object]:
        allowed = ("CI", "PYTHONPATH", "VIRTUAL_ENV")
        return {
            "platform": platform.platform(),
            "machine": platform.machine(),
            "variables": {name: os.environ[name] for name in allowed if name in os.environ},
        }

    @staticmethod
    def _services(container) -> Mapping[str, object]:
        if container is None:
            return {}
        return {
            "registrations": [
                {
                    "service": descriptor.service_type.__name__,
                    "implementation": descriptor.implementation_type.__name__,
                    "lifetime": descriptor.lifetime.value,
                    "constructor_cached": descriptor.constructor_cached,
                }
                for descriptor in container.service_descriptors()
            ]
        }

    @staticmethod
    def _dependencies(container) -> Mapping[str, object]:
        if container is None:
            return {}
        return {
            "edges": [
                {"service": node.name, "dependencies": sorted(child.name for child in node.dependencies)}
                for node in sorted(container.dependency_graph, key=lambda item: item.name)
            ]
        }

    @staticmethod
    def _configuration(configuration) -> Mapping[str, object]:
        if configuration is None:
            return {}
        if hasattr(configuration, "as_dict"):
            return configuration.as_dict(redact_secrets=True)
        if isinstance(configuration, Mapping):
            return dict(configuration)
        if is_dataclass(configuration) and not isinstance(configuration, type):
            return asdict(configuration)
        return vars(configuration)

    @staticmethod
    def _secrets(secrets) -> Mapping[str, object]:
        if secrets is None:
            return {}
        snapshot = getattr(secrets, "current", secrets)
        if hasattr(snapshot, "safe_summary"):
            return snapshot.safe_summary()
        return {"available": True, "details": REDACTED}


class DiagnosticBundleWriter:
    def write_json(self, bundle: DiagnosticBundle, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(bundle.to_dict(), indent=2) + "\n", encoding="utf-8")
        return path


class DiagnosticBundleTextRenderer:
    def render(self, bundle: DiagnosticBundle) -> str:
        lines = ["PROJECT SARATHI Runtime Diagnostic Bundle", "=" * 41]
        for section in bundle.sections:
            lines.append(f"[{section.status.value.upper()}] {section.name}")
            if section.error:
                lines.append(f"  {section.error}")
            else:
                lines.append(f"  Fields: {len(section.data)}")
        lines.extend(
            ("", f"Summary: {len(bundle.sections)} sections | {bundle.partial} partial | {bundle.failures} failed", "Safe to share: YES")
        )
        return "\n".join(lines)


class DiagnosticBundleJsonRenderer:
    def render(self, bundle: DiagnosticBundle) -> str:
        return json.dumps(bundle.to_dict(), indent=2)
