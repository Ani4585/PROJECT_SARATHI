"""Hybrid retriever (RRF)."""
from collections import defaultdict
from typing import List, Dict, Any, Optional
from sarathi.vector_rag.document import VectorDocument, SearchResult
from sarathi.vector_rag.index import FlatVectorIndex
from sarathi.vector_rag.bm25 import BM25Retriever

class HybridRetriever:
    def __init__(self, vector_index: FlatVectorIndex, bm25_retriever: BM25Retriever, rrf_k: int = 60):
        self.vector_index, self.bm25_retriever, self.rrf_k = vector_index, bm25_retriever, rrf_k

    def search(self, query: str, query_vector: List[float], top_k: int = 10, filter_spec: Optional[Dict[str, Any]] = None, tenant_id: Optional[str] = None) -> List[SearchResult]:
        dense_res = self.vector_index.search(query_vector=query_vector, top_k=top_k * 2, filter_spec=filter_spec, tenant_id=tenant_id)
        sparse_res = self.bm25_retriever.search(query=query, top_k=top_k * 2, filter_spec=filter_spec, tenant_id=tenant_id)
        rrf_scores, docs_by_id = defaultdict(float), {}
        for r, res in enumerate(dense_res, start=1):
            rrf_scores[res.doc_id] += 1.0 / (self.rrf_k + r)
            docs_by_id[res.doc_id] = res.document
        for r, res in enumerate(sparse_res, start=1):
            rrf_scores[res.doc_id] += 1.0 / (self.rrf_k + r)
            docs_by_id[res.doc_id] = res.document
        sorted_items = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        return [SearchResult(doc_id=did, score=score, document=docs_by_id[did], retrieval_type="hybrid_rrf") for did, score in sorted_items[:top_k]]
