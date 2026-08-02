"""
PROJECT SARATHI

Framework Import Diagnostic

Verifies that required framework packages can be imported
without coupling diagnostics to repository tooling.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from importlib import import_module
from types import ModuleType

from ..check import DiagnosticCheck
from ..result import DiagnosticResult
from ..status import DiagnosticStatus


DEFAULT_FRAMEWORK_MODULES = (
    "src.adr",
    "src.application",
    "src.caching",
    "src.configuration",
    "src.container",
    "src.core",
    "src.domain",
    "src.extensions",
    "src.graph",
    "src.health",
    "src.hooks",
    "src.http",
    "src.jobs",
    "src.kernel",
    "src.lifecycle",
    "src.metrics",
    "src.modules",
    "src.observability",
    "src.persistence",
    "src.performance",
    "src.plugins",
    "src.reflection",
    "src.runtime_diagnostics",
    "src.resources",
    "src.routing",
    "src.serialization",
    "src.secrets",
)


class ModuleImportCheck(DiagnosticCheck):
    """Validate imports for required framework modules."""

    def __init__(
        self,
        modules: Iterable[str] = DEFAULT_FRAMEWORK_MODULES,
        *,
        importer: Callable[[str], object] = import_module,
    ) -> None:
        """Initialize the module import diagnostic."""

        normalized_modules: list[str] = []
        observed_modules: set[str] = set()

        for module_name in modules:
            if not isinstance(module_name, str):
                raise TypeError(
                    "Framework module names must be strings."
                )

            normalized_name = module_name.strip()

            if not normalized_name:
                raise ValueError(
                    "Framework module names must not be empty."
                )

            if normalized_name in observed_modules:
                raise ValueError(
                    "Duplicate framework module: "
                    f"{normalized_name!r}."
                )

            observed_modules.add(normalized_name)
            normalized_modules.append(normalized_name)

        if not normalized_modules:
            raise ValueError(
                "At least one framework module is required."
            )

        if not callable(importer):
            raise TypeError(
                "Framework module importer must be callable."
            )

        self._modules = tuple(normalized_modules)
        self._importer = importer

    @property
    def name(self) -> str:
        """Return the stable diagnostic name."""

        return "framework-imports"

    @property
    def description(self) -> str:
        """Return the diagnostic description."""

        return "Import required framework modules."

    @property
    def modules(self) -> tuple[str, ...]:
        """Return modules in deterministic validation order."""

        return self._modules

    def run(self) -> DiagnosticResult:
        """Attempt every required framework import."""

        failures: list[str] = []

        for module_name in self.modules:
            try:
                self._importer(module_name)
            except Exception as error:
                error_name = type(error).__name__
                error_message = str(error).strip()

                failure = (
                    f"{module_name}: {error_name}"
                )

                if error_message:
                    failure = (
                        f"{failure}: {error_message}"
                    )

                failures.append(failure)

        if failures:
            return DiagnosticResult(
                name=self.name,
                status=DiagnosticStatus.FAIL,
                summary=(
                    "One or more required framework modules "
                    "could not be imported."
                ),
                details=tuple(failures),
            )

        return DiagnosticResult(
            name=self.name,
            status=DiagnosticStatus.PASS,
            summary=(
                "All required framework modules imported "
                "successfully."
            ),
            details=(
                f"Modules checked: {len(self.modules)}",
            ),
        )
