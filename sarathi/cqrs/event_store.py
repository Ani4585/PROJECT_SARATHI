from typing import Dict, List
from .models import DomainEvent

class EventStore:
    def __init__(self):
        self._store: Dict[str, List[DomainEvent]] = {}

    def append_events(self, aggregate_id: str, events: List[DomainEvent]):
        if aggregate_id not in self._store:
            self._store[aggregate_id] = []
        self._store[aggregate_id].extend(events)

    def get_events(self, aggregate_id: str) -> List[DomainEvent]:
        return list(self._store.get(aggregate_id, []))
