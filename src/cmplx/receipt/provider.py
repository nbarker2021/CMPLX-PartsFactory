"""
ReceiptProvider — the `receipt` port provider.

Bundles `ReceiptChain` + `DagEdgeStore`. Register on the `receipt`
port:

    MorphonController.get().register("receipt", ReceiptProvider())
"""
from __future__ import annotations

from typing import Optional

from .chain import ReceiptChain
from .dag import DagEdgeStore
from .types import DagEdge, Receipt, ReceiptType


class ReceiptProvider:
    """Composite receipt provider: chain + DAG."""

    name: str = "receipt_provider"

    def __init__(
        self,
        chain: Optional[ReceiptChain] = None,
        dag: Optional[DagEdgeStore] = None,
    ) -> None:
        self.chain = chain or ReceiptChain()
        self.dag = dag or DagEdgeStore()

    # ── Mint helpers (typed) ─────────────────────────────────────────

    def mint(
        self,
        receipt_type: str = ReceiptType.PROCESS.value,
        agent_id: str = "",
        atom_id: str = "",
        operation: str = "",
        operator: str = "",
        delta_phi: float = 0.0,
        snap_labels: Optional[list[str]] = None,
        epoch: int = 0,
        payload: Optional[dict] = None,
        parent_hash: str = "",
    ) -> Receipt:
        return self.chain.mint(
            receipt_type=receipt_type,
            agent_id=agent_id,
            atom_id=atom_id,
            operation=operation,
            operator=operator,
            delta_phi=delta_phi,
            snap_labels=snap_labels,
            epoch=epoch,
            payload=payload,
            parent_hash=parent_hash,
        )

    def mint_mint(self, atom_id: str, agent_id: str = "",
                  operation: str = "create", **kw) -> Receipt:
        return self.mint(ReceiptType.MINT.value, agent_id=agent_id,
                         atom_id=atom_id, operation=operation, **kw)

    def mint_bond(self, source_atom: str, target_atom: str,
                  agent_id: str = "", **kw) -> Receipt:
        return self.mint(
            ReceiptType.BOND.value,
            agent_id=agent_id,
            atom_id=source_atom,
            operation=f"bond:{source_atom}->{target_atom}",
            payload={"target_atom": target_atom, **kw.pop("payload", {})},
            **kw,
        )

    def mint_gate(self, atom_id: str, accepted: bool, delta_phi: float = 0.0,
                  agent_id: str = "", **kw) -> Receipt:
        return self.mint(
            ReceiptType.GATE.value,
            agent_id=agent_id, atom_id=atom_id,
            operation="gate:accept" if accepted else "gate:reject",
            delta_phi=delta_phi,
            payload={"accepted": accepted, **kw.pop("payload", {})},
            **kw,
        )

    def mint_crossing(self, atom_id: str, boundary: str,
                      agent_id: str = "", **kw) -> Receipt:
        return self.mint(
            ReceiptType.CROSSING.value,
            agent_id=agent_id, atom_id=atom_id,
            operation=f"crossing:{boundary}",
            payload={"boundary": boundary, **kw.pop("payload", {})},
            **kw,
        )

    # ── Lookup pass-throughs ─────────────────────────────────────────

    def by_id(self, receipt_id: str) -> Optional[Receipt]:
        return self.chain.by_id(receipt_id)

    def by_hash(self, receipt_hash: str) -> Optional[Receipt]:
        return self.chain.by_hash(receipt_hash)

    def by_atom(self, atom_id: str) -> list[Receipt]:
        return self.chain.by_atom(atom_id)

    def by_agent(self, agent_id: str, limit: Optional[int] = None) -> list[Receipt]:
        return self.chain.by_agent(agent_id, limit)

    def by_type(self, receipt_type: str) -> list[Receipt]:
        return self.chain.by_type(receipt_type)

    def chain_for_atom(self, atom_id: str) -> list[Receipt]:
        return self.chain.chain_for_atom(atom_id)

    def recent(self, limit: int = 20, offset: int = 0) -> list[Receipt]:
        return self.chain.recent(limit, offset)

    @property
    def head(self) -> str:
        return self.chain.head

    @property
    def length(self) -> int:
        return self.chain.length

    # ── Chain verification ───────────────────────────────────────────

    def verify(self, receipt_hash: str = "", max_depth: int = 100) -> dict:
        return self.chain.verify(receipt_hash, max_depth)

    def verify_chain(self) -> dict:
        return self.chain.verify_chain()

    def walk_chain(self, start_hash: Optional[str] = None,
                   max_depth: int = 100) -> list[Receipt]:
        return self.chain.walk_chain(start_hash, max_depth)

    # ── DAG helpers ──────────────────────────────────────────────────

    def add_edge(
        self,
        source_id: str,
        target_id: str,
        edge_type: str = "depends",
        weight: float = 1.0,
        snap_overlap: Optional[list[str]] = None,
    ) -> DagEdge:
        edge = DagEdge(
            source_id=source_id, target_id=target_id,
            edge_type=edge_type, weight=weight,
            snap_overlap=list(snap_overlap or []),
        )
        return self.dag.add(edge)

    def edges_of(self, atom_id: str) -> dict:
        return self.dag.edges_of(atom_id)

    # ── Reporting ────────────────────────────────────────────────────

    @property
    def health(self) -> dict:
        return {
            "ok": True,
            "service": "receipt_provider",
            "chain": self.chain.stats(),
            "dag": self.dag.stats(),
        }

    def stats(self) -> dict:
        return self.health

    def __repr__(self) -> str:
        return (
            f"<ReceiptProvider receipts={self.chain.length} "
            f"edges={len(self.dag)}>"
        )
