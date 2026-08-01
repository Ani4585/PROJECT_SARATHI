"""Public persistence ports and in-memory adapters."""

from .exceptions import EntityAlreadyExistsError, EntityNotFoundError, PersistenceError
from .memory import InMemoryRepository
from .repository import EntityT, IdentifierT, Repository
from .unit_of_work import InMemoryUnitOfWork, UnitOfWork, UnitOfWorkState

__all__ = [
    "EntityAlreadyExistsError",
    "EntityNotFoundError",
    "EntityT",
    "IdentifierT",
    "InMemoryRepository",
    "InMemoryUnitOfWork",
    "PersistenceError",
    "Repository",
    "UnitOfWork",
    "UnitOfWorkState",
]
