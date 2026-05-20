"""
ComputationReceipt + ReceiptStore.

A receipt is the atomic record of a computation: who ran what, what
came out, how long it took, and where it lives in the lattice. The
ReceiptStore is the append-only ledger of receipts.
"""
from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any, Iterable, Optional


def _hash_obj(obj: Any) -> str:
    """Stable SHA256 hex digest of a JSON-serializable object."""
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()


@dataclass
class ComputationReceipt:
    """The atomic record of an idempotent computation."""
    receipt_id: str = ""
    task_id: str = ""
    task_hash: str = ""
    result_hash: str = ""
    result: Any = None
    cost_seconds: float = 0.0
    cached_at: float = 0.0
    fn_name: str = ""
    e8_coords: Optional[list[float]] = None
    leech_coords: Optional[list[float]] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.receipt_id:
            self.receipt_id = uuid.uuid4().hex[:12]
        if not self.cached_at:
            self.cached_at = time.time()
        if not self.task_hash and self.task_id:
            self.task_hash = _hash_obj({"task_id": self.task_id})
        if not self.result_hash:
            self.result_hash = _hash_obj({"r": self.result})

    def to_dict(self) -> dict:
        return asdict(self)


class ReceiptStore:
    """Append-only in-process ledger of computation receipts.

    Indexed by `task_id` and by `task_hash` for fast lookup. The
    canonical TMN2 store backs to MMDB; this in-process version is
    the dependency-free default for the unified build.
    """

    name: str = "receipt_store"

    def __init__(self) -> None:
        self._by_task: dict[str, ComputationReceipt] = {}
        self._by_hash: dict[str, str] = {}  # task_hash → task_id
        self._order: list[str] = []

    def append(self, receipt: ComputationReceipt) -> ComputationReceipt:
        if not receipt.task_id:
            raise ValueError("receipt.task_id is required")
        self._by_task[receipt.task_id] = receipt
        self._by_hash[receipt.task_hash] = receipt.task_id
        # maintain insertion order; if updating, move to end
        if receipt.task_id in self._order:
            self._order.remove(receipt.task_id)
        self._order.append(receipt.task_id)
        return receipt

    def get(self, task_id: str) -> Optional[ComputationReceipt]:
        return self._by_task.get(task_id)

    def get_by_hash(self, task_hash: str) -> Optional[ComputationReceipt]:
        tid = self._by_hash.get(task_hash)
        return self._by_task.get(tid) if tid else None

    def has(self, task_id: str) -> bool:
        return task_id in self._by_task

    def __contains__(self, task_id: str) -> bool:
        return task_id in self._by_task

    def __len__(self) -> int:
        return len(self._by_task)

    def iter_receipts(self) -> Iterable[ComputationReceipt]:
        for tid in self._order:
            yield self._by_task[tid]

    def all(self) -> list[ComputationReceipt]:
        return [self._by_task[tid] for tid in self._order]

    def clear(self) -> None:
        self._by_task.clear()
        self._by_hash.clear()
        self._order.clear()

    def stats(self) -> dict:
        return {
            "total_receipts": len(self._by_task),
            "unique_hashes": len(self._by_hash),
        }

    def __repr__(self) -> str:
        return f"<ReceiptStore receipts={len(self._by_task)}>"
