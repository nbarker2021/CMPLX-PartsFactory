"""
ReceiptChain — the Merkle-chained operation store.

Adapted from `CMPLX-TMN-main/src/receipt/receipt.py`. Each minted
`Receipt` chains onto the chain head; multiple indexes give O(1)
lookup by id / hash / agent / type / atom. `verify_chain()` walks the
whole chain to confirm `prev_hash` consistency; `walk_chain(head)`
traces backward from any tip.
"""
from __future__ import annotations

import os
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional

from .types import (
    GENESIS_HASH,
    Receipt,
    ReceiptType,
    compute_receipt_hash,
    normalize_receipt_type,
)

try:
    from .ledger_manager import OperationReceipt, ReceiptLedgerManager
except ImportError:  # pragma: no cover
    OperationReceipt = Any  # type: ignore[misc, assignment]
    ReceiptLedgerManager = Any  # type: ignore[misc, assignment]


class ReceiptChain:
    """In-process Merkle-chained receipt store with multi-index lookup."""

    name: str = "receipt_chain"

    def __init__(self, storage_mode: str = "memory") -> None:
        self.storage_mode = storage_mode
        self._runs_dir = Path(
            os.environ.get("RECEIPT_RUNS_DIR", "./data/receipt-runs")
        )
        self._chain: list[Receipt] = []
        self._head: str = GENESIS_HASH
        self._by_id: dict[str, Receipt] = {}
        self._by_hash: dict[str, Receipt] = {}
        self._by_agent: dict[str, list[str]] = {}
        self._by_type: dict[str, list[str]] = {}
        self._by_atom: dict[str, list[str]] = {}
        self._operation_manager: Optional[ReceiptLedgerManager] = None

    # ── Mint ──────────────────────────────────────────────────────────

    @property
    def operation_manager(self) -> ReceiptLedgerManager:
        if self._operation_manager is None:
            self._operation_manager = ReceiptLedgerManager("receipt_chain")
        return self._operation_manager

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
        """Append a new receipt. Returns the minted Receipt."""
        receipt_type = normalize_receipt_type(receipt_type)
        parent = parent_hash or self._head
        receipt = Receipt(
            prev_hash=parent,
            receipt_type=receipt_type,
            agent_id=agent_id,
            operator=operator or agent_id,
            atom_id=atom_id,
            operation=operation,
            delta_phi=delta_phi,
            snap_labels=list(snap_labels or []),
            epoch=epoch,
            chain_index=len(self._chain),
            payload=dict(payload or {}),
        )
        self._append(receipt)
        return receipt

    def append_receipt(self, receipt: Receipt) -> Receipt:
        """Append a pre-built Receipt. The Receipt's `prev_hash`
        determines linkage; this does NOT overwrite it."""
        # If user pre-built with prev_hash == GENESIS but chain has
        # entries, force a re-chain to current head for honesty.
        if receipt.prev_hash == GENESIS_HASH and self._head != GENESIS_HASH:
            receipt = Receipt(
                receipt_id=receipt.receipt_id,
                prev_hash=self._head,
                receipt_type=receipt.receipt_type,
                agent_id=receipt.agent_id,
                operator=receipt.operator,
                atom_id=receipt.atom_id,
                operation=receipt.operation,
                delta_phi=receipt.delta_phi,
                snap_labels=list(receipt.snap_labels),
                epoch=receipt.epoch,
                chain_index=len(self._chain),
                payload=dict(receipt.payload),
                created_at=receipt.created_at,
            )
        self._append(receipt)
        return receipt

    def _append(self, receipt: Receipt) -> None:
        if receipt.receipt_id in self._by_id:
            raise RuntimeError(
                f"receipt {receipt.receipt_id!r} already in chain"
            )
        # Sequence + head bookkeeping
        receipt.chain_index = len(self._chain)
        self._chain.append(receipt)
        self._head = receipt.receipt_hash
        # Indexes
        self._by_id[receipt.receipt_id] = receipt
        self._by_hash[receipt.receipt_hash] = receipt
        if receipt.agent_id:
            self._by_agent.setdefault(receipt.agent_id, []).append(receipt.receipt_id)
        self._by_type.setdefault(receipt.receipt_type, []).append(receipt.receipt_id)
        if receipt.atom_id:
            self._by_atom.setdefault(receipt.atom_id, []).append(receipt.receipt_id)

    # ── Properties ────────────────────────────────────────────────────

    @property
    def head(self) -> str:
        return self._head

    @property
    def length(self) -> int:
        return len(self._chain)

    def __len__(self) -> int:
        return len(self._chain)

    def __contains__(self, receipt_id: str) -> bool:
        return receipt_id in self._by_id

    # ── Multi-index lookup ───────────────────────────────────────────

    def by_id(self, receipt_id: str) -> Optional[Receipt]:
        return self._by_id.get(receipt_id)

    def by_hash(self, receipt_hash: str) -> Optional[Receipt]:
        return self._by_hash.get(receipt_hash)

    def by_agent(self, agent_id: str, limit: Optional[int] = None) -> list[Receipt]:
        ids = self._by_agent.get(agent_id, [])
        if limit is not None:
            ids = ids[-limit:]
        return [self._by_id[rid] for rid in ids]

    def by_type(self, receipt_type: str) -> list[Receipt]:
        return [self._by_id[rid] for rid in self._by_type.get(receipt_type, [])]

    def by_atom(self, atom_id: str) -> list[Receipt]:
        return [self._by_id[rid] for rid in self._by_atom.get(atom_id, [])]

    def chain_for_atom(self, atom_id: str) -> list[Receipt]:
        """All receipts touching `atom_id`, in chronological order."""
        return sorted(self.by_atom(atom_id), key=lambda r: r.chain_index)

    # ── Walking + verification ───────────────────────────────────────

    def walk_chain(
        self,
        start_hash: Optional[str] = None,
        max_depth: int = 100,
    ) -> list[Receipt]:
        """Walk receipts backward from `start_hash` (defaults to head)
        until reaching GENESIS or `max_depth` is hit. Returns the
        receipts in the order encountered (newest first)."""
        start = start_hash if start_hash is not None else self._head
        if start == GENESIS_HASH:
            return []
        chain: list[Receipt] = []
        seen: set[str] = set()
        current = start
        for _ in range(max_depth):
            if current in seen or current == GENESIS_HASH:
                break
            seen.add(current)
            receipt = self._by_hash.get(current)
            if receipt is None:
                break
            chain.append(receipt)
            current = receipt.prev_hash
        return chain

    def verify(
        self,
        receipt_hash: str = "",
        max_depth: int = 100,
    ) -> dict:
        """Verify that walking back from `receipt_hash` reaches genesis.

        If `receipt_hash` is empty, verifies the full in-memory chain
        (checks every `prev_hash` against the previous receipt's hash
        and re-derives the hash from inputs).
        """
        if not receipt_hash:
            # Full-chain verification
            prev = GENESIS_HASH
            breaks: list[dict] = []
            for i, r in enumerate(self._chain):
                if r.prev_hash != prev:
                    breaks.append({
                        "index": i,
                        "expected_prev": prev[:16],
                        "got_prev": r.prev_hash[:16],
                    })
                # Re-derive hash and compare
                expected_hash = compute_receipt_hash(
                    r.prev_hash, r.operation, r.atom_id, r.created_at,
                )
                if expected_hash != r.receipt_hash:
                    breaks.append({
                        "index": i,
                        "hash_mismatch": True,
                        "expected": expected_hash[:16],
                        "got": r.receipt_hash[:16],
                    })
                prev = r.receipt_hash
            return {
                "valid": len(breaks) == 0,
                "length": len(self._chain),
                "head": self._head,
                "breaks": breaks[:10],
            }

        # Walk from a specific hash
        chain = self.walk_chain(receipt_hash, max_depth)
        reaches_genesis = bool(chain) and chain[-1].prev_hash == GENESIS_HASH
        return {
            "receipt_hash": receipt_hash,
            "chain_depth": len(chain),
            "reaches_genesis": reaches_genesis,
            "chain": [
                {"hash": r.receipt_hash[:16],
                 "op": r.operation, "atom": r.atom_id}
                for r in chain
            ],
        }

    def verify_chain(self) -> dict:
        """Alias for `verify()` with no hash argument."""
        return self.verify()

    # ── Listing ──────────────────────────────────────────────────────

    def recent(self, limit: int = 20, offset: int = 0) -> list[Receipt]:
        start = max(0, len(self._chain) - limit - offset)
        end = max(0, len(self._chain) - offset)
        return list(self._chain[start:end])

    def all(self) -> list[Receipt]:
        return list(self._chain)

    # ── Stats ────────────────────────────────────────────────────────

    def stats(self) -> dict:
        # Chain-depth histogram per atom
        depth_histogram: Counter[str] = Counter()
        for atom_id, rids in self._by_atom.items():
            depth = len(rids)
            bucket = str(depth) if depth <= 10 else "10+"
            depth_histogram[bucket] += 1
        return {
            "length": len(self._chain),
            "head": self._head,
            "agents": len(self._by_agent),
            "atoms_tracked": len(self._by_atom),
            "by_type": {t: len(self._by_type.get(t, [])) for t in self._by_type},
            "by_agent": {a: len(rids) for a, rids in self._by_agent.items()},
            "depth_histogram": dict(depth_histogram),
        }

    def clear(self) -> None:
        self._chain.clear()
        self._head = GENESIS_HASH
        self._by_id.clear()
        self._by_hash.clear()
        self._by_agent.clear()
        self._by_type.clear()
        self._by_atom.clear()

    # ── Run JSONL ledger (SpeedLight) ─────────────────────────────────

    def write_run_receipt(self, workspace: Path, **kwargs: Any) -> Dict[str, Any]:
        from ._persistence import jsonl_run_ledger

        return jsonl_run_ledger.write_receipt(workspace, **kwargs)

    def verify_run_ledger(self, workspace: Path, run_id: str, **kwargs: Any) -> Dict[str, Any]:
        from ._persistence.jsonl_run_ledger import verify_ledger

        return verify_ledger(workspace, run_id, **kwargs)

    # ── CQE operation profile ─────────────────────────────────────────

    def mint_operation(
        self,
        claim: str,
        pre_state: Dict[str, Any],
        post_state: Dict[str, Any],
        *,
        agent_id: str = "",
        atom_id: str = "",
        energies: Optional[Dict[str, float]] = None,
        validators: Optional[Dict[str, bool]] = None,
        also_mint_spine: bool = True,
    ) -> OperationReceipt:
        """Create CQE-style OperationReceipt; optionally mirror on Merkle spine."""
        op = self.operation_manager.create_receipt(
            claim=claim,
            pre_state=pre_state,
            post_state=post_state,
            energies=energies,
            validators=validators,
        )
        if also_mint_spine:
            self.mint(
                ReceiptType.PROCESS.value,
                agent_id=agent_id,
                atom_id=atom_id or claim,
                operation=f"operation:{claim}",
                payload={
                    "operation_receipt": {
                        "sequence": op.sequence,
                        "merkle_root": op.merkle_root,
                        "parity64": op.parity64,
                    },
                    "pre_state": pre_state,
                    "post_state": post_state,
                    "energies": op.energies,
                },
            )
        return op

    def __repr__(self) -> str:
        return (
            f"<ReceiptChain length={len(self._chain)} "
            f"head={self._head[:8]}...>"
        )
