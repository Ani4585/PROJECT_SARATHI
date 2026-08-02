"""Hook events, decisions, outcomes, and instrumentation models."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType


class HookDecision(StrEnum):
    CONTINUE = "continue"
    CANCEL = "cancel"


class HookStatus(StrEnum):
    SUCCEEDED = "succeeded"
    SKIPPED = "skipped"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True, slots=True)
class HookEvent:
    name: str
    payload: Mapping[str, object]

    def __post_init__(self) -> None:
        name = self.name.strip()
        if not name:
            raise ValueError("Hook event name must not be blank.")
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "payload", MappingProxyType(dict(self.payload)))


@dataclass(frozen=True, slots=True)
class HookOutcome:
    owner: str
    status: HookStatus
    duration_seconds: float
    message: str | None = None


@dataclass(frozen=True, slots=True)
class HookReport:
    event: HookEvent
    outcomes: tuple[HookOutcome, ...]
    cancelled: bool = False

    @property
    def failures(self) -> int:
        return sum(item.status is HookStatus.FAILED for item in self.outcomes)

    @property
    def passed(self) -> bool:
        return self.failures == 0


@dataclass(frozen=True, slots=True)
class HookExecutionEvent:
    hook: str
    owner: str
    status: HookStatus
    duration_seconds: float
