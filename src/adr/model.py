"""Architecture decision record model and lifecycle statuses."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date
from enum import StrEnum


class AdrStatus(StrEnum):
    PROPOSED = "Proposed"
    ACCEPTED = "Accepted"
    REJECTED = "Rejected"
    DEPRECATED = "Deprecated"
    SUPERSEDED = "Superseded"


@dataclass(frozen=True, slots=True)
class ArchitectureDecision:
    number: int
    title: str
    status: AdrStatus
    decided_on: date
    context: str
    decision: str
    consequences: str
    links: tuple[str, ...] = ()
    supersedes: int | None = None
    superseded_by: int | None = None

    def __post_init__(self) -> None:
        if self.number < 1:
            raise ValueError("ADR number must be positive.")
        for name in ("title", "context", "decision", "consequences"):
            value = getattr(self, name).strip()
            if not value:
                raise ValueError(f"ADR {name} must not be blank.")
            object.__setattr__(self, name, value)
        object.__setattr__(self, "links", tuple(link.strip() for link in self.links if link.strip()))

    @property
    def identifier(self) -> str:
        return f"ADR-{self.number:04d}"

    @property
    def filename(self) -> str:
        slug = "-".join(part for part in self.title.lower().replace("_", "-").split() if part)
        return f"{self.number:04d}-{slug}.md"

    def with_status(self, status: AdrStatus, *, superseded_by: int | None = None) -> "ArchitectureDecision":
        return replace(self, status=status, superseded_by=superseded_by)
