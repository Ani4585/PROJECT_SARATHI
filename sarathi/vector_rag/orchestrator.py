"""Vector RAG Manager."""
from sarathi.vector_rag.store import VectorStore
from sarathi.vector_rag.bm25 import BM25Retriever
from sarathi.vector_rag.embeddings import MockEmbeddingDriver
from sarathi.vector_rag.pipeline import DocumentIngestionPipeline, RAGPipeline
from sarathi.vector_rag.agent_tool import RAGTool

class VectorRAGManager:
    def __init__(self, dimension: int = 1536):
        self.dimension = dimension
        self.embedding_driver = MockEmbeddingDriver(dimension=dimension)
        self.vector_store = VectorStore(dimension=dimension)
        self.bm25_retriever = BM25Retriever()
        self.ingestion_pipeline = DocumentIngestionPipeline(self.vector_store, self.bm25_retriever, self.embedding_driver)
        self.rag_pipeline = RAGPipeline(self.vector_store, self.bm25_retriever, self.embedding_driver)
        self.tool = RAGTool(self.rag_pipeline)
    def get_status(self): return {"status": "active", "dimension": self.dimension}
