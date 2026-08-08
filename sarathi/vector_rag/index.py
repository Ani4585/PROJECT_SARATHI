"""Vector index implementations."""
from typing import List, Dict, Any, Optional
import numpy as np
from sarathi.vector_rag.document import VectorDocument, SearchResult
from sarathi.vector_rag.metrics import DistanceMetric, compute_similarity
from sarathi.vector_rag.filter import MetadataFilter

class FlatVectorIndex:
    def __init__(self, dimension: int, metric: DistanceMetric = DistanceMetric.COSINE):
        self.dimension = dimension
        self.metric = metric
        self.documents: Dict[str, VectorDocument] = {}

    def add(self, docs: List[VectorDocument]):
        for doc in docs:
            if len(doc.vector) != self.dimension:
                raise ValueError(f"Dimension mismatch: expected {self.dimension}, got {len(doc.vector)}")
            self.documents[doc.id] = doc

    def delete(self, doc_ids: List[str]):
        for did in doc_ids: self.documents.pop(did, None)

    def count(self) -> int: return len(self.documents)

    def search(self, query_vector: List[float], top_k: int = 10, filter_spec: Optional[Dict[str, Any]] = None, tenant_id: Optional[str] = None) -> List[SearchResult]:
        if not self.documents: return []
        q_arr = np.asarray(query_vector, dtype=np.float32)
        results = []
        for did, doc in self.documents.items():
            if tenant_id is not None and doc.tenant_id != tenant_id: continue
            if filter_spec and not MetadataFilter.matches(filter_spec, doc.metadata): continue
            score = compute_similarity(q_arr, np.asarray(doc.vector, dtype=np.float32), self.metric)
            results.append(SearchResult(doc_id=did, score=score, document=doc, retrieval_type="dense"))
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]
