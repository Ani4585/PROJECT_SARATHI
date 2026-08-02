"""Public persistence contracts, runtime, and reference adapters."""

from .configuration import PersistenceSettings
from .contracts import PersistenceConnection, PersistenceSession, SessionFactory
from .database import (
    DatabaseState,
    InMemoryConnection,
    InMemoryDatabase,
    InMemorySession,
    InMemorySessionRepository,
    SessionState,
)
from .exceptions import (
    ActiveSessionError,
    EntityAlreadyExistsError,
    EntityNotFoundError,
    PersistenceConfigurationError,
    PersistenceConnectionError,
    PersistenceError,
    PersistenceSessionError,
    TransactionConflictError,
)
from .health import PersistenceHealthCheck
from .integration import persistence_resource, register_persistence
from .memory import InMemoryRepository
from .repository import EntityT, IdentifierT, Repository
from .runtime import PersistenceRuntime, create_persistence_runtime
from .unit_of_work import (
    InMemoryUnitOfWork,
    SessionUnitOfWork,
    UnitOfWork,
    UnitOfWorkState,
)

__all__ = [
    "ActiveSessionError",
    "DatabaseState",
    "EntityAlreadyExistsError",
    "EntityNotFoundError",
    "EntityT",
    "IdentifierT",
    "InMemoryConnection",
    "InMemoryDatabase",
    "InMemoryRepository",
    "InMemorySession",
    "InMemorySessionRepository",
    "InMemoryUnitOfWork",
    "PersistenceConfigurationError",
    "PersistenceConnection",
    "PersistenceConnectionError",
    "PersistenceError",
    "PersistenceHealthCheck",
    "PersistenceRuntime",
    "PersistenceSession",
    "PersistenceSessionError",
    "Repository",
    "SessionFactory",
    "SessionState",
    "SessionUnitOfWork",
    "TransactionConflictError",
    "UnitOfWork",
    "UnitOfWorkState",
    "create_persistence_runtime",
    "persistence_resource",
    "register_persistence",
]
