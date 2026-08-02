"""Operational health-check contract."""

from __future__ import annotations

from abc import ABC, abstractmethod

from .model import HealthGroup, HealthResult


class HealthCheck(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def group(self) -> HealthGroup: ...

    @property
    def critical(self) -> bool:
        return True

    @property
    def dependencies(self) -> tuple[str, ...]:
        return ()

    @property
    def timeout_seconds(self) -> float:
        return 5.0

    @abstractmethod
    def run(self) -> HealthResult: ...
