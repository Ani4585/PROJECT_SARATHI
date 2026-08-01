"""Domain-facing repository port."""

from __future__ import annotations

from typing import Protocol, TypeVar


EntityT = TypeVar("EntityT")
IdentifierT = TypeVar("IdentifierT")


class Repository(Protocol[EntityT, IdentifierT]):
    """Minimal collection-like persistence contract."""

    def add(self, entity: EntityT) -> None:
        """Add a new entity."""

    def get(self, identifier: IdentifierT) -> EntityT | None:
        """Return an entity by identity when it exists."""

    def require(self, identifier: IdentifierT) -> EntityT:
        """Return an entity or raise a persistence-specific error."""

    def remove(self, identifier: IdentifierT) -> EntityT:
        """Remove and return an entity."""

    def list(self) -> tuple[EntityT, ...]:
        """Return all entities in insertion order."""
