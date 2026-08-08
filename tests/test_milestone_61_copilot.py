"""
Unit and Integration Tests for Milestone 61: Autonomous Agentic RAG Copilot, Knowledge Graph & Streaming Engine.
Tag: v2.5.0-autonomous-agentic-rag-copilot
"""
import asyncio
from sarathi.copilot import KnowledgeGraph, StreamingResponseGenerator, AgenticRAGCopilot

def test_knowledge_graph_multi_hop_search():
    kg = KnowledgeGraph()
    kg.add_node("sarathi", "Framework")
    kg.add_node("rag", "Subsystem")
    kg.add_node("vector_db", "Storage")

    kg.add_edge("sarathi", "rag", relation="CONTAINS")
    kg.add_edge("rag", "vector_db", relation="USES")

    hops = kg.multi_hop_search("sarathi", max_hops=2)
    assert len(hops) == 2
    assert hops[0]["relation"] == "CONTAINS"
    assert hops[1]["relation"] == "USES"

def test_streaming_response_generator():
    async def run():
        tokens = []
        async for chunk in StreamingResponseGenerator.stream_tokens("Hello Sarathi", chunk_size=3, delay_sec=0.0):
            tokens.append(chunk)

        assert "".join(tokens) == "Hello Sarathi"
        assert len(tokens) == 5  # "Hel", "lo ", "Sar", "ath", "i"

    asyncio.run(run())

def test_agentic_rag_copilot():
    async def run():
        copilot = AgenticRAGCopilot()
        copilot.knowledge_graph.add_node("agent_1", "Agent")
        copilot.knowledge_graph.add_node("tool_1", "Tool")
        copilot.knowledge_graph.add_edge("agent_1", "tool_1", relation="INVOKES")

        res = await copilot.query_copilot("Execute workflow", start_entity="agent_1")
        assert "synthesis" in res
        assert len(res["graph_context"]) == 1

    asyncio.run(run())
