"""
Agentic RAG Copilot Master Orchestrator.
"""
from typing import Dict, Any, Optional
from sarathi.copilot.graph import KnowledgeGraph
from sarathi.copilot.streaming import StreamingResponseGenerator

class AgenticRAGCopilot:
    def __init__(self):
        self.knowledge_graph = KnowledgeGraph()
        self.streamer = StreamingResponseGenerator()

    async def query_copilot(self, prompt: str, start_entity: Optional[str] = None) -> Dict[str, Any]:
        graph_context = []
        if start_entity and start_entity in self.knowledge_graph.nodes:
            graph_context = self.knowledge_graph.multi_hop_search(start_entity, max_hops=2)

        synthesis = f"Copilot Response for '{prompt}'. Graph Entities Linked: {len(graph_context)}"
        return {
            "prompt": prompt,
            "synthesis": synthesis,
            "graph_context": graph_context
        }
