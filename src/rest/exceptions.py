"""PROJECT SARATHI REST Framework RFC 7807 Problem Details."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ProblemDetails:
    """RFC 7807 compliant problem details model."""

    title: str
    status: int
    detail: str | None = None
    type: str = "about:blank"
    instance: str | None = None
    errors: dict[str, list[str]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "type": self.type,
            "title": self.title,
            "status": self.status,
        }
        if self.detail is not None:
            data["detail"] = self.detail
        if self.instance is not None:
            data["instance"] = self.instance
        if self.errors:
            data["errors"] = self.errors
        return data


class RestValidationError(Exception):
    """Raised when parameter or body validation fails."""

    def __init__(self, problem: ProblemDetails) -> None:
        super().__init__(problem.detail or problem.title)
        self.problem = problem
