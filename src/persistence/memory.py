"""Thread-safe in-memory persistence adapter."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from copy import deepcopy
from threading import RLock
from typing import Generic

from .exceptions import EntityAlreadyExistsError, EntityNotFoundError
from .repository import EntityT, IdentifierT


class InMemoryRepository(Generic[EntityT, IdentifierT]):
    """Deterministic repository useful for tests and local runtimes."""

    def __init__(self, identity: Callable[[EntityT], IdentifierT]) -> None:
        if not callable(identity):
            raise TypeError("Repository identity selector must be callable.")
        self._identity = identity
        self._entities: dict[IdentifierT, EntityT] = {}
        self._lock = RLock()

    def add(self, entity: EntityT) -> None:
        identifier = self._identity(entity)
        with self._lock:
            if identifier in self._entities:
                raise EntityAlreadyExistsError(identifier)
            self._entities[identifier] = entity

    def get(self, identifier: IdentifierT) -> EntityT | None:
        with self._lock:
            return self._entities.get(identifier)

    def require(self, identifier: IdentifierT) -> EntityT:
        entity = self.get(identifier)
        if entity is None:
            raise EntityNotFoundError(identifier)
        return entity

    def remove(self, identifier: IdentifierT) -> EntityT:
        with self._lock:
            try:
                return self._entities.pop(identifier)
            except KeyError as error:
                raise EntityNotFoundError(identifier) from error

    def list(self) -> tuple[EntityT, ...]:
        with self._lock:
            return tuple(self._entities.values())

    def snapshot(self) -> dict[IdentifierT, EntityT]:
        """Return a deep snapshot for transactional rollback."""

        with self._lock:
            return deepcopy(self._entities)

    def restore(self, snapshot: Mapping[IdentifierT, EntityT]) -> None:
        """Replace current contents from a detached snapshot."""

        with self._lock:
            self._entities = deepcopy(dict(snapshot))

    def __len__(self) -> int:
        with self._lock:
            return len(self._entities)
