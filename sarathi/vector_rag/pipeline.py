"""Document Ingestion & RAG Pipeline."""
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from sarathi.vector_rag.document import VectorDocument, SearchResult
from sarathi.vector_rag.store import VectorStore
from sarathi.vector_rag.bm25 import BM25Retriever
from sarathi.vector_rag.embeddings import MockEmbeddingDriver
from sarathi.vector_rag.chunking import RecursiveTextChunker
from sarathi.vector_rag.retrieval import HybridRetriever

@dataclass
class RAGResponse:
    query: str
    expanded_queries: List[str]
    answer: str
    retrieved_chunks: List[SearchResult]
    context: str
    citations: List[Dict[str, Any]]
    execution_time_ms: float

class DocumentIngestionPipeline:
    def __init__(self, vector_store: VectorStore, bm25_retriever: BM25Retriever, embedding_driver: MockEmbeddingDriver):
        self.vector_store, self.bm25_retriever, self.embedding_driver = vector_store, bm25_retriever, embedding_driver
        self.chunker = RecursiveTextChunker(chunk_size=300, chunk_overlap=30)

    async def ingest_document(self, doc_id: str, text: str, metadata: Optional[Dict[str, Any]] = None, tenant_id: Optional[str] = None, namespace: str = "default"):
        chunks = self.chunker.chunk_text(text, metadata=metadata)
        embeddings = await self.embedding_driver.embed_documents([c.text for c in chunks])
        vector_docs = [VectorDocument(id=f"{doc_id}_chunk_{c.chunk_index}", vector=emb, text=c.text, metadata=c.metadata, tenant_id=tenant_id) for c, emb in zip(chunks, embeddings)]
        await self.vector_store.upsert(vector_docs, namespace=namespace)
        self.bm25_retriever.add_documents(vector_docs)
        return vector_docs

class RAGPipeline:
    def __init__(self, vector_store: VectorStore, bm25_retriever: BM25Retriever, embedding_driver: MockEmbeddingDriver):
        self.vector_store, self.bm25_retriever, self.embedding_driver = vector_store, bm25_retriever, embedding_driver

    async def query(self, question: str, top_k: int = 5, filter_spec: Optional[Dict[str, Any]] = None, tenant_id: Optional[str] = None, namespace: str = "default") -> RAGResponse:
        st = time.perf_counter()
        q_vec = await self.embedding_driver.embed_query(question)
        retriever = HybridRetriever(self.vector_store.get_namespace(namespace), self.bm25_retriever)
        results = retriever.search(query=question, query_vector=q_vec, top_k=top_k, filter_spec=filter_spec, tenant_id=tenant_id)
        parts, citations = [], []
        for idx, res in enumerate(results, start=1):
            tag = f"[Doc {idx}]"
            text = res.document.text or ""
            parts.append(f"{tag} {text}")
            citations.append({"citation_id": tag, "doc_id": res.doc_id, "score": res.score, "snippet": text[:100]})
        context = "\n\n".join(parts)
        return RAGResponse(query=question, expanded_queries=[question], answer=f"Context:\n{context}", retrieved_chunks=results, context=context, citations=citations, execution_time_ms=(time.perf_counter() - st) * 1000.0)
