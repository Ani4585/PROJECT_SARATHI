"""
Document Ingestion & RAG Pipeline Engine.
"""
import re
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field

from sarathi.vector_rag.document import VectorDocument, SearchResult
from sarathi.vector_rag.store import VectorStore
from sarathi.vector_rag.bm25 import BM25Retriever
from sarathi.vector_rag.embeddings import BaseEmbeddingDriver, MockEmbeddingDriver
from sarathi.vector_rag.chunking import BaseChunker, RecursiveTextChunker
from sarathi.vector_rag.retrieval import HybridRetriever, ScoreReranker

@dataclass
class RAGResponse:
    query: str
    expanded_queries: List[str]
    answer: str
    retrieved_chunks: List[SearchResult]
    context: str
    citations: List[Dict[str, Any]]
    execution_time_ms: float
    metadata: Dict[str, Any] = field(default_factory=dict)

class QueryTransformer:
    def __init__(self, enable_expansion: bool = True):
        self.enable_expansion = enable_expansion

    def transform(self, query: str) -> List[str]:
        queries = [query]
        if not self.enable_expansion:
            return queries

        cleaned = query.strip()
        if cleaned.endswith("?"):
            queries.append(cleaned[:-1])

        words = re.findall(r'\b\w+\b', query)
        if len(words) > 3:
            kw = " ".join([w for w in words if len(w) > 3])
            if kw and kw not in queries:
                queries.append(kw)

        return queries

class RAGContextBuilder:
    def __init__(self, max_context_length: int = 4000, citation_format: str = "[Doc {idx}]"):
        self.max_context_length = max_context_length
        self.citation_format = citation_format

    def build_context(self, search_results: List[SearchResult]) -> Tuple[str, List[Dict[str, Any]]]:
        context_parts = []
        citations = []
        current_len = 0

        for idx, res in enumerate(search_results, start=1):
            citation_tag = self.citation_format.format(idx=idx)
            text_part = res.document.text or ""
            entry = f"{citation_tag} {text_part}"

            if current_len + len(entry) > self.max_context_length:
                break

            context_parts.append(entry)
            current_len += len(entry)
            citations.append({
                "citation_id": citation_tag,
                "doc_id": res.doc_id,
                "score": res.score,
                "metadata": res.document.metadata,
                "snippet": text_part[:120]
            })

        full_context = "\n\n".join(context_parts)
        return full_context, citations

class DocumentIngestionPipeline:
    def __init__(
        self,
        vector_store: VectorStore,
        bm25_retriever: BM25Retriever,
        embedding_driver: BaseEmbeddingDriver,
        chunker: Optional[BaseChunker] = None
    ):
        self.vector_store = vector_store
        self.bm25_retriever = bm25_retriever
        self.embedding_driver = embedding_driver
        self.chunker = chunker or RecursiveTextChunker(chunk_size=300, chunk_overlap=30)

    async def ingest_document(
        self,
        doc_id: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        tenant_id: Optional[str] = None,
        namespace: str = "default"
    ) -> List[VectorDocument]:
        base_meta = metadata.copy() if metadata else {}
        base_meta["source_doc_id"] = doc_id

        chunks = self.chunker.chunk_text(text, metadata=base_meta)
        chunk_texts = [c.text for c in chunks]

        embeddings = await self.embedding_driver.embed_documents(chunk_texts)

        vector_docs = []
        for c, emb in zip(chunks, embeddings):
            c_id = f"{doc_id}_chunk_{c.chunk_index}"
            chunk_meta = c.metadata.copy()
            chunk_meta["chunk_index"] = c.chunk_index
            chunk_meta["start_char"] = c.start_char
            chunk_meta["end_char"] = c.end_char

            vdoc = VectorDocument(
                id=c_id,
                vector=emb,
                text=c.text,
                metadata=chunk_meta,
                tenant_id=tenant_id
            )
            vector_docs.append(vdoc)

        await self.vector_store.upsert(vector_docs, namespace=namespace)
        self.bm25_retriever.add_documents(vector_docs)

        return vector_docs

class RAGPipeline:
    def __init__(
        self,
        vector_store: VectorStore,
        bm25_retriever: BM25Retriever,
        embedding_driver: BaseEmbeddingDriver,
        llm_provider: Optional[Any] = None,
        fusion_mode: str = "rrf"
    ):
        self.vector_store = vector_store
        self.bm25_retriever = bm25_retriever
        self.embedding_driver = embedding_driver
        self.llm_provider = llm_provider
        self.query_transformer = QueryTransformer()
        self.context_builder = RAGContextBuilder()
        self.fusion_mode = fusion_mode

    async def query(
        self,
        question: str,
        top_k: int = 5,
        filter_spec: Optional[Dict[str, Any]] = None,
        tenant_id: Optional[str] = None,
        namespace: str = "default",
        min_score: float = 0.0
    ) -> RAGResponse:
        start_time = time.perf_counter()

        expanded_queries = self.query_transformer.transform(question)
        q_vec = await self.embedding_driver.embed_query(question)

        hybrid_retriever = HybridRetriever(
            vector_index=self.vector_store.get_namespace(namespace),
            bm25_retriever=self.bm25_retriever,
            fusion_mode=self.fusion_mode
        )

        retrieved_chunks = hybrid_retriever.search(
            query=question,
            query_vector=q_vec,
            top_k=top_k,
            filter_spec=filter_spec,
            tenant_id=tenant_id
        )

        reranker = ScoreReranker(min_score=min_score)
        retrieved_chunks = reranker.rerank(retrieved_chunks)

        context, citations = self.context_builder.build_context(retrieved_chunks)

        if self.llm_provider:
            answer = await self.llm_provider(question, context)
        else:
            answer = f"Synthesized Answer from Context:\n{context}" if context else "No context found."

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return RAGResponse(
            query=question,
            expanded_queries=expanded_queries,
            answer=answer,
            retrieved_chunks=retrieved_chunks,
            context=context,
            citations=citations,
            execution_time_ms=elapsed_ms
        )
