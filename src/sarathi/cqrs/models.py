import time
from dataclasses import dataclass, field
from typing import Dict, List, Any

@dataclass
class DomainEvent:
    aggregate_id: str
    event_type: str
    data: Dict[str, Any]
    version: int = 1
    timestamp: float = field(default_factory=time.time)

class AggregateRoot:
    def __init__(self, aggregate_id: str):
        self.aggregate_id = aggregate_id
        self.version = 0
        self._uncommitted_events: List[DomainEvent] = []

    def raise_event(self, event_type: str, data: Dict[str, Any]):
        self.version += 1
        event = DomainEvent(
            aggregate_id=self.aggregate_id,
            event_type=event_type,
            data=data,
            version=self.version
        )
        self.apply(event)
        self._uncommitted_events.append(event)

    def apply(self, event: DomainEvent):
        """Override in subclasses to update internal aggregate state."""
        pass

    def commit_events(self) -> List[DomainEvent]:
        events = list(self._uncommitted_events)
        self._uncommitted_events.clear()
        return events
