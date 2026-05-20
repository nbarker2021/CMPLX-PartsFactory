"""
NSLLedger + NSLReceipt — the cumulative conservation audit trail.

Every state change reports an `NSLReceipt` with `delta_phi` and the
sector breakdown. The ledger appends each receipt, updates cumulative
ΔΦ, and flags violations.

Adapted from `CMPLX-TMN-main/src/conservation/conservation.py` — the
in-process variant (no PG). The receipt JSON shape matches
`SNAPNslReceipts2025Q4.json`.
"""
from __future__ import annotations

import hashlib
import json
import time
import uuid
from collections import Counter
from dataclasses import asdict, dataclass, field
from typing import Optional

from .sectors import NSLSectors


@dataclass(frozen=True)
class NSLReceipt:
    """One conservation-ledger entry.

    Required: `sectors`. Other fields name the source of the operation
    so the ledger can produce per-agent / per-service breakdowns.
    """
    receipt_id: str = ""
    sectors: NSLSectors = field(default_factory=NSLSectors)
    delta_phi: float = 0.0
    agent_id: str = ""
    service: str = ""
    atom_id: str = ""
    operation: str = ""
    epoch: int = 0
    timestamp: float = 0.0

    def __post_init__(self) -> None:
        if not self.receipt_id:
            object.__setattr__(self, "receipt_id", uuid.uuid4().hex[:12])
        if not self.timestamp:
            object.__setattr__(self, "timestamp", time.time())
        # Force delta_phi to mirror sectors.total if not set
        if self.delta_phi == 0.0 and self.sectors.total != 0.0:
            object.__setattr__(self, "delta_phi", self.sectors.total)

    def to_dict(self) -> dict:
        """Matches the canonical SNAPNslReceipts2025Q4 JSON shape."""
        return {
            "kind": "snapdna",
            "receipt_id": self.receipt_id,
            "delta_phi": self.delta_phi,
            "sectors": self.sectors.to_dict(),
            "agent_id": self.agent_id,
            "service": self.service,
            "atom_id": self.atom_id,
            "operation": self.operation,
            "epoch": self.epoch,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "NSLReceipt":
        sectors = NSLSectors.from_dict(d.get("sectors", {}))
        return cls(
            receipt_id=d.get("receipt_id", ""),
            sectors=sectors,
            delta_phi=float(d.get("delta_phi", sectors.total)),
            agent_id=d.get("agent_id", ""),
            service=d.get("service", ""),
            atom_id=d.get("atom_id", ""),
            operation=d.get("operation", ""),
            epoch=int(d.get("epoch", 0)),
            timestamp=float(d.get("timestamp", 0.0)),
        )

    @property
    def hash(self) -> str:
        return hashlib.sha256(
            json.dumps(self.to_dict(), sort_keys=True).encode()
        ).hexdigest()[:32]


class NSLLedger:
    """Append-only cumulative conservation ledger.

    `append(receipt)` updates cumulative ΔΦ, flags violations, and
    returns a status dict. `audit()` walks the chain and recomputes
    cumulative to detect drift.
    """

    name: str = "nsl_ledger"

    def __init__(self) -> None:
        self._entries: list[NSLReceipt] = []
        self._cumulative: float = 0.0
        self._violations: int = 0
        self._by_agent: dict[str, float] = {}
        self._by_service: dict[str, float] = {}
        self._by_operation: dict[str, float] = {}
        self._violations_by_agent: Counter[str] = Counter()
        self._total_checks: int = 0

    def append(self, receipt: NSLReceipt) -> dict:
        self._total_checks += 1
        self._cumulative += receipt.delta_phi
        self._by_agent[receipt.agent_id] = (
            self._by_agent.get(receipt.agent_id, 0.0) + receipt.delta_phi
        )
        self._by_service[receipt.service] = (
            self._by_service.get(receipt.service, 0.0) + receipt.delta_phi
        )
        self._by_operation[receipt.operation] = (
            self._by_operation.get(receipt.operation, 0.0) + receipt.delta_phi
        )

        is_violation = receipt.delta_phi > 0
        if is_violation:
            self._violations += 1
            self._violations_by_agent[receipt.agent_id] += 1

        self._entries.append(receipt)
        return {
            "receipt_id": receipt.receipt_id,
            "delta_phi": receipt.delta_phi,
            "cumulative": self._cumulative,
            "violation": is_violation,
        }

    # ── Properties ────────────────────────────────────────────────────

    @property
    def cumulative(self) -> float:
        return self._cumulative

    @property
    def violations(self) -> int:
        return self._violations

    @property
    def is_valid(self) -> bool:
        """`True` iff no violations have been recorded."""
        return self._violations == 0

    @property
    def total_checks(self) -> int:
        return self._total_checks

    def __len__(self) -> int:
        return len(self._entries)

    def entries(self, limit: Optional[int] = None) -> list[NSLReceipt]:
        if limit is None:
            return list(self._entries)
        return list(self._entries[-limit:])

    # ── Per-source breakdowns ────────────────────────────────────────

    def by_agent(self, agent_id: str) -> dict:
        return {
            "agent_id": agent_id,
            "cumulative_dphi": self._by_agent.get(agent_id, 0.0),
            "violations": self._violations_by_agent.get(agent_id, 0),
        }

    def by_service(self, service: str) -> dict:
        return {
            "service": service,
            "cumulative_dphi": self._by_service.get(service, 0.0),
        }

    def by_operation(self, operation: str) -> dict:
        return {
            "operation": operation,
            "cumulative_dphi": self._by_operation.get(operation, 0.0),
        }

    # ── Audit ────────────────────────────────────────────────────────

    def audit(self) -> dict:
        """Recompute cumulative from entries; return drift + chain errors."""
        running = 0.0
        for entry in self._entries:
            running += entry.delta_phi
        drift = abs(running - self._cumulative)
        return {
            "valid": drift < 1e-8 and self._violations == 0,
            "memory_cumulative": self._cumulative,
            "recomputed_cumulative": running,
            "drift": drift,
            "total_entries": len(self._entries),
            "violations": self._violations,
        }

    def stats(self) -> dict:
        return {
            "cumulative_dphi": self._cumulative,
            "total_checks": self._total_checks,
            "violations": self._violations,
            "conservation_valid": self.is_valid,
            "by_agent": dict(self._by_agent),
            "by_service": dict(self._by_service),
            "by_operation": dict(self._by_operation),
        }

    def clear(self) -> None:
        self._entries.clear()
        self._cumulative = 0.0
        self._violations = 0
        self._by_agent.clear()
        self._by_service.clear()
        self._by_operation.clear()
        self._violations_by_agent.clear()
        self._total_checks = 0

    def __repr__(self) -> str:
        return (
            f"<NSLLedger entries={len(self._entries)} "
            f"cumulative={self._cumulative:.6f} "
            f"violations={self._violations}>"
        )
