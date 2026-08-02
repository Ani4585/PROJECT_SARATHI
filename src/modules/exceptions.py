"""Module runtime exceptions."""

from __future__ import annotations

from src.exceptions.base import SarathiException


class ModuleError(SarathiException):
    """Base module runtime failure."""


class ModuleAlreadyRegisteredError(ModuleError):
    def __init__(self, name: str) -> None:
        super().__init__(
            f"Module {name!r} is already registered.",
            error_code="MODULE_ALREADY_REGISTERED",
            details={"module": name},
        )


class ModuleDependencyError(ModuleError):
    def __init__(self, module: str, dependency: str) -> None:
        super().__init__(
            f"Module {module!r} requires unknown module {dependency!r}.",
            error_code="MODULE_DEPENDENCY_MISSING",
            details={"module": module, "dependency": dependency},
        )


class ModuleCycleError(ModuleError):
    def __init__(self, modules: tuple[str, ...]) -> None:
        super().__init__(
            "Module dependency cycle detected: " + ", ".join(modules),
            error_code="MODULE_DEPENDENCY_CYCLE",
            details={"modules": modules},
        )


class ModuleStartupError(ModuleError):
    def __init__(self, module: str, reason: str) -> None:
        super().__init__(
            f"Module {module!r} failed to start: {reason}",
            error_code="MODULE_STARTUP_FAILED",
            details={"module": module, "reason": reason},
        )


class ModuleReloadError(ModuleError):
    def __init__(self, module: str, reason: str) -> None:
        super().__init__(
            f"Module {module!r} cannot be reloaded: {reason}",
            error_code="MODULE_RELOAD_REJECTED",
            details={"module": module, "reason": reason},
        )
