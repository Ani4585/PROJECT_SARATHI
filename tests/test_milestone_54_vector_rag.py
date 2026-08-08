"""Milestone 54 Tests."""
import asyncio
from sarathi.vector_rag import VectorRAGManager, DistanceMetric, compute_similarity, MetadataFilter

def test_distance_metrics(): assert abs(compute_similarity([1.0, 0.0], [1.0, 0.0], DistanceMetric.COSINE) - 1.0) < 1e-5
def test_metadata_filter(): assert MetadataFilter.matches({"cat": "ai"}, {"cat": "ai"})
def test_rag_e2e():
    async def run():
        mgr = VectorRAGManager(dimension=16)
        await mgr.ingestion_pipeline.ingest_document("d1", "Sarathi async platform", tenant_id="t1")
        res = await mgr.tool.execute("Sarathi platform", tenant_id="t1")
        assert "Sarathi" in res["context"]
    asyncio.run(run())
