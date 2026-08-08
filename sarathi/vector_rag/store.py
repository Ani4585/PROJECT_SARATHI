"""Asynchronous multi-tenant VectorStore."""
from typing import List, Dict, Any, Optional
from sarathi.vector_rag.document import VectorDocument, SearchResult
from sarathi.vector_rag.metrics import DistanceMetric
from sarathi.vector_rag.index import FlatVectorIndex

class VectorStore:
    def __init__(self, dimension: int = 1536, metric: DistanceMetric = DistanceMetric.COSINE):
        self.dimension = dimension
        self.metric = metric
        self.namespaces: Dict[str, FlatVectorIndex] = {}

    def get_namespace(self, name: str = "default") -> FlatVectorIndex:
        if name not in self.namespaces:
            self.namespaces[name] = FlatVectorIndex(dimension=self.dimension, metric=self.metric)
        return self.namespaces[name]

    async def upsert(self, documents: List[VectorDocument], namespace: str = "default"):
        self.get_namespace(namespace).add(documents)

    async def search(self, query_vector: List[float], top_k: int = 10, filter_spec: Optional[Dict[str, Any]] = None, tenant_id: Optional[str] = None, namespace: str = "default") -> List[SearchResult]:
        return self.get_namespace(namespace).search(query_vector=query_vector, top_k=top_k, filter_spec=filter_spec, tenant_id=tenant_id)
