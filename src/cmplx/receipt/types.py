"""
ReceiptType + Receipt + DagEdge dataclasses.

Adapted from `CMPLX-TMN-main/src/receipt/receipt.py`. The 10 canonical
receipt types cover the operations that have shown up in the corpus;
custom string types are accepted via the dataclass field.
"""
from __future__ import annotations

import hashlib
import time
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


GENESIS_HASH: str = "0" * 64


class ReceiptType(str, Enum):
    """Canonical receipt operation classes (10 core + 2 engine extensions)."""
    MINT = "MINT"           # New artifact created
    POST = "POST"           # Content posted
    BOND = "BOND"           # Two grains/entities bonded
    PROCESS = "PROCESS"     # General computation step
    ASSIGN = "ASSIGN"       # Capability / role assignment
    VOTE = "VOTE"           # Governance decision
    BIRTH = "BIRTH"         # Entity instantiated
    DEATH = "DEATH"         # Entity terminated
    GATE = "GATE"           # NSL gate decision
    CROSSING = "CROSSING"   # Boundary traversal
    # CMPLX-1T engine types that are semantically distinct from PROCESS/POST
    TOOL_EXECUTION = "TOOL_EXECUTION"
    CHECKPOINT = "CHECKPOINT"


CANONICAL_TYPES: tuple[str, ...] = tuple(t.value for t in ReceiptType)

# CMPLX-1T SpeedLight / agent.core dotted types → canonical enum value
LEGACY_TYPE_ALIASES: dict[str, str] = {
    "morphon.created": ReceiptType.MINT.value,
    "state.transition": ReceiptType.PROCESS.value,
    "policy.check": ReceiptType.GATE.value,
    "tool.execution": ReceiptType.TOOL_EXECUTION.value,
    "data.access": ReceiptType.PROCESS.value,
    "agent.dispatch": ReceiptType.ASSIGN.value,
    "tier.promotion": ReceiptType.ASSIGN.value,
    "checkpoint": ReceiptType.CHECKPOINT.value,
    "error": ReceiptType.DEATH.value,
    "metrics": ReceiptType.POST.value,
}

DAG_EDGE_TYPES: tuple[str, ...] = (
    "depends",
    "caused_by",
    "depends_on",
    "parent_of",
    "child_of",
    "bond",
    "snap_overlap",
)


def is_canonical_type(t: str) -> bool:
    return t in CANONICAL_TYPES


def normalize_receipt_type(
    receipt_type: str,
    *,
    strict: bool | None = None,
) -> str:
    """Map legacy/dotted types to canonical enum values.

    When ``strict`` is None, reads ``RECEIPT_STRICT_TYPES`` env (0 = permissive).
    Non-aliased custom types pass through in permissive mode.
    """
    import os

    if strict is None:
        strict = os.environ.get("RECEIPT_STRICT_TYPES", "0").strip() in (
            "1",
            "true",
            "yes",
        )
    key = receipt_type.strip()
    if key in CANONICAL_TYPES:
        return key
    mapped = LEGACY_TYPE_ALIASES.get(key)
    if mapped:
        return mapped
    if strict:
        raise ValueError(f"Unknown receipt type: {receipt_type!r}")
    return key


def compute_receipt_hash(
    prev_hash: str,
    operation: str,
    atom_id: str,
    timestamp: float,
) -> str:
    """`SHA256(prev_hash:operation:atom_id:timestamp)`.

    Same formula as `CMPLX-TMN-main/src/receipt/receipt.py:91`. Stable
    across processes (deterministic input ordering).
    """
    payload = f"{prev_hash}:{operation}:{atom_id}:{timestamp}"
    return hashlib.sha256(payload.encode()).hexdigest()


@dataclass
class Receipt:
    """One Merkle-chained operation receipt.

    `receipt_hash` is derived (`compute_receipt_hash`); never set by
    the caller. `prev_hash` is the chain link.
    """
    receipt_id: str = ""
    receipt_hash: str = ""
    prev_hash: str = GENESIS_HASH
    receipt_type: str = ReceiptType.PROCESS.value
    agent_id: str = ""
    operator: str = ""
    atom_id: str = ""
    operation: str = ""
    delta_phi: float = 0.0
    snap_labels: list[str] = field(default_factory=list)
    epoch: int = 0
    chain_index: int = 0
    source_tag: str = ""
    payload: dict = field(default_factory=dict)
    created_at: float = 0.0

    def __post_init__(self) -> None:
        if not self.receipt_id:
            self.receipt_id = uuid.uuid4().hex[:16]
        if not self.created_at:
            self.created_at = time.time()
        if not self.operator:
            self.operator = self.agent_id
        if not self.source_tag:
            self.source_tag = (
                f"{self.agent_id}@epoch{self.epoch}::receipt::{self.receipt_id}"
            )
        if not self.receipt_hash:
            self.receipt_hash = compute_receipt_hash(
                self.prev_hash,
                self.operation,
                self.atom_id,
                self.created_at,
            )

    def verify_hash(self) -> bool:
        """Re-derive `receipt_hash` from inputs; True iff it matches."""
        expected = compute_receipt_hash(
            self.prev_hash, self.operation, self.atom_id, self.created_at
        )
        return expected == self.receipt_hash

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Receipt":
        return cls(
            receipt_id=d.get("receipt_id", ""),
            receipt_hash=d.get("receipt_hash", ""),
            prev_hash=d.get("prev_hash", GENESIS_HASH),
            receipt_type=d.get("receipt_type", ReceiptType.PROCESS.value),
            agent_id=d.get("agent_id", ""),
            operator=d.get("operator", ""),
            atom_id=d.get("atom_id", ""),
            operation=d.get("operation", ""),
            delta_phi=float(d.get("delta_phi", 0.0)),
            snap_labels=list(d.get("snap_labels", [])),
            epoch=int(d.get("epoch", 0)),
            chain_index=int(d.get("chain_index", 0)),
            source_tag=d.get("source_tag", ""),
            payload=dict(d.get("payload", {})),
            created_at=float(d.get("created_at", 0.0)),
        )

    def __repr__(self) -> str:
        return (
            f"<Receipt {self.receipt_id} type={self.receipt_type} "
            f"atom={self.atom_id!r} hash={self.receipt_hash[:8]}...>"
        )


# ---------------------------------------------------------------------------
# DagEdge — receipts linked into a dependency DAG
# ---------------------------------------------------------------------------

@dataclass
class DagEdge:
    """An edge in the receipt DAG.

    Edges link `source_id → target_id` with an `edge_type` and a
    numeric `weight`. `snap_overlap` is the optional set of SNAP
    labels both endpoints carry (useful for label-similarity weighting).
    """
    source_id: str
    target_id: str
    edge_type: str = "depends"
    weight: float = 1.0
    snap_overlap: list[str] = field(default_factory=list)
    created_at: float = 0.0

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = time.time()

    @property
    def key(self) -> tuple[str, str, str]:
        return (self.source_id, self.target_id, self.edge_type)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "DagEdge":
        return cls(
            source_id=d["source_id"],
            target_id=d["target_id"],
            edge_type=d.get("edge_type", "depends"),
            weight=float(d.get("weight", 1.0)),
            snap_overlap=list(d.get("snap_overlap", [])),
            created_at=float(d.get("created_at", 0.0)),
        )
