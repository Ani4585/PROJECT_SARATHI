"""
Knowledge Graph Memory & Graph-Augmented Retrieval (GraphRAG).
"""
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field

@dataclass
class GraphNode:
    node_id: str
    entity_type: str
    properties: Dict[str, Any] = field(default_factory=dict)

@dataclass
class GraphEdge:
    source_id: str
    target_id: str
    relation: str
    weight: float = 1.0
    properties: Dict[str, Any] = field(default_factory=dict)

class KnowledgeGraph:
    def __init__(self):
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: List[GraphEdge] = []
        self.adj: Dict[str, List[GraphEdge]] = {}

    def add_node(self, node_id: str, entity_type: str, properties: Optional[Dict[str, Any]] = None):
        self.nodes[node_id] = GraphNode(node_id=node_id, entity_type=entity_type, properties=properties or {})
        if node_id not in self.adj:
            self.adj[node_id] = []

    def add_edge(self, source_id: str, target_id: str, relation: str, weight: float = 1.0):
        if source_id not in self.nodes or target_id not in self.nodes:
            raise ValueError("Source and target nodes must exist in KnowledgeGraph.")
        edge = GraphEdge(source_id=source_id, target_id=target_id, relation=relation, weight=weight)
        self.edges.append(edge)
        self.adj[source_id].append(edge)

    def multi_hop_search(self, start_node_id: str, max_hops: int = 2) -> List[Dict[str, Any]]:
        if start_node_id not in self.nodes:
            return []

        visited: Set[str] = {start_node_id}
        subgraph: List[Dict[str, Any]] = []
        queue = [(start_node_id, 0)]

        while queue:
            curr_id, depth = queue.pop(0)
            if depth >= max_hops:
                continue

            for edge in self.adj.get(curr_id, []):
                target = edge.target_id
                subgraph.append({
                    "source": curr_id,
                    "target": target,
                    "relation": edge.relation,
                    "weight": edge.weight,
                    "target_type": self.nodes[target].entity_type
                })
                if target not in visited:
                    visited.add(target)
                    queue.append((target, depth + 1))

        return subgraph
