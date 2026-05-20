"""Receipt Service — Merkle-chained operation receipts.

Port of TMN2 receipt.py core logic. Every operation across every service
produces a receipt. Receipts chain via prev_hash.

Receipt types: MINT, POST, BOND, PROCESS, ASSIGN, VOTE, BIRTH, DEATH, GATE, CROSSING.
Integrates with GeometricGovernance for boundary event recording.
"""
from __future__ import annotations
import hashlib
import json
import time
import uuid
from typing import Any, Dict, List

import logging
logger = logging.getLogger("services.receipt")

RECEIPT_TYPES = ["MINT", "POST", "BOND", "PROCESS", "ASSIGN", "VOTE", "BIRTH", "DEATH", "GATE", "CROSSING"]


class ReceiptRequest:
    def __init__(self, receipt_type: str = "PROCESS", agent_id: str = "",
                 atom_id: str = "", operation: str = "", operator: str = "",
                 payload: dict | None = None, delta_phi: float = 0.0,
                 snap_labels: list[str] | None = None, epoch: int = 0,
                 parent_hash: str = ""):
        self.receipt_type = receipt_type
        self.agent_id = agent_id
        self.atom_id = atom_id
        self.operation = operation
        self.operator = operator
        self.payload = payload or {}
        self.delta_phi = delta_phi
        self.snap_labels = snap_labels or []
        self.epoch = epoch
        self.parent_hash = parent_hash


class DagEdgeRequest:
    def __init__(self, source_id: str, target_id: str,
                 edge_type: str = "depends", weight: float = 1.0,
                 snap_overlap: list[str] | None = None):
        self.source_id = source_id
        self.target_id = target_id
        self.edge_type = edge_type
        self.weight = weight
        self.snap_overlap = snap_overlap or []


