"""Application command and query message contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True, kw_only=True)
class Message:
    """Immutable base metadata for application messages."""

    message_id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if self.created_at.tzinfo is None:
            raise ValueError("Application message timestamps must be timezone-aware.")


class Command(Message):
    """Marker base for state-changing requests."""


class Query(Message):
    """Marker base for read-only requests."""
