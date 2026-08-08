"""Vector document model and search result container."""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class VectorDocument:
    id: str
    vector: List[float]
    text: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    tenant_id: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.id, "vector": list(self.vector), "text": self.text, "metadata": self.metadata, "tenant_id": self.tenant_id, "created_at": self.created_at}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VectorDocument":
        return cls(id=data["id"], vector=data["vector"], text=data.get("text"), metadata=data.get("metadata", {}), tenant_id=data.get("tenant_id"), created_at=data.get("created_at", datetime.utcnow().isoformat()))

@dataclass
class SearchResult:
    doc_id: str
    score: float
    document: VectorDocument
    retrieval_type: str = "dense"
