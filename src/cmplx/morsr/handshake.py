"""
Handshake + HandshakeLog — the per-pulse audit trail.

Every candidate the engine evaluates emits a `Handshake`. The log
aggregates them with reason counts and per-op breakdowns. This is the
"Reader" half of the Shaper-Reader duality: pulses shape candidates,
handshakes read what happened.

Receipt JSON shape matches `morsr_handshake_v1` from
`CQE_MORSR_NewBest_v1/cqe_plus/morsr.py:71-76`.
"""
from __future__ import annotations

import hashlib
import json
import time
import uuid
from collections import Counter
from dataclasses import asdict, dataclass, field
from typing import Optional

from cmplx.nsl import NSLSectors


@dataclass(frozen=True)
class Handshake:
    """One pulse attempt's audit record.

    Fields mirror the canonical `morsr_handshake_v1` shape with the
    NSL sector breakdown attached.
    """
    handshake_id: str = ""
    overlay_id: str = ""
    op: str = ""
    phi_before: float = 0.0
    phi_after: float = 0.0
    delta: float = 0.0
    sectors: NSLSectors = field(default_factory=NSLSectors)
    accepted: bool = False
    reason: str = ""
    stage: int = 0
    ring: int = 1
    timestamp: float = 0.0

    def __post_init__(self) -> None:
        if not self.handshake_id:
            object.__setattr__(self, "handshake_id", uuid.uuid4().hex[:12])
        if not self.timestamp:
            object.__setattr__(self, "timestamp", time.time())
        # Force delta to match phi_after - phi_before if not set
        if self.delta == 0.0 and (self.phi_before or self.phi_after):
            object.__setattr__(self, "delta", self.phi_after - self.phi_before)

    @property
    def signature(self) -> str:
        return hashlib.sha256(
            json.dumps(self.to_dict(), sort_keys=True, default=str).encode()
        ).hexdigest()[:24]

    def to_dict(self) -> dict:
        return {
            "version": "morsr_handshake_v1",
            "handshake_id": self.handshake_id,
            "overlay_id": self.overlay_id,
            "op": self.op,
            "phi_before": self.phi_before,
            "phi_after": self.phi_after,
            "delta": self.delta,
            "sectors": self.sectors.to_dict(),
            "accepted": self.accepted,
            "reason": self.reason,
            "stage": self.stage,
            "ring": self.ring,
            "timestamp": self.timestamp,
        }


class HandshakeLog:
    """Append-only handshake aggregator."""

    name: str = "handshake_log"

    def __init__(self) -> None:
        self._entries: list[Handshake] = []
        self._reasons: Counter[str] = Counter()
        self._ops: Counter[str] = Counter()
        self._accepts: int = 0
        self._rejects: int = 0

    def append(self, hs: Handshake) -> Handshake:
        self._entries.append(hs)
        self._reasons[hs.reason] += 1
        self._ops[hs.op] += 1
        if hs.accepted:
            self._accepts += 1
        else:
            self._rejects += 1
        return hs

    def __len__(self) -> int:
        return len(self._entries)

    def entries(self, limit: Optional[int] = None) -> list[Handshake]:
        return list(self._entries if limit is None else self._entries[-limit:])

    def by_op(self, op: str) -> list[Handshake]:
        return [h for h in self._entries if h.op == op]

    def by_reason(self, reason: str) -> list[Handshake]:
        return [h for h in self._entries if h.reason == reason]

    def by_stage(self, stage: int) -> list[Handshake]:
        return [h for h in self._entries if h.stage == stage]

    def accepted(self) -> list[Handshake]:
        return [h for h in self._entries if h.accepted]

    def rejected(self) -> list[Handshake]:
        return [h for h in self._entries if not h.accepted]

    # ── Reporting ─────────────────────────────────────────────────────

    def reason_counts(self) -> dict[str, int]:
        return dict(self._reasons)

    def op_counts(self) -> dict[str, int]:
        return dict(self._ops)

    def stats(self) -> dict:
        total = self._accepts + self._rejects
        return {
            "total": total,
            "accepts": self._accepts,
            "rejects": self._rejects,
            "accept_rate": (self._accepts / total) if total else 0.0,
            "reasons": self.reason_counts(),
            "ops": self.op_counts(),
        }

    def to_jsonl(self) -> str:
        """Serialize as one JSON object per line (handshakes.jsonl format)."""
        return "\n".join(json.dumps(h.to_dict(), default=str) for h in self._entries)

    def clear(self) -> None:
        self._entries.clear()
        self._reasons.clear()
        self._ops.clear()
        self._accepts = 0
        self._rejects = 0

    def __repr__(self) -> str:
        return (
            f"<HandshakeLog entries={len(self._entries)} "
            f"accepts={self._accepts} rejects={self._rejects}>"
        )
