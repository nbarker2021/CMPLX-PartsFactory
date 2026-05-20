"""
DagEdgeStore — the receipt DAG topology layer.

Receipts can be linked into a directed graph: `source_id → target_id`
with an `edge_type` and `weight`. The same source/target/type triple
upserts (latest weight wins). Useful for: SNAP-label-similarity
edges, BOND-graph dependencies, agent-trust relationships, etc.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Optional

from .types import DagEdge


class DagEdgeStore:
    """In-process DAG-edge store.

    Keys edges on `(source_id, target_id, edge_type)` — at most one
    edge per triple; `add()` upserts.
    """

    name: str = "dag_edge_store"

    def __init__(self) -> None:
        self._edges: dict[tuple[str, str, str], DagEdge] = {}
        # Outgoing/incoming adjacency for fast node-centric lookup
        self._outgoing: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
        self._incoming: dict[str, list[tuple[str, str, str]]] = defaultdict(list)

    def add(self, edge: DagEdge) -> DagEdge:
        """Upsert an edge. Returns the stored edge."""
        key = edge.key
        was_new = key not in self._edges
        self._edges[key] = edge
        if was_new:
            self._outgoing[edge.source_id].append(key)
            self._incoming[edge.target_id].append(key)
        return edge

    def get(
        self,
        source_id: str,
        target_id: str,
        edge_type: str = "depends",
    ) -> Optional[DagEdge]:
        return self._edges.get((source_id, target_id, edge_type))

    def has(
        self,
        source_id: str,
        target_id: str,
        edge_type: str = "depends",
    ) -> bool:
        return (source_id, target_id, edge_type) in self._edges

    def outgoing(self, atom_id: str) -> list[DagEdge]:
        return [self._edges[k] for k in self._outgoing.get(atom_id, [])]

    def incoming(self, atom_id: str) -> list[DagEdge]:
        return [self._edges[k] for k in self._incoming.get(atom_id, [])]

    def edges_of(self, atom_id: str) -> dict:
        """Both directions for `atom_id`."""
        return {
            "atom_id": atom_id,
            "outgoing": [e.to_dict() for e in self.outgoing(atom_id)],
            "incoming": [e.to_dict() for e in self.incoming(atom_id)],
        }

    def all(self) -> list[DagEdge]:
        return list(self._edges.values())

    def by_type(self, edge_type: str) -> list[DagEdge]:
        return [e for e in self._edges.values() if e.edge_type == edge_type]

    def __len__(self) -> int:
        return len(self._edges)

    def stats(self) -> dict:
        from collections import Counter
        type_counts: Counter[str] = Counter()
        for e in self._edges.values():
            type_counts[e.edge_type] += 1
        return {
            "total_edges": len(self._edges),
            "nodes_with_outgoing": len(self._outgoing),
            "nodes_with_incoming": len(self._incoming),
            "by_type": dict(type_counts),
        }

    def clear(self) -> None:
        self._edges.clear()
        self._outgoing.clear()
        self._incoming.clear()

    def __repr__(self) -> str:
        return f"<DagEdgeStore edges={len(self._edges)}>"
