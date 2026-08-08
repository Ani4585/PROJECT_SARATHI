"""Hybrid retriever (RRF and weighted fusion)."""
from collections import defaultdict
from typing import List, Dict, Any, Optional
from sarathi.vector_rag.document import VectorDocument, SearchResult
from sarathi.vector_rag.index import FlatVectorIndex
from sarathi.vector_rag.bm25 import BM25Retriever

class HybridRetriever:
    def __init__(self, vector_index: FlatVectorIndex, bm25_retriever: BM25Retriever, fusion_mode: str = "rrf", rrf_k: int = 60, alpha: float = 0.5):
        self.vector_index = vector_index
        self.bm25_retriever = bm25_retriever
        self.fusion_mode = fusion_mode
        self.rrf_k = rrf_k
        self.alpha = alpha

    def search(self, query: str, query_vector: List[float], top_k: int = 10, filter_spec: Optional[Dict[str, Any]] = None, tenant_id: Optional[str] = None) -> List[SearchResult]:
        dense_res = self.vector_index.search(query_vector=query_vector, top_k=top_k * 2, filter_spec=filter_spec, tenant_id=tenant_id)
        sparse_res = self.bm25_retriever.search(query=query, top_k=top_k * 2, filter_spec=filter_spec, tenant_id=tenant_id)
        rrf_scores = defaultdict(float)
        docs_by_id = {}
        for r, res in enumerate(dense_res, start=1):
            rrf_scores[res.doc_id] += 1.0 / (self.rrf_k + r)
            docs_by_id[res.doc_id] = res.document
        for r, res in enumerate(sparse_res, start=1):
            rrf_scores[res.doc_id] += 1.0 / (self.rrf_k + r)
            docs_by_id[res.doc_id] = res.document
        sorted_items = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        return [SearchResult(doc_id=did, score=score, document=docs_by_id[did], retrieval_type="hybrid_rrf") for did, score in sorted_items[:top_k]]

class ScoreReranker:
    def __init__(self, min_score: float = 0.0, top_k: Optional[int] = None):
        self.min_score = min_score
        self.top_k = top_k

    def rerank(self, results: List[SearchResult]) -> List[SearchResult]:
        filtered = [r for r in results if r.score >= self.min_score]
        filtered.sort(key=lambda x: x.score, reverse=True)
        if self.top_k is not None:
            return filtered[:self.top_k]
        return filtered
