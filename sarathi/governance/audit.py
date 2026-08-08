"""
Tamper-Evident Hash-Chained Audit Trail Logger for Compliance.
"""
import hashlib
import json
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

@dataclass
class AuditEntry:
    entry_id: str
    actor: str
    action: str
    resource_id: str
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    prev_hash: str = "GENESIS"
    curr_hash: str = ""

    def compute_hash(self) -> str:
        payload = f"{self.entry_id}:{self.actor}:{self.action}:{self.resource_id}:{self.timestamp}:{json.dumps(self.metadata, sort_keys=True)}:{self.prev_hash}"
        return hashlib.sha256(payload.encode('utf-8')).hexdigest()

class AuditLogger:
    def __init__(self):
        self.chain: List[AuditEntry] = []

    def log(self, entry_id: str, actor: str, action: str, resource_id: str, metadata: Optional[Dict[str, Any]] = None) -> AuditEntry:
        prev_hash = self.chain[-1].curr_hash if self.chain else "GENESIS"
        entry = AuditEntry(
            entry_id=entry_id,
            actor=actor,
            action=action,
            resource_id=resource_id,
            metadata=metadata or {},
            prev_hash=prev_hash
        )
        entry.curr_hash = entry.compute_hash()
        self.chain.append(entry)
        return entry

    def verify_integrity(self) -> bool:
        for i, entry in enumerate(self.chain):
            if entry.compute_hash() != entry.curr_hash:
                return False  # Entry content tampered
            if i > 0 and entry.prev_hash != self.chain[i-1].curr_hash:
                return False  # Hash chain broken
        return True