class ReceiptService:
    """Merkle-chained receipt engine — every operation produces a chained receipt."""

    def __init__(self, governance=None):
        self._governance = governance
        self._chain: list[dict] = []
        self._chain_head: str = "0" * 64
        self._index_by_id: Dict[str, dict] = {}
        self._index_by_hash: Dict[str, dict] = {}
        self._index_by_agent: Dict[str, list[str]] = {}
        self._index_by_type: Dict[str, list[str]] = {}
        self._index_by_atom: Dict[str, list[str]] = {}
        self._dag_edges: list[dict] = []
        self._pg = None
        self._init_pg()

    def _init_pg(self):
        try:
            from ._pg import get_pg, ensure_table
            self._pg = get_pg()
            if self._pg:
                ensure_table(self._pg, "receipts", """
                    receipt_id TEXT PRIMARY KEY,
                    receipt_hash TEXT, receipt_type TEXT,
                    agent_id TEXT, atom_id TEXT, operation TEXT,
                    operator TEXT, delta_phi DOUBLE PRECISION,
                    snap_labels TEXT, epoch INT,
                    prev_hash TEXT, chain_index INT,
                    created_at DOUBLE PRECISION,
                    source_tag TEXT
                """)
        except Exception:
            self._pg = None

    def _persist_receipt(self, receipt: dict):
        if not self._pg:
            return
        try:
            from ._pg import upsert
            upsert(self._pg, "receipts", {
                "receipt_id": receipt.get("receipt_id", ""),
                "receipt_hash": receipt.get("receipt_hash", ""),
                "receipt_type": receipt.get("receipt_type", ""),
                "agent_id": receipt.get("agent_id", ""),
                "atom_id": receipt.get("atom_id", ""),
                "operation": receipt.get("operation", ""),
                "operator": receipt.get("operator", ""),
                "delta_phi": receipt.get("delta_phi", 0.0),
                "snap_labels": str(receipt.get("snap_labels", [])),
                "epoch": receipt.get("epoch", 0),
                "prev_hash": receipt.get("prev_hash", ""),
                "chain_index": receipt.get("chain_index", 0),
                "created_at": receipt.get("created_at", time.time()),
                "source_tag": receipt.get("source_tag", ""),
            }, pk="receipt_id")
        except Exception:
            pass

    def mint(self, req: ReceiptRequest) -> dict:
        receipt_id = str(uuid.uuid4())[:16]
        ts = time.time()
        parent = req.parent_hash if req.parent_hash else self._chain_head
        operator = req.operator or req.agent_id

        hash_input = f"{parent}:{req.operation}:{req.atom_id}:{ts}"
        receipt_hash = hashlib.sha256(hash_input.encode()).hexdigest()

        receipt = {
            "receipt_id": receipt_id, "receipt_hash": receipt_hash,
            "receipt_type": req.receipt_type, "agent_id": req.agent_id,
            "atom_id": req.atom_id, "operation": req.operation,
            "operator": operator, "delta_phi": req.delta_phi,
            "snap_labels": req.snap_labels, "epoch": req.epoch,
            "prev_hash": parent, "created_at": ts,
            "chain_index": len(self._chain),
            "source_tag": f"{req.agent_id}@epoch{req.epoch}::receipt::{receipt_id}",
        }

        self._chain.append(receipt)
        self._chain_head = receipt_hash
        self._index_by_id[receipt_id] = receipt
        self._index_by_hash[receipt_hash] = receipt
        self._index_by_agent.setdefault(req.agent_id, []).append(receipt_id)
        self._index_by_type.setdefault(req.receipt_type, []).append(receipt_id)
        if req.atom_id:
            self._index_by_atom.setdefault(req.atom_id, []).append(receipt_id)

        self._persist_receipt(receipt)

        if self._governance:
            from governance.engine import BoundaryEvent
            event = BoundaryEvent(
                event_id=receipt_id, timestamp=ts, entropy_delta=req.delta_phi,
                receipt_data={
                    "receipt_hash": receipt_hash, "prev_hash": parent,
                    "operation": req.operation, "agent_id": req.agent_id,
                    "atom_id": req.atom_id, "type": req.receipt_type,
                },
                boundary_type=f"receipt:{req.receipt_type}",
            )
            self._governance.record_boundary_event(event)

        return receipt

    def verify(self, receipt_hash: str = "", max_depth: int = 100) -> dict:
        if not receipt_hash:
            prev = "0" * 64
            breaks = []
            for i, r in enumerate(self._chain):
                if r["prev_hash"] != prev:
                    breaks.append({"index": i, "expected": prev[:16], "got": r["prev_hash"][:16]})
                prev = r["receipt_hash"]
            return {"valid": len(breaks) == 0, "length": len(self._chain),
                    "head": self._chain_head, "breaks": breaks[:10]}

        chain = self._walk_chain(receipt_hash, max_depth)
        reaches_genesis = chain and chain[-1].get("prev_hash", "") == "0" * 64
        return {
            "receipt_hash": receipt_hash, "chain_depth": len(chain),
            "reaches_genesis": reaches_genesis,
            "chain": [{"hash": r["receipt_hash"][:16], "op": r.get("operation"),
                       "atom": r.get("atom_id")} for r in chain],
        }

    def _walk_chain(self, start_hash: str, max_depth: int = 100) -> list[dict]:
        chain = []
        current = start_hash
        seen = set()
        for _ in range(max_depth):
            if current in seen or current == "0" * 64:
                break
            seen.add(current)
            receipt = self._index_by_hash.get(current)
            if not receipt:
                break
            chain.append(receipt)
            current = receipt.get("prev_hash", "")
        return chain

    def get_atom_chain(self, atom_id: str) -> dict:
        receipt_ids = self._index_by_atom.get(atom_id, [])
        receipts = [self._index_by_id[rid] for rid in receipt_ids if rid in self._index_by_id]
        return {"atom_id": atom_id, "receipts": receipts, "total": len(receipts)}

    def get_receipt(self, receipt_id: str) -> dict | None:
        return self._index_by_id.get(receipt_id)

    def get_agent_receipts(self, agent_id: str, limit: int = 20) -> list[dict]:
        ids = self._index_by_agent.get(agent_id, [])
        return [self._index_by_id[rid] for rid in ids[-limit:]]

    def add_dag_edge(self, req: DagEdgeRequest) -> dict:
        edge = {
            "source": req.source_id, "target": req.target_id,
            "edge_type": req.edge_type, "weight": req.weight,
            "snap_overlap": req.snap_overlap, "created_at": time.time(),
        }
        self._dag_edges.append(edge)
        return {"stored": True, **edge}

    def get_dag_edges(self, atom_id: str) -> dict:
        outgoing = [e for e in self._dag_edges if e["source"] == atom_id]
        incoming = [e for e in self._dag_edges if e["target"] == atom_id]
        return {"atom_id": atom_id, "outgoing": outgoing, "incoming": incoming}

    def recent(self, limit: int = 20, offset: int = 0) -> dict:
        start = max(0, len(self._chain) - limit - offset)
        end = max(0, len(self._chain) - offset)
        return {"receipts": self._chain[start:end], "total": len(self._chain),
                "limit": limit, "offset": offset}

    @property
    def stats(self) -> dict:
        depth_histogram = {}
        for atom_id, rids in self._index_by_atom.items():
            depth = len(rids)
            bucket = str(depth) if depth <= 10 else "10+"
            depth_histogram[bucket] = depth_histogram.get(bucket, 0) + 1

        op_counts: Dict[str, int] = {}
        for r in self._chain:
            op = r.get("operation", "unknown")
            op_counts[op] = op_counts.get(op, 0) + 1

        return {
            "total": len(self._chain), "head": self._chain_head[:16],
            "by_type": {t: len(self._index_by_type.get(t, [])) for t in RECEIPT_TYPES},
            "by_operation": op_counts,
            "atoms_with_receipts": len(self._index_by_atom),
            "agents_with_receipts": len(self._index_by_agent),
            "chain_depth_histogram": depth_histogram,
        }

    @property
    def status(self) -> dict:
        return {
            "chain_length": len(self._chain), "head": self._chain_head,
            "agents": len(self._index_by_agent),
            "atoms_tracked": len(self._index_by_atom),
            "types": {t: len(self._index_by_type.get(t, [])) for t in RECEIPT_TYPES},
        }
