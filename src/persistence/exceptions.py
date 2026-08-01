"""Persistence abstraction exceptions."""

from __future__ import annotations

from src.exceptions.base import SarathiException


class PersistenceError(SarathiException):
    """Base persistence port failure."""


class EntityAlreadyExistsError(PersistenceError):
    def __init__(self, identifier: object) -> None:
        super().__init__(
            f"Entity {identifier!r} already exists.",
            error_code="ENTITY_ALREADY_EXISTS",
            details={"identifier": identifier},
        )


class EntityNotFoundError(PersistenceError):
    def __init__(self, identifier: object) -> None:
        super().__init__(
            f"Entity {identifier!r} was not found.",
            error_code="ENTITY_NOT_FOUND",
            details={"identifier": identifier},
        )
