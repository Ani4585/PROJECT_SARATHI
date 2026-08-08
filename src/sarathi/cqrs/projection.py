from typing import Dict, Callable, List
from .models import DomainEvent

class ProjectionManager:
    def __init__(self):
        self._projectors: Dict[str, List[Callable[[DomainEvent], None]]] = {}

    def register_projector(self, event_type: str, projector_fn: Callable[[DomainEvent], None]):
        if event_type not in self._projectors:
            self._projectors[event_type] = []
        self._projectors[event_type].append(projector_fn)

    def apply_event(self, event: DomainEvent):
        if event.event_type in self._projectors:
            for fn in self._projectors[event.event_type]:
                fn(event)
