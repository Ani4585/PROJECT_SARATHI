"""RAG Tool for AI Agents."""
class RAGTool:
    name = "rag_knowledge_search"
    description = "Searches vector database."
    def __init__(self, rag_pipeline): self.rag_pipeline = rag_pipeline
    def get_schema(self): return {"name": self.name, "description": self.description}
    async def execute(self, query: str, top_k: int = 5, tenant_id=None, **kwargs):
        resp = await self.rag_pipeline.query(question=query, top_k=top_k, tenant_id=tenant_id)
        return {"answer": resp.answer, "context": resp.context, "citations": resp.citations, "chunk_count": len(resp.retrieved_chunks)}
